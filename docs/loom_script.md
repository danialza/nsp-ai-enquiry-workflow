# Loom Script (3-5 Minutes)

## 0:00 - 0:40 | Problem Context
"In this demo, I'm solving a practical NSP Cases workflow problem. Sales enquiries for custom flight cases come in as free-text emails, sometimes with attachment references, and key quote inputs are often buried in the message.  
This creates manual effort and risk of missing important details before quoting."

## 0:40 - 1:40 | What the Prototype Does
"This mini project takes a sample enquiry email and runs it through an AI extraction step.  
It outputs a structured JSON object with the fields a business team actually needs:
product type, dimensions, use case, requirements, attachment flag, concise summary, missing information, and confidence.

The script prints the JSON and saves it locally, so it is easy to inspect, test, and version in GitHub."

## 1:40 - 2:50 | Quick Walkthrough
"At the top level, `main.py` orchestrates the flow.  
Prompts are stored separately in the `prompts` folder, which makes prompt tuning simple without changing Python logic.  
The provider call is isolated in one function, so this can evolve from OpenAI today to Claude or Gemini later.

The code also normalizes model output to a stable schema and includes basic error handling for missing files, API issues, and JSON parse failures."

## 2:50 - 3:50 | Why This Design
"The design is intentionally simple and practical:
- local-first and easy to run
- structured output for system handoff
- provider abstraction for future flexibility
- no overengineering

This is exactly the level of solution I'd use as a first production stepping stone: useful now, but still easy to scale."

## 3:50 - 4:40 | How It Scales
"In a larger workflow, incoming emails can trigger this extraction automatically.  
A human review checkpoint can approve or correct low-confidence outputs.  
Approved data can then feed ERP/MRP or CRM processes like quote creation, engineering review, and planning tasks.

So AI handles unstructured text intake, while core operational systems remain the source of record."

## 4:40 - 5:00 | Close
"This prototype demonstrates a credible, interview-ready workflow that is clean, understandable, and extensible for real operations."
