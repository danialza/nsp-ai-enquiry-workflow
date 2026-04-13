"""FastAPI app for NSP enquiry extraction with a simple frontend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from main import (
    LLMProviderError,
    LLMResponseError,
    SAMPLE_EMAIL_PATH,
    extract_from_email_text,
    load_text_file,
    resolve_output_path,
)


load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
APP_VERSION = "1.1.0"

app = FastAPI(
    title="NSP AI Enquiry Extractor",
    version=APP_VERSION,
    description=(
        "Extracts structured flight-case enquiry details from free-text customer emails."
    ),
)
app.mount("/static", StaticFiles(directory=ROOT_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))


class ExtractRequest(BaseModel):
    email_text: str = Field(..., min_length=1, description="Raw customer enquiry email text")


class DimensionsModel(BaseModel):
    length: str | None
    width: str | None
    height: str | None
    unit: str | None


class ExtractResponse(BaseModel):
    product_type: str
    dimensions: DimensionsModel
    use_case: str
    requirements: list[str]
    attachments_present: bool
    summary: str
    missing_information: list[str]
    confidence: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nsp-ai-enquiry-extractor"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"version": APP_VERSION}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the frontend page."""
    try:
        sample_email = load_text_file(SAMPLE_EMAIL_PATH)
    except FileNotFoundError:
        sample_email = ""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"sample_email": sample_email},
    )


@app.post("/api/extract", response_model=ExtractResponse)
def extract_api(payload: ExtractRequest) -> dict[str, Any]:
    email_text = payload.email_text.strip()
    if not email_text:
        raise HTTPException(status_code=400, detail="Please paste an enquiry email first.")

    try:
        return extract_from_email_text(email_text, output_path=resolve_output_path())
    except (ValueError, FileNotFoundError, LLMProviderError, LLMResponseError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {exc}") from exc


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
