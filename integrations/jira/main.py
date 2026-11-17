"""Read-only Jira adapter: real public issues and an explicit fictional scenario."""
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
import httpx
import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("scenario.json")
FIELDS = "summary,status,issuetype,issuelinks"


def components():
    paths = [*sorted((ROOT / "services").glob("*/catalog-info.yaml")), ROOT / "frontend/customer-portal/catalog-info.yaml"]
    result = []
    for path in paths:
        entity = next(e for e in yaml.safe_load_all(path.read_text()) if e["kind"] == "Component")
        annotations = entity["metadata"].get("annotations", {})
        project = annotations.get("jira/project-key")
        label = annotations.get("acmesecure.example/jira-label")
        if project and label:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", project) or not re.fullmatch(r"[a-z0-9-]+", label):
                raise ValueError("Invalid catalog Jira mapping")
            result.append({"name": entity["metadata"]["name"], "title": entity["metadata"].get("title", entity["metadata"]["name"]),
                           "owner": entity["spec"]["owner"].split("/")[-1], "project": project, "label": label})
    return result


def normalize(issue, base_url=None):
    fields = issue["fields"]
    links = []
    for link in fields.get("issuelinks", []):
        for side, direction in (("outwardIssue", "outward"), ("inwardIssue", "inward")):
            if side in link:
                links.append({"key": link[side]["key"], "relationship": link["type"][direction]})
    return {"key": issue["key"], "summary": fields["summary"], "status": fields["status"]["name"],
            "type": fields.get("issuetype", {}).get("name", "Task"), "links": links,
            "url": f"{base_url}/browse/{issue['key']}" if base_url else None,
            "handover": fields.get("handover", "")}


def create_app(transport=None):
    app = FastAPI(docs_url=None, redoc_url=None)

    @app.get("/healthz")
    async def health():
        return {"status": "alive"}

    @app.get("/components")
    async def list_components():
        return components()

    @app.get("/issues")
    async def issues(source: str = Query(default="public", pattern="^(public|scenario)$"), component: str | None = None):
        fetched = datetime.now(timezone.utc).isoformat()
        if source == "scenario":
            mappings = {c["name"]: c for c in components()}
            if component and component not in mappings:
                raise HTTPException(404, "No Jira mapping for this component")
            mapping = mappings.get(component)
            dataset = json.loads(FIXTURE.read_text())
            selected = [i for i in dataset if not mapping or
                        (i["key"].startswith(mapping["project"] + "-") and mapping["label"] in i["fields"]["labels"])]
            return {"source": "scenario", "notice": "Fictional activation handover example — not connected Jira records.",
                    "fetched_at": fetched, "issues": [normalize(i) for i in selected], "has_more": False,
                    "jql": f'project = "{mapping["project"]}" AND labels = "{mapping["label"]}"' if mapping else 'project = "ACT"',
                    "component": mapping}
        if component:
            raise HTTPException(400, "Public Atlassian issues are not mapped to the fictional service catalog")
        base = "https://jira.atlassian.com"
        jql = "project = JRASERVER ORDER BY updated DESC"
        try:
            async with httpx.AsyncClient(transport=transport, timeout=12, follow_redirects=False) as client:
                response = await client.get(base + "/rest/api/2/search", params={"jql": jql, "maxResults": 5, "fields": FIELDS},
                                            headers={"Accept": "application/json"})
                response.raise_for_status()
                data = response.json()
                normalized = [normalize(i, base) for i in data["issues"]]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            # Do not silently replace live records with fictional records.
            raise HTTPException(503, "Public Jira is unavailable. Retry, or explicitly choose the fictional activation example.") from None
        return {"source": "public", "notice": "Live read-only Atlassian public tracker. These issues are unrelated to our fictional services.",
                "fetched_at": fetched, "issues": normalized, "has_more": data.get("total", 0) > len(normalized),
                "jql": jql, "component": None, "browse_url": base + "/issues/?jql=" + str(httpx.QueryParams({"jql": jql})).removeprefix("jql=")}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("JIRA_ADAPTER_PORT", "8090")))
