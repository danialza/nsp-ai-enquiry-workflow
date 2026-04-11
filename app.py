"""Simple web UI for NSP enquiry extraction."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from main import (
    LLMProviderError,
    LLMResponseError,
    SAMPLE_EMAIL_PATH,
    extract_from_email_text,
    load_text_file,
    resolve_output_path,
)


load_dotenv()
app = Flask(__name__)


@app.get("/")
def index() -> str:
    """Render a simple single-page UI."""
    try:
        sample_email = load_text_file(SAMPLE_EMAIL_PATH)
    except FileNotFoundError:
        sample_email = ""
    return render_template("index.html", sample_email=sample_email)


@app.post("/api/extract")
def extract_api():
    payload = request.get_json(silent=True) or {}
    email_text = str(payload.get("email_text", "")).strip()
    if not email_text:
        return jsonify({"error": "Please paste an enquiry email first."}), 400

    try:
        result = extract_from_email_text(email_text, output_path=resolve_output_path())
        return jsonify(result)
    except (ValueError, FileNotFoundError, LLMProviderError, LLMResponseError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": f"Unexpected server error: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0").strip() == "1"
    app.run(host="127.0.0.1", port=port, debug=debug)
