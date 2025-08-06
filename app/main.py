from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import asyncio
from dotenv import load_dotenv
import os, re
from requests.exceptions import HTTPError

from .metadata import list_all_services, load_metadata
from .llm_router import plan_calls
from .odata_client import query_odata

# Load .env (for local dev)
load_dotenv()

# Initialize app and metadata
app = FastAPI()
services = list_all_services()
metadata_registry = {srv: load_metadata(srv) for srv in services}

# CORS: allow your front-end origin (set via env)
frontend_origin = os.getenv("FRONTEND_ORIGIN")  # e.g. https://sap-odata-frontend.onrender.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin] if frontend_origin else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query")
async def query_endpoint(body: dict):
    question = body.get("question", "")
    if not question:
        raise HTTPException(400, "Missing 'question'")

    # Parse paging
    limit  = body.get("limit")
    offset = body.get("offset")
    # ...validate as before...

    # 1) Plan
    try:
        plan = plan_calls(question, metadata_registry)
    except Exception as e:
        raise HTTPException(400, f"LLM planning failed: {e}")

    # 2) Detect 'first N'
    top_n = None
    if limit is None:
        m = re.search(r"\bfirst\s+(\d+)\b", question, re.I)
        if m:
            top_n = int(m.group(1))

    # 3) Concurrent OData calls
    tasks = []
    for call in plan:
        svc, ent = call["service"], call["entity"]
        params = {}
        if call.get("filter"): params["$filter"] = call["filter"]
        if call.get("select"): params["$select"] = ",".join(call["select"])
        if limit is not None: params["$top"] = limit
        elif top_n:         params["$top"] = top_n
        if offset is not None: params["$skip"] = offset
        tasks.append(run_in_threadpool(query_odata, svc, ent, params))

    try:
        datas = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(400, f"OData calls failed: {e}")

    results = [{"call": plan[i], "data": datas[i]} for i in range(len(plan))]
    # Build pagination
    pagination = {}
    if limit is not None: pagination["limit"] = limit
    if offset is not None: pagination["offset"] = offset
    if limit is not None and offset is not None:
        pagination["next_offset"] = offset + limit

    resp = {"plan": plan, "results": results}
    if pagination: resp["pagination"] = pagination
    return resp