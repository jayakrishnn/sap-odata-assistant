# app/metadata.py

from pathlib import Path
from dotenv import load_dotenv
import os
from functools import lru_cache
from lxml import etree
from .http_client import sap_get

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

@lru_cache(maxsize=None)
def load_metadata(service_name: str):
    """
    Fetch & parse the $metadata XML from SAP OData V2,
    returning a dict: { EntitySetName: [prop1, prop2, ...], ... }
    """
    path = f"/sap/opu/odata/sap/{service_name}/$metadata"    
    resp = sap_get(path, skip_format=True)
    xml = etree.fromstring(resp.content)

    registry = {}
    # Use XPath to find EntitySet nodes (namespace-agnostic)
    entity_sets = xml.xpath('//*[local-name()="EntitySet"]')
    for es in entity_sets:
        set_name = es.get("Name")
        # EntityType attr looks like "Namespace.Type"; take the short name
        etype = es.get("EntityType").split(".")[-1]

        # Find matching EntityType's Property children
        prop_xpath = (
            f'//*[local-name()="EntityType" and @Name="{etype}"]/*[local-name()="Property"]'
        )
        props = [p.get("Name") for p in xml.xpath(prop_xpath)]

        registry[set_name] = props

    return registry

def list_all_services():
    """
    List your OData service names here.
    Add more as you onboard services.
    """
    return [
        "Z_SALESORDER_SRV",
        "Z_BILLINGDOCBASIC_SRV",
        # …add the rest…
    ]
