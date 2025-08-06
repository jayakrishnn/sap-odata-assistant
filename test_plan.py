# test_plan.py

from dotenv import load_dotenv
from pathlib import Path
import json, logging

# 1) Load your .env so GEMINI_API_KEY is available
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2) Import your modules
from app.metadata import list_all_services, load_metadata
from app.llm_router import plan_calls

# 3) Set up logging to console
logging.basicConfig(level=logging.INFO)

# 4) Build a minimal metadata_registry
services = list_all_services()
registry = {srv: load_metadata(srv) for srv in services}

# 5) Call plan_calls with your real prompt
question = "List the first 5 entries of SalesOrderSet"
logging.info("Running plan_calls for question: %r", question)

try:
    calls = plan_calls(question, registry)
    print("Parsed calls JSON:")
    print(json.dumps(calls, indent=2))
except Exception as e:
    print("ERROR:", e)
