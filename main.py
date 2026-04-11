"""NSP Cases enquiry extraction prototype.

Loads a sample enquiry email, sends it to an LLM, enforces a stable JSON shape,
prints the result, and saves it to output/example_output.json.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT_DIR / "prompts"
SAMPLE_EMAIL_PATH = ROOT_DIR / "sample_email.txt"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"
EXTRACTION_PROMPT_PATH = PROMPTS_DIR / "extraction_prompt.txt"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "output" / "example_output.json"


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider fails."""


class LLMResponseError(RuntimeError):
    """Raised when the LLM response cannot be parsed or normalized."""


@dataclass
class ProviderConfig:
    provider: str
    model: str
    api_key: str
    timeout_seconds: int = 45


def load_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing required file: {path}") from exc


def read_provider_config() -> ProviderConfig:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise LLMProviderError(
                "OPENAI_API_KEY is missing. Add it to your .env file."
            )
        return ProviderConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

    # The architecture intentionally supports future providers.
    if provider in {"anthropic", "claude", "gemini"}:
        raise LLMProviderError(
            f"Provider '{provider}' is not implemented yet. "
            "Set LLM_PROVIDER=openai for this demo."
        )

    raise LLMProviderError(f"Unsupported provider: {provider}")


def build_messages(
    system_prompt: str, extraction_prompt_template: str, email_text: str
) -> list[dict[str, str]]:
    user_prompt = extraction_prompt_template.replace("{{email_text}}", email_text.strip())
    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]


def call_llm(messages: list[dict[str, str]], config: ProviderConfig) -> str:
    if config.provider == "openai":
        return call_openai_chat(messages, config)
    raise LLMProviderError(f"Provider not implemented: {config.provider}")


def call_openai_chat(messages: list[dict[str, str]], config: ProviderConfig) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": config.model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=config.timeout_seconds
        )
    except requests.RequestException as exc:
        raise LLMProviderError(f"Network error while calling OpenAI: {exc}") from exc

    if response.status_code >= 400:
        details = response.text
        try:
            details = response.json().get("error", {}).get("message", details)
        except ValueError:
            pass
        raise LLMProviderError(
            f"OpenAI API request failed ({response.status_code}): {details}"
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if not content:
            raise KeyError("Missing response content")
        return content
    except (ValueError, KeyError, IndexError) as exc:
        raise LLMProviderError(f"Unexpected OpenAI response format: {exc}") from exc


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return match.group(0)

    raise LLMResponseError("Could not find a JSON object in the model response.")


def as_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        cleaned: list[str] = []
        for item in value:
            item_str = as_string(item)
            if item_str:
                cleaned.append(item_str)
        return cleaned
    if isinstance(value, str):
        # Allows recovery if model returns one long semicolon-separated string.
        parts = [part.strip(" -") for part in re.split(r"[;\n]", value)]
        return [part for part in parts if part]
    return []


def as_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def normalize_result(data: dict[str, Any]) -> dict[str, Any]:
    dimensions = data.get("dimensions", {}) if isinstance(data.get("dimensions"), dict) else {}

    normalized = {
        "product_type": as_string(data.get("product_type")),
        "dimensions": {
            "length": as_string(dimensions.get("length")),
            "width": as_string(dimensions.get("width")),
            "height": as_string(dimensions.get("height")),
            "unit": as_string(dimensions.get("unit")),
        },
        "use_case": as_string(data.get("use_case")),
        "requirements": as_string_list(data.get("requirements")),
        "attachments_present": as_bool(data.get("attachments_present")),
        "summary": as_string(data.get("summary")),
        "missing_information": as_string_list(data.get("missing_information")),
        "confidence": as_confidence(data.get("confidence")),
    }

    # Guarantee required top-level keys are not null for easier downstream use.
    for key in ("product_type", "use_case", "summary"):
        if normalized[key] is None:
            normalized[key] = ""

    return normalized


def parse_model_response(raw_response: str) -> dict[str, Any]:
    json_payload = extract_json_object(raw_response)
    try:
        parsed = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(f"Model returned invalid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise LLMResponseError("Expected top-level JSON object from model response.")

    return normalize_result(parsed)


def write_output(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def resolve_output_path() -> Path:
    configured = os.getenv("OUTPUT_PATH", "").strip()
    if not configured:
        return DEFAULT_OUTPUT_PATH
    path = Path(configured)
    return path if path.is_absolute() else ROOT_DIR / path


def extract_from_email_text(
    email_text: str, output_path: Path | None = None
) -> dict[str, Any]:
    """Extract structured enquiry data from raw email text."""
    load_dotenv()
    if not email_text or not email_text.strip():
        raise ValueError("Email text is empty. Please provide enquiry content.")

    config = read_provider_config()
    system_prompt = load_text_file(SYSTEM_PROMPT_PATH)
    extraction_prompt = load_text_file(EXTRACTION_PROMPT_PATH)

    messages = build_messages(system_prompt, extraction_prompt, email_text)
    raw_response = call_llm(messages, config)
    result = parse_model_response(raw_response)

    if output_path is not None:
        write_output(result, output_path)

    return result


def run() -> dict[str, Any]:
    load_dotenv()
    email_text = load_text_file(SAMPLE_EMAIL_PATH)
    output_path = resolve_output_path()
    result = extract_from_email_text(email_text, output_path=output_path)

    print(json.dumps(result, indent=2))
    print(f"\nSaved structured output to: {output_path}")
    return result


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
