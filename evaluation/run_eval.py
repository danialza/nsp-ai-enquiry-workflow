"""Starter evaluation runner for NSP enquiry extraction."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import extract_from_email_text, load_text_file

SAMPLES_DIR = ROOT_DIR / "evaluation" / "samples"
RESULTS_DIR = ROOT_DIR / "evaluation" / "results"

REQUIRED_KEYS = {
    "product_type",
    "dimensions",
    "use_case",
    "requirements",
    "attachments_present",
    "summary",
    "missing_information",
    "confidence",
}


@dataclass
class EvalCase:
    case_id: str
    email_text: str
    expected: dict[str, Any]


def load_cases() -> list[EvalCase]:
    cases: list[EvalCase] = []
    for email_path in sorted(SAMPLES_DIR.glob("*_email.txt")):
        case_id = email_path.name.replace("_email.txt", "")
        expected_path = SAMPLES_DIR / f"{case_id}_expected.json"
        if not expected_path.exists():
            raise FileNotFoundError(f"Missing expected file for case '{case_id}'.")
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        cases.append(
            EvalCase(
                case_id=case_id,
                email_text=load_text_file(email_path),
                expected=expected,
            )
        )
    if not cases:
        raise FileNotFoundError("No evaluation samples found in evaluation/samples.")
    return cases


def validate_expected_schema(payload: dict[str, Any]) -> list[str]:
    missing_keys = sorted(REQUIRED_KEYS - set(payload.keys()))
    return [f"Missing required key: {key}" for key in missing_keys]


def normalize_text_list(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


def score_case(expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, float]:
    dimensions_expected = expected.get("dimensions", {})
    dimensions_predicted = predicted.get("dimensions", {})

    matched_dims = 0
    total_dims = 4
    for key in ("length", "width", "height", "unit"):
        if str(dimensions_expected.get(key, "")).strip().lower() == str(
            dimensions_predicted.get(key, "")
        ).strip().lower():
            matched_dims += 1
    dimensions_score = matched_dims / total_dims

    expected_reqs = normalize_text_list(expected.get("requirements", []))
    predicted_reqs = normalize_text_list(predicted.get("requirements", []))
    if expected_reqs:
        req_overlap = len(expected_reqs & predicted_reqs) / len(expected_reqs)
    else:
        req_overlap = 1.0

    attachment_score = (
        1.0
        if bool(expected.get("attachments_present")) == bool(predicted.get("attachments_present"))
        else 0.0
    )
    product_type_score = (
        1.0
        if expected.get("product_type", "").strip().lower()
        in predicted.get("product_type", "").strip().lower()
        else 0.0
    )

    overall = (
        (0.35 * dimensions_score)
        + (0.3 * req_overlap)
        + (0.2 * attachment_score)
        + (0.15 * product_type_score)
    )

    return {
        "dimensions_score": round(dimensions_score, 3),
        "requirements_overlap": round(req_overlap, 3),
        "attachment_score": round(attachment_score, 3),
        "product_type_score": round(product_type_score, 3),
        "overall_score": round(overall, 3),
    }


def run_offline_schema_check(cases: list[EvalCase]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    has_failure = False
    for case in cases:
        errors = validate_expected_schema(case.expected)
        if errors:
            has_failure = True
        results.append(
            {
                "case_id": case.case_id,
                "status": "failed" if errors else "passed",
                "errors": errors,
            }
        )
    return {
        "mode": "offline_schema_check",
        "all_passed": not has_failure,
        "cases": results,
    }


def run_live_eval(cases: list[EvalCase]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in cases:
        predicted = extract_from_email_text(case.email_text, output_path=None)
        scores = score_case(case.expected, predicted)
        results.append(
            {
                "case_id": case.case_id,
                "scores": scores,
                "predicted": predicted,
            }
        )

    avg_score = sum(item["scores"]["overall_score"] for item in results) / len(results)
    return {
        "mode": "live_eval",
        "average_overall_score": round(avg_score, 3),
        "cases": results,
    }


def save_report(report: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "latest_eval.json"
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NSP extraction evaluation.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run only schema checks on expected fixtures (no API calls).",
    )
    args = parser.parse_args()

    cases = load_cases()
    report = run_offline_schema_check(cases) if args.offline else run_live_eval(cases)
    report_path = save_report(report)

    print(json.dumps(report, indent=2))
    print(f"\nSaved evaluation report to: {report_path}")


if __name__ == "__main__":
    main()
