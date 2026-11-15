"""Compare committed repository metadata with the actual FastAPI application."""
import json
from pathlib import Path

from tests.client import Client
import httpx
from jsonschema import Draft202012Validator
import yaml

from main import app
from routes import CONFIG
from service import create_app

ROOT = Path(__file__).resolve().parent.parent


def test_catalog_contract():
    component, api = list(yaml.safe_load_all((ROOT / "catalog-info.yaml").read_text()))
    assert component["kind"] == "Component" and api["kind"] == "API"
    assert component["metadata"]["name"] == CONFIG.name, "catalog name drift"
    assert component["spec"]["owner"] == api["spec"]["owner"] == "group:default/" + CONFIG.owner, "catalog owner drift"
    assert api["metadata"]["name"] == CONFIG.name + "-api", "API name drift"
    annotations = component["metadata"]["annotations"]
    for key, value in {"http-method": CONFIG.method, "http-route": CONFIG.route, "http-port": str(CONFIG.port)}.items():
        assert str(annotations["acmesecure.example/" + key]) == value, f"catalog {key} drift"
    assert annotations["backstage.io/techdocs-ref"] == "dir:.", "TechDocs must be owned in this repository"
    names = [dependency.name for dependency in CONFIG.dependencies]
    assert sorted(component["spec"]["dependsOn"]) == sorted("component:default/" + name for name in names), "dependsOn drift"
    assert sorted(component["spec"]["consumesApis"]) == sorted(name + "-api" for name in names), "consumesApis drift"
    assert component["spec"]["providesApis"] == [CONFIG.name + "-api"], "providesApis drift"
    contract_text = (ROOT / "openapi.yaml").read_text()
    assert api["spec"]["definition"] == contract_text, "embedded API drift: explicitly run python tools/sync-api.py and review the diff"
    committed = yaml.safe_load(contract_text)
    assert committed == app.openapi(), "OpenAPI drift: routes.py/models changed; explicitly run python tools/sync-api.py and review the diff"
    actual = {(method, route.path) for route in app.routes if getattr(route, "include_in_schema", False) for method in route.methods}
    documented = {(method.upper(), path) for path, item in committed["paths"].items() for method in item if method in {"get", "post", "put", "patch", "delete", "head", "options"}}
    assert actual == documented, "registered HTTP routes drift"
    table = {}
    for line in (ROOT / "docs/index.md").read_text().splitlines():
        cells = line.strip().split("|")
        if len(cells) == 4:
            table[cells[1].strip()] = cells[2].strip().strip("`")
    expected = {"Service": CONFIG.name, "Owner": CONFIG.owner, "HTTP endpoint": f"{CONFIG.method} {CONFIG.route}",
                "Port": str(CONFIG.port), "Dependencies": ", ".join(names) or "none",
                "Result fields": ", ".join(sorted(CONFIG.result_model.model_fields))}
    for label, value in expected.items():
        assert table.get(label) == value, f"TechDocs interface drift: {label} must be {value!r}"
    for name in ["README.md", "docs/runbook.md", "docs/qa.md", "ci/check.sh", "ci/build-docs.sh", ".gitlab-ci.yml", "CODEOWNERS"]:
        assert (ROOT / name).is_file(), f"Missing repository-owned file {name}"
    docs_config = yaml.safe_load((ROOT / "mkdocs.yml").read_text())
    assert docs_config.get("docs_dir", "docs") == "docs", "TechDocs sources must remain in this repository"

    def check_nav(nav):
        if isinstance(nav, list):
            for item in nav:
                check_nav(item)
        elif isinstance(nav, dict):
            for item in nav.values():
                check_nav(item)
        elif isinstance(nav, str):
            source = (ROOT / "docs" / nav).resolve()
            assert source.is_relative_to((ROOT / "docs").resolve()) and source.is_file(), f"Missing or external TechDocs source {nav}"
    check_nav(docs_config["nav"])


def test_actual_response_matches_schema():
    # Providers are stubbed, so the repository can run CI without any siblings.
    client = Client(create_app(CONFIG, transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True}))))
    headers = {"X-Request-ID": "qa-contract-001"}
    if CONFIG.method == "POST":
        response = client.post(CONFIG.route, json={"tenant_id": "tenant-acme"}, headers=headers)
    else:
        response = client.get(CONFIG.route.replace("{tenantID}", "tenant-acme"), headers=headers)
    assert response.status_code == 200, response.text
    contract = app.openapi()
    response_schema = contract["paths"][CONFIG.route][CONFIG.method.lower()]["responses"]["200"]["content"]["application/json"]["schema"]
    Draft202012Validator({**response_schema, "components": contract["components"]}).validate(response.json())
    assert response.json()["checked_dependencies"] == [d.name for d in CONFIG.dependencies]
    assert response.headers["X-Request-ID"] == response.json()["request_id"] == "qa-contract-001"
