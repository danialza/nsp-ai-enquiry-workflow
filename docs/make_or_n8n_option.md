# Optional Automation Design (Make or n8n)

This document shows how the same workflow can be automated in Make or n8n without changing the core extraction concept.

## Target Flow
1. Trigger from incoming enquiry email
2. Read subject/body (and attachment metadata if available)
3. Send email content to LLM extraction step
4. Parse structured JSON response
5. Write result to table/CRM/ERP intake step
6. Optionally alert a human reviewer when confidence is low or key fields are missing

## Option A: n8n (Self-Hosted Friendly)
### Suggested node sequence
1. **IMAP Email Trigger** or **Microsoft Outlook/Gmail Trigger**  
   Watches a mailbox/folder for new NSP enquiries.
2. **Set / Function Node**  
   Cleans and combines subject + body into one text payload.
3. **HTTP Request Node (LLM API)**  
   Sends prompt + email text and asks for strict JSON.
4. **Code Node / JSON Parse**  
   Validates and parses the JSON fields.
5. **IF Node**  
   If `confidence < threshold` OR `missing_information` non-empty, route to human review.
6. **Destination Node**  
   Write structured record to Google Sheet, Airtable, HubSpot, or ERP webhook endpoint.

### Why n8n here
- Can be hosted privately
- Good fit for operational workflows and custom logic
- Easy to add approval steps and notifications

## Option B: Make
### Suggested module sequence
1. **Email module trigger** (Gmail/Outlook/IMAP)
2. **Text aggregator/formatter**
3. **HTTP module to LLM API**
4. **JSON parser module**
5. **Router module**
   - Route A: send to review queue
   - Route B: push to CRM/ERP step directly
6. **Data store module**
   Save structured enquiry output

### Why Make here
- Fast setup for business teams
- Strong prebuilt app integrations
- Easy visual routing for non-technical stakeholders

## Production Notes
- Keep prompt and schema versioned in Git.
- Add retries and rate-limit handling around LLM calls.
- Log extraction outcomes for QA (confidence, missing fields, manual corrections).
- Use a human-in-the-loop checkpoint during early rollout.
- Push approved records into ERP/MRP through API endpoints or integration middleware.
