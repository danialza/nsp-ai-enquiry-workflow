# NSP Cases AI Enquiry Workflow

Practical, GitHub-ready mini project for a hiring task: convert unstructured customer enquiry emails into structured, business-usable JSON for downstream quoting and operations workflows.

## Problem This Solves
NSP Cases receives custom flight case enquiries by email. Important details (dimensions, use case, requirements, attachment mentions) are often buried in free text. This prototype standardizes that data in seconds so teams can quote and route work faster.

## What The Prototype Does
- Reads a sample enquiry email from `sample_email.txt`
- Sends the email text to an LLM through an isolated provider function
- Extracts required fields into a strict JSON schema
- Prints the result in a readable format
- Saves output to `output/example_output.json`

No paid automation platform is required for the core demo. It runs locally with Python.

## Output Schema
```json
{
  "product_type": "string",
  "dimensions": {
    "length": "string|null",
    "width": "string|null",
    "height": "string|null",
    "unit": "string|null"
  },
  "use_case": "string",
  "requirements": ["string"],
  "attachments_present": true,
  "summary": "string",
  "missing_information": ["string"],
  "confidence": 0.0
}
```

## Quick Start
1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Configure environment:
```bash
cp .env.example .env
```
4. Add your API key in `.env`:
```env
OPENAI_API_KEY=your_real_key_here
```
5. Run:
```bash
python main.py
```

## Repo Structure
```text
.
|-- .env.example
|-- .gitignore
|-- README.md
|-- docs
|   |-- loom_script.md
|   |-- make_or_n8n_option.md
|   `-- workflow_overview.md
|-- main.py
|-- output
|   `-- example_output.json
|-- prompts
|   |-- extraction_prompt.txt
|   `-- system_prompt.txt
|-- requirements.txt
`-- sample_email.txt
```

## Design Choices
- **Simple and interview-appropriate:** one clear entry point (`main.py`) and no unnecessary framework overhead.
- **Prompt-driven extraction:** prompt files are externalized in `prompts/` for easy iteration.
- **Provider abstraction:** LLM call path is isolated so Claude/Gemini can be added later without redesigning the app.
- **Schema normalization:** output is validated/normalized into predictable fields for downstream system reliability.
- **Operationally realistic:** includes missing-information detection and confidence scoring for human review workflows.

## Sample Input / Output
- Input: `sample_email.txt`
- Output: `output/example_output.json`

Input excerpt:
```text
Subject: Quote Request - Custom Flight Case for Thermal Camera Kit
...
- Target external dimensions: 620 mm (L) x 420 mm (W) x 280 mm (H)
- Case must be waterproof, shock-resistant, and suitable for ATA-style transit.
...
I have attached:
1) a simple internal layout sketch (PDF)
2) one reference photo of our current case setup (JPG)
```

Output excerpt:
```json
{
  "product_type": "Custom shock-resistant flight case for thermal camera inspection kit",
  "dimensions": {
    "length": "620",
    "width": "420",
    "height": "280",
    "unit": "mm"
  },
  "attachments_present": true,
  "confidence": 0.93
}
```

## How This Scales
This can evolve into a production intake flow:
1. Email ingestion captures new enquiries.
2. AI extraction standardizes free-text into structured JSON.
3. Rule checks and optional human review handle low confidence or missing data.
4. Structured records are pushed into CRM/ERP/MRP quoting and planning workflows.

See:
- `docs/workflow_overview.md`
- `docs/make_or_n8n_option.md`
- `docs/loom_script.md`

## Future ERP/MRP Integration
- Create enquiry records with structured technical/commercial fields
- Trigger quote-preparation tasks for engineering/sales
- Route missing information back to account managers for follow-up
- Feed approved data into planning/BOM workflows

## Notes
- This is a prototype for interview demonstration.
- API usage may incur provider costs.
