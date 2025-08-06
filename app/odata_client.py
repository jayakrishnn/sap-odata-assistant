# app/odata_client.py

from .http_client import sap_get
from requests.exceptions import RequestException, HTTPError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    before_log,
)
import logging
import time

logger = logging.getLogger(__name__)

# ─── In-memory TTL cache for OData results ─────────────────────────────────
_CACHE = {}
_CACHE_TTL = 300  # seconds

# Retry up to 3 times, waiting 2s between tries, for transient errors
@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=(retry_if_exception_type(RequestException) |
           retry_if_exception_type(HTTPError)),
    before=before_log(logger, logging.WARNING),
)
def query_odata(service: str, entity: str, params: dict):
    """
    Calls SAP via sap_get and returns the JSON results array.
    Retries on ConnectionError, Timeout, and HTTP 5xx.
    Caches results in-memory for TTL seconds.
    """
    # Create a cache key based on service, entity, and sorted params
    key = (
        service,
        entity,
        tuple(sorted(params.items())) if params else (),
    )
    now = time.time()
    # Check cache
    if key in _CACHE:
        data, timestamp = _CACHE[key]
        if now - timestamp < _CACHE_TTL:
            logger.info(f"Cache hit for {service}/{entity} with params {params}")
            return data
        else:
            # expired
            del _CACHE[key]

    # Cache miss: perform the OData call
    path = f"/sap/opu/odata/sap/{service}/{entity}"
    resp = sap_get(path, params=params)
    data = resp.json()
    # Unwrap OData V2 payload
    if isinstance(data, dict) and "d" in data and "results" in data["d"]:
        results = data["d"]["results"]
    else:
        results = data

    # Store in cache
    _CACHE[key] = (results, now)
    logger.info(f"Cache set for {service}/{entity} with params {params}")
    return results
