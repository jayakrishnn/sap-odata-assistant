# app/http_client.py

from pathlib import Path
from dotenv import load_dotenv
import os, requests

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SAP_IP       = os.getenv("SAP_HOST_IP").strip()
SAP_PORT     = os.getenv("SAP_PORT", "").strip()
SAP_HOSTNAME = os.getenv("SAP_HOSTNAME").strip()
SAP_CLIENT   = os.getenv("SAP_CLIENT", "").strip()
SAP_USERNAME = os.getenv("SAP_USERNAME", "").strip()
SAP_PASSWORD = os.getenv("SAP_PASSWORD", "").strip()
SAP_AUTH     = (SAP_USERNAME, SAP_PASSWORD)
VERIFY_CERT  = False  # or your CA bundle path

def sap_get(path: str, params: dict = None, skip_format: bool = False):
    """
    HTTP GET to SAP. 
    - Always adds sap-client.
    - Adds $format=json only if skip_format=False.
    - Sends Accept: application/xml for metadata; application/json otherwise.
    """
    if params is None:
        params = {}
    # sap-client always
    if SAP_CLIENT:
        params["sap-client"] = SAP_CLIENT

    # Only inject JSON format on data calls
    if not skip_format:
        params.setdefault("$format", "json")

    # Choose Accept header
    headers = {"Host": SAP_HOSTNAME}
    if skip_format:
        headers["Accept"] = "application/xml"
    else:
        headers["Accept"] = "application/json"

    url = f"https://{SAP_IP}{SAP_PORT}{path}"
    resp = requests.get(
        url, auth=SAP_AUTH, headers=headers, params=params, verify=VERIFY_CERT
    )
    # Clearer 401 message
    if resp.status_code == 401:
        raise RuntimeError("SAP 401 Unauthorized—check your SAP_USERNAME/SAP_PASSWORD")
    resp.raise_for_status()
    return resp
