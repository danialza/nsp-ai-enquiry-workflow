# Workflow Overview

## 1) Input
The workflow starts with a customer enquiry email (plain text body, and optionally attachment references).

For this prototype:
- input file: `sample_email.txt`
- optional attachment signal: inferred from text mentions such as "attached PDF", "drawing", or "image"

## 2) AI Extraction Step
The email content is combined with:
- `prompts/system_prompt.txt` (rules and schema)
- `prompts/extraction_prompt.txt` (task-specific extraction prompt)

The LLM is called through a provider-isolated function in `main.py`, so the extraction layer can later switch from OpenAI to Claude or Gemini with minimal code changes.

The AI returns structured JSON fields:
- product type
- dimensions
- use case
- requirements
- attachment presence
- concise summary
- missing information
- confidence

## 3) Structured Output
The script:
1. Parses model output
2. Normalizes values into a stable schema
3. Prints JSON to terminal
4. Saves JSON to `output/example_output.json`

This stable JSON format makes downstream integration easier and safer.

## 4) Optional Human Review
Before creating a formal quote, a sales or operations user can review:
- extracted dimensions
- technical requirements
- missing information list
- confidence score

If confidence is low or key fields are missing, a follow-up email can be triggered automatically.

## 5) Future ERP/MRP Integration
A production version can push this structured output into an ERP/MRP process:
- create enquiry/opportunity record in CRM/ERP
- create technical review task for engineering
- trigger quote preparation workflow
- map final approved values into BOM/planning stages

This keeps AI as a practical front-end data standardization layer rather than replacing core operational systems.
