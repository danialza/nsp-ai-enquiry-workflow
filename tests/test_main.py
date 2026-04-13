from __future__ import annotations

import pytest

from main import extract_json_object, normalize_result, parse_model_response


def test_extract_json_object_from_fenced_block() -> None:
    raw = """```json
    {"product_type":"Case","dimensions":{"length":"1","width":"2","height":"3","unit":"mm"},"use_case":"Transport","requirements":["waterproof"],"attachments_present":true,"summary":"x","missing_information":[],"confidence":0.8}
    ```"""
    extracted = extract_json_object(raw)
    assert extracted.startswith("{")
    assert extracted.endswith("}")


def test_parse_model_response_normalizes_types() -> None:
    raw = """
    {
      "product_type": "Flight case",
      "dimensions": {"length": 620, "width": 420, "height": 280, "unit": "mm"},
      "use_case": "Transport",
      "requirements": "waterproof; shock-resistant",
      "attachments_present": "yes",
      "summary": "Summary",
      "missing_information": "lead time;price",
      "confidence": "0.92"
    }
    """
    parsed = parse_model_response(raw)

    assert parsed["dimensions"]["length"] == "620"
    assert parsed["requirements"] == ["waterproof", "shock-resistant"]
    assert parsed["attachments_present"] is True
    assert parsed["missing_information"] == ["lead time", "price"]
    assert parsed["confidence"] == pytest.approx(0.92)


def test_normalize_result_keeps_required_top_level_strings() -> None:
    normalized = normalize_result(
        {
            "dimensions": {},
            "requirements": [],
            "attachments_present": False,
            "missing_information": [],
            "confidence": 0,
        }
    )
    assert normalized["product_type"] == ""
    assert normalized["use_case"] == ""
    assert normalized["summary"] == ""
