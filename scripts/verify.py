"""Acceptance checks against the six running, dedicated local POC services."""
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request
import yaml
from load_model import load_model

ROOT = Path(__file__).resolve().parent.parent
MODEL = load_model()
checks = 0


def call(port, path, body=None, raw=False):
    request = urllib.request.Request(f"http://localhost:{port}{path}", data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json", "X-Request-ID": "qa-release-001"})
    try:
        response = urllib.request.urlopen(request, timeout=8)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        content = response.read().decode()
        return response.status, content if raw else json.loads(content), response.headers


def expect(condition, message):
    global checks
    assert condition, message
    checks += 1


def fault(enabled):
    status, _, _ = call(8083, "/demo/fault", {"enabled": enabled})
    expect(status == 200, "Policy demonstration controls are unavailable. Use scripts/start.sh or Compose.")


def lookup(service, tenant):
    if service["name"] == "onboarding-service":
        return call(service["port"], service["route"], {"tenant_id": tenant})
    return call(service["port"], service["route"].replace("{tenantID}", tenant))


def main():
    subprocess.run(["node", "scripts/check-catalog.cjs"], cwd=ROOT, check=True)
    # Export actual catalog declarations; compare both fixture metadata and runtime info.
    declarations = [next(e for e in yaml.safe_load_all((ROOT / "services" / s["name"] / "catalog-info.yaml").read_text()) if e["kind"] == "Component") for s in MODEL]
    fault(False)
    for service, entity in zip(MODEL, declarations):
        name, port = service["name"], service["port"]
        status, info, _ = call(port, "/info")
        dependencies = [d["name"] for d in (info["dependencies"] or [])]
        expect(status == 200 and info["owner"] == service["owner"], f"{name} owner mismatch")
        expect(dependencies == service["dependencies"] == [r.split("/")[-1] for r in entity["spec"]["dependsOn"]], f"{name} dependency drift")
        expect(entity["spec"]["owner"] == "group:default/" + info["owner"], f"{name} catalog owner drift")
        status, contract, _ = call(port, "/openapi.yaml", raw=True)
        expect(status == 200 and yaml.safe_load(contract)["openapi"] == "3.1.0", f"{name} missing API contract")
        for probe in ["/healthz", "/readyz"]:
            expect(call(port, probe)[0] == 200, f"{name} {probe} failed")
    for tenant, expected, owner in [
        ("tenant-acme", [200, 200, 200, 200, 200, 200], None),
        ("tenant-suspended", [200, 409, 200, 502, 200, 502], "commerce"),
        ("tenant-missing", [404, 502, 502, 502, 502, 502], "identity"),
    ]:
        for service, wanted in zip(MODEL, expected):
            status, body, headers = lookup(service, tenant)
            expect(status == wanted, f"{service['name']} {tenant}: got {status}, wanted {wanted}: {body}")
            expect(headers["X-Request-ID"] == body["request_id"] == "qa-release-001", "Correlation ID lost")
            if status == 200:
                expect(body["simulation"] is True and body["checked_dependencies"] == service["dependencies"], "Incomplete dependency checks")
            else:
                expect(body["root_cause"]["owner"] == owner, f"Wrong owner: {body}")
    fault(True)
    expect(call(8083, "/healthz")[0] == 200 and call(8083, "/readyz")[0] == 503, "Liveness/readiness distinction lost")
    for service, wanted in zip(MODEL, [200, 200, 503, 502, 200, 502]):
        status, body, _ = lookup(service, "tenant-acme")
        expect(status == wanted, f"Outage blast radius wrong for {service['name']}")
        if wanted != 200:
            expect(body["root_cause"] == {"service": "policy-service", "owner": "cloud-security", "code": "policy_unavailable"}, f"Root cause lost: {body}")
    fault(False)
    expect(lookup(MODEL[-1], "tenant-acme")[0] == 200, "Journey did not recover")
    expect(call(8086, "/v1/activations", {})[0] == 400, "Missing tenant was accepted")
    expect(call(8086, "/v1/activations", {"tenant_id": "../secret"})[0] == 400, "Invalid tenant was accepted")
    print(f"PASS: {checks} acceptance checks across six services, catalog agreement, failure routing, and recovery.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            fault(False)
        except (OSError, ValueError):
            pass
