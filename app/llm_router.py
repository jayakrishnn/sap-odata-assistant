# app/llm_router.py

from pathlib import Path
from dotenv import load_dotenv
import os
import json
import logging
import re
from google import genai

# ─── Load .env ───────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

# ─── Initialize Gemini client ─────────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY/GOOGLE_API_KEY in .env")
client = genai.Client(api_key=api_key)

# ─── Prompt template ──────────────────────────────────────────────────────────
# We explicitly tell the model to NOT use markdown or code fences—only raw JSON.
PROMPT_TEMPLATE = """
You have access to these OData services and their entity sets:
{service_summaries}

Below are examples of valid JSON-only responses:

Example 1 – simple select:
Input question: "Show me all customers with country = 'US'"
Output:
[
  {{
    "service": "Z_CUSTOMER_SRV",
    "entity": "CustomerSet",
    "filter": "Country eq 'US'",
    "select": ["CustomerID","Name","Country"]
  }}
]

Example 2 – multi-service:
Input question: "Get sales orders above 1000 and corresponding invoices"
Output:
[
  {{
    "service": "Z_SALESORDER_SRV",
    "entity": "I_SalesOrder",
    "filter": "NetAmount gt 1000",
    "select": ["SalesOrder","NetAmount","CustomerID"]
  }},
  {{
    "service": "Z_BILLINGDOCBASIC_SRV",
    "entity": "BillingDocumentBasicSet",
    "filter": "NetAmount gt 1000",
    "select": ["BillingDocument","NetAmount","SalesOrderID"]
  }}
]

Now, given the user’s question, return **only** a JSON array of objects with keys:
  - "service": the OData service name  
  - "entity": the EntitySet  
  - "filter": the $filter expression or empty string  
  - "select": an array of fields

Do not output any extra text—only the JSON array.

User question: "{question}"
"""


def plan_calls(question: str, metadata_registry: dict):
    # Build the prompt
    summaries = "\n".join(
        f"- {srv}: Entities({', '.join(metadata_registry[srv].keys())})"
        for srv in metadata_registry
    )
    prompt = PROMPT_TEMPLATE.format(
        service_summaries=summaries,
        question=question
    )
    logging.info("LLM prompt:\n%s", prompt)

    # Call Gemini
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    raw = resp.text or ""
    logging.info("LLM raw response.text: %r", raw)

    # Strip out any markdown fences and whitespace, then grab only the JSON
    no_fences = re.sub(r"```[a-zA-Z]*", "", raw)
    no_fences = no_fences.strip()
    start = no_fences.find("[")
    end   = no_fences.rfind("]") + 1
    if start < 0 or end < start:
        logging.error("Failed to find JSON array in LLM output: %r", no_fences)
        raise ValueError(f"No JSON array found in LLM output")
    clean = no_fences[start:end]
    logging.info("LLM cleaned JSON text: %r", clean)

    # Parse it
    try:
        calls = json.loads(clean)
    except json.JSONDecodeError as e:
        logging.error("JSON parse error: %s", e)
        logging.error("Bad JSON was:\n%s", clean)
        raise ValueError(f"Invalid JSON from LLM: {e}")

    return calls
