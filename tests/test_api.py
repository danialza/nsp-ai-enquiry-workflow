from __future__ import annotations

from fastapi.testclient import TestClient

import app as fastapi_app


client = TestClient(fastapi_app.app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_version_endpoint() -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_extract_requires_input() -> None:
    response = client.post("/api/extract", json={"email_text": "   "})
    assert response.status_code == 400


def test_extract_success(monkeypatch) -> None:
    def fake_extract(email_text: str, output_path=None):  # noqa: ANN001
        return {
            "product_type": "Custom flight case",
            "dimensions": {
                "length": "620",
                "width": "420",
                "height": "280",
                "unit": "mm",
            },
            "use_case": "Transport between office and offshore vessel",
            "requirements": ["waterproof", "shock-resistant"],
            "attachments_present": True,
            "summary": "Concise summary",
            "missing_information": ["lead time"],
            "confidence": 0.91,
        }

    monkeypatch.setattr(fastapi_app, "extract_from_email_text", fake_extract)

    response = client.post("/api/extract", json={"email_text": "Sample enquiry"})
    assert response.status_code == 200
    body = response.json()
    assert body["product_type"] == "Custom flight case"
    assert body["dimensions"]["unit"] == "mm"
    assert body["attachments_present"] is True
