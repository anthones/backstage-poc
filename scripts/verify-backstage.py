"""Verify the running catalog and TechDocs through Backstage's actual APIs."""
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
from load_model import load_model

ROOT = Path(__file__).resolve().parent.parent
MODEL = load_model()
BASE = "http://localhost:7007"


def get(path, token=None, raw=False):
    headers = {"X-Requested-With": "XMLHttpRequest"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=headers), timeout=10) as response:
        content = response.read().decode()
        return content if raw else json.loads(content)


def main():
    get("/.backstage/health/v1/readiness")
    # Authenticate using the POC's explicit development Guest provider. Never print tokens.
    identity = get("/api/auth/guest/refresh")
    token = identity["backstageIdentity"]["token"]
    deadline = time.monotonic() + 45
    while True:
        entities = get("/api/catalog/entities", token)
        apis = [e for e in entities if e["kind"] == "API"]
        if len(apis) == 6:
            break
        if time.monotonic() > deadline:
            raise AssertionError(f"Expected six ingested APIs; got {len(apis)}. Inspect catalog processing errors.")
        time.sleep(1)
    components = {e["metadata"]["name"]: e for e in entities if e["kind"] == "Component"}
    assert len(components) == 6, f"Expected exactly six domain-owned documentation sites, got {len(components)} components"
    edges = 0
    for service in MODEL:
        entity = components[service["name"]]
        source = entity["metadata"]["annotations"]["backstage.io/managed-by-location"]
        assert source.endswith(f"/services/{service['name']}/catalog-info.yaml"), f"Service is not ingested from its own repository: {source}"
        relations = sorted(r["targetRef"] for r in entity["relations"] if r["type"] == "dependsOn")
        assert relations == sorted("component:default/" + d for d in service["dependencies"]), service["name"]
        edges += len(relations)
        assert not entity.get("status", {}).get("items"), f"Processing error on {service['name']}"
    assert edges == 10
    for api in apis:
        service_name = api["metadata"]["name"].removesuffix("-api")
        expected = (ROOT / "services" / service_name / "openapi.yaml").read_text()
        assert api["spec"]["definition"] == expected, f"Ingested API drift: {service_name}"
    for name in components:
        prefix = f"/api/techdocs/static/docs/default/component/{name}/"
        assert get(prefix + "techdocs_metadata.json", token)["site_name"]
        assert "<article" in get(prefix + "index.html", token, raw=True)
        index = get(prefix + "search/search_index.json", token)
        assert index["docs"], f"Missing documentation search index: {name}"
        assert "L1" in get(prefix + "runbook/index.html", token, raw=True)
        assert "QA" in get(prefix + "qa/index.html", token, raw=True)
    for page in ["repositories", "glossary", "ownership", "architecture", "incident", "handover", "presentation", "on-prem"]:
        assert "<article" in get(f"/api/techdocs/static/docs/default/component/onboarding-service/handbook/{page}/index.html", token, raw=True)
    # Search indexing is scheduled; allow the startup task to complete.
    until = time.monotonic() + 90
    query = urllib.parse.urlencode({"term": "policy_unavailable"})
    while True:
        result = get("/api/search/query?" + query, token)
        if result.get("results"):
            break
        assert time.monotonic() < until, "TechDocs search did not index the policy runbook"
        time.sleep(2)
    for path in ["/", "/home", "/demo", "/catalog-graph", "/activation-architecture.svg"]:
        request = urllib.request.Request("http://localhost:3000" + path, headers={"Accept": "text/html" if not path.endswith(".svg") else "image/svg+xml"})
        with urllib.request.urlopen(request, timeout=10) as response:
            assert response.status == 200
    print(f"PASS: {len(entities)} ingested entities, six API definitions, ten dependency edges, six repository-owned TechDocs sites, documentation search, and frontend HTTP routes.")


if __name__ == "__main__":
    main()
