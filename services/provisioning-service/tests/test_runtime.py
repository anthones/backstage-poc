"""Real ASGI handlers with injected HTTP transports; no listening ports required."""
import asyncio
from dataclasses import replace
import time

from tests.client import Client
import httpx
import pytest

from routes import CONFIG
from service import Dependency, create_app

HEADERS = {"X-Request-ID": "qa-correlation-001"}


def invoke(client, config=CONFIG, tenant="tenant-acme", headers=HEADERS):
    if config.method == "POST":
        return client.post(config.route, json={"tenant_id": tenant}, headers=headers)
    return client.get(config.route.replace("{tenantID}", tenant), headers=headers)


def test_preserves_root_cause_across_two_boundaries():
    cause = {"service": "policy-service", "owner": "cloud-security", "code": "policy_unavailable"}
    def failed_provider(request):
        assert request.headers["X-Request-ID"] == HEADERS["X-Request-ID"]
        return httpx.Response(503, json={"error": "policy_unavailable", "request_id": HEADERS["X-Request-ID"], "root_cause": cause})
    middle_config = replace(CONFIG, name="provisioning-service", method="GET", route="/v1/workspaces/{tenantID}",
                            dependencies=(Dependency("policy-service", "cloud-security", 8083, "/v1/policies/{tenantID}"),))
    middle = create_app(middle_config, transport=httpx.MockTransport(failed_provider))
    async def call_middle(request):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=middle), base_url="http://middle") as client:
            return await client.get(request.url.path, headers={"X-Request-ID": request.headers["X-Request-ID"]})
    top_config = replace(CONFIG, dependencies=(Dependency("provisioning-service", "cloud-security", 8084, "/v1/workspaces/{tenantID}"),))
    response = invoke(Client(create_app(top_config, transport=httpx.MockTransport(call_middle))), top_config)
    assert response.status_code == 502
    assert response.json()["root_cause"] == cause
    assert response.json()["failed_dependency"] == "provisioning-service"
    assert response.json()["request_id"] == HEADERS["X-Request-ID"]


def test_dependency_timeout_is_bounded_and_named():
    async def slow_provider(request):
        await asyncio.sleep(1)
        return httpx.Response(200)
    config = replace(CONFIG, dependencies=(Dependency("slow-provider", "provider-team", 9999, "/lookup"),))
    client = Client(create_app(config, transport=httpx.MockTransport(slow_provider), dependency_timeout=0.01))
    started = time.monotonic()
    response = invoke(client, config)
    assert response.status_code == 502
    assert response.json()["root_cause"] == {"service": "slow-provider", "owner": "provider-team", "code": "unreachable_or_timeout"}
    assert time.monotonic() - started < 1


def test_total_budget_bounds_sequential_dependencies():
    async def provider(request):
        await asyncio.sleep(0.02)
        return httpx.Response(200)
    config = replace(CONFIG, dependencies=tuple(Dependency(f"provider-{i}", "provider-team", 9999, "/lookup") for i in range(5)))
    client = Client(create_app(config, transport=httpx.MockTransport(provider), dependency_timeout=1, operation_timeout=0.03))
    response = invoke(client, config)
    assert response.status_code == 502
    assert response.json()["root_cause"]["code"] == "unreachable_or_timeout"


@pytest.mark.parametrize("body", [{}, {"tenant_id": "../secret"}, {"tenant_id": "x" * 65}, {"tenant_id": 123}])
def test_invalid_input_never_calls_provider(body):
    def unexpected(request):
        raise AssertionError("Invalid input reached provider")
    config = replace(CONFIG, method="POST", route="/v1/activations")
    client = Client(create_app(config, transport=httpx.MockTransport(unexpected)))
    assert client.post(config.route, json=body).status_code == 400
    assert client.post(config.route, content="{", headers={"Content-Type": "application/json"}).status_code == 400


def test_fault_is_opt_in_and_recovery_restores_readiness(monkeypatch):
    config = replace(CONFIG, name="policy-service", owner="cloud-security")
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    monkeypatch.setenv("ENABLE_DEMO_CONTROLS", "false")
    assert Client(create_app(config)).post("/demo/fault", json={"enabled": True}).status_code == 404
    monkeypatch.setenv("ENABLE_DEMO_CONTROLS", "true")
    client = Client(create_app(config, transport=transport))
    assert client.post("/demo/fault", json={"enabled": "true"}).status_code == 400
    assert client.post("/demo/fault", json={"enabled": True}).status_code == 200
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503
    assert invoke(client, config).status_code == 503
    client.post("/demo/fault", json={"enabled": False})
    assert invoke(client, config).status_code == 200


def test_invalid_request_id_is_replaced_and_forwarded():
    seen = []
    def provider(request):
        seen.append(request.headers["X-Request-ID"])
        return httpx.Response(200)
    config = replace(CONFIG, dependencies=(Dependency("provider", "team", 9999, "/lookup"),))
    client = Client(create_app(config, transport=httpx.MockTransport(provider)))
    response = invoke(client, config, headers={"X-Request-ID": "invalid id"})
    assert response.status_code == 200
    assert seen == [response.headers["X-Request-ID"]]
    assert len(seen[0]) == 32


def test_invalid_upstream_error_has_attributable_fallback():
    config = replace(CONFIG, dependencies=(Dependency("broken-provider", "provider-team", 9999, "/lookup"),))
    client = Client(create_app(config, transport=httpx.MockTransport(lambda request: httpx.Response(503, text="unstructured error"))))
    response = invoke(client, config)
    assert response.status_code == 502
    assert response.json()["root_cause"] == {"service": "broken-provider", "owner": "provider-team", "code": "upstream_error"}
