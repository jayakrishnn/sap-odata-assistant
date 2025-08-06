# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
import asyncio
from dotenv import load_dotenv
import re
from requests.exceptions import HTTPError

from .metadata import list_all_services, load_metadata
from .llm_router import plan_calls
from .odata_client import query_odata

# ─── Load environment variables ─────────────────────────────────────────────────
load_dotenv()

# ─── Initialize FastAPI and metadata ─────────────────────────────────────────────
app = FastAPI()
services = list_all_services()
metadata_registry = {srv: load_metadata(srv) for srv in services}


@app.post("/query")
async def query_endpoint(body: dict):
    # ─── Parse & validate inputs ─────────────────────────────────────────────────
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")

    limit = body.get("limit")
    offset = body.get("offset")

    # Validate limit
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 1:
                raise ValueError()
        except ValueError:
            raise HTTPException(status_code=400, detail="`limit` must be a positive integer")

    # Validate offset
    if offset is not None:
        try:
            offset = int(offset)
            if offset < 0:
                raise ValueError()
        except ValueError:
            raise HTTPException(status_code=400, detail="`offset` must be a non-negative integer")

    # ─── 1) LLM Planning ───────────────────────────────────────────────────────────
    try:
        plan = plan_calls(question, metadata_registry)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"LLM planning failed: {e}")

    # ─── 2) Detect “first N” fallback if no explicit limit ─────────────────────────
    top_n = None
    if limit is None:
        m = re.search(r"\bfirst\s+(\d+)\b", question, re.IGNORECASE)
        if m:
            top_n = int(m.group(1))

    # ─── 3) Prepare concurrent OData calls ─────────────────────────────────────────
    tasks = []
    for call in plan:
        service = call.get("service")
        entity = call.get("entity")
        params = {}

        if call.get("filter"):
            params["$filter"] = call["filter"]
        if call.get("select"):
            params["$select"] = ",".join(call["select"])
        # Paging logic
        if limit is not None:
            params["$top"] = limit
        elif top_n:
            params["$top"] = top_n
        if offset is not None:
            params["$skip"] = offset

        # Schedule in threadpool
        tasks.append(
            run_in_threadpool(query_odata, service, entity, params)
        )

    # ─── 4) Execute tasks concurrently ─────────────────────────────────────────────
    try:
        datas = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OData parallel calls failed: {e}")

    # ─── 5) Pair calls with their results ─────────────────────────────────────────
    results = [
        {"call": plan[i], "data": datas[i]}
        for i in range(len(plan))
    ]

    # ─── 6) Build pagination metadata ────────────────────────────────────────────
    pagination = {}
    if limit is not None:
        pagination["limit"] = limit
    if offset is not None:
        pagination["offset"] = offset
    if limit is not None and offset is not None:
        pagination["next_offset"] = offset + limit

    # ─── Return final response ───────────────────────────────────────────────────
    response = {"plan": plan, "results": results}
    if pagination:
        response["pagination"] = pagination
    return response
