"""Repository-local HTTP mechanics; routes.py owns the service's domain decisions."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import os
import re
import time
from typing import Annotated, Callable, Generic, Literal, TypeVar
import uuid

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
import httpx
from pydantic import BaseModel, ConfigDict, StrictBool, StringConstraints
import yaml

IDENTIFIER = re.compile(r"^[a-zA-Z0-9-]{1,64}$")
TenantID = Annotated[str, StringConstraints(pattern=IDENTIFIER.pattern)]
RequestIDHeader = Annotated[str | None, Header(alias="X-Request-ID", description="Forwarded across service boundaries. Invalid or absent IDs are replaced.")]
T = TypeVar("T", bound=BaseModel)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Cause(StrictModel):
    service: str
    owner: str
    code: str


class Failure(StrictModel):
    error: str
    request_id: str
    root_cause: Cause
    failed_dependency: str | None = None


class Success(StrictModel, Generic[T]):
    service: str
    owner: str
    request_id: str
    tenant_id: str
    checked_dependencies: list[str]
    result: T
    simulation: Literal[True]


class ActivationRequest(StrictModel):
    tenant_id: TenantID


class FaultRequest(StrictModel):
    enabled: StrictBool


@dataclass(frozen=True)
class Dependency:
    name: str
    owner: str
    port: int
    path: str

    @property
    def url(self) -> str:
        key = self.name.upper().replace("-", "_") + "_URL"
        return os.environ.get(key, f"http://127.0.0.1:{self.port}").rstrip("/")


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    title: str
    owner: str
    port: int
    method: str
    route: str
    dependencies: tuple[Dependency, ...]
    result_model: type[BaseModel]
    result: Callable[[str], BaseModel]


def create_app(config: ServiceConfig, *, transport: httpx.AsyncBaseTransport | None = None,
               dependency_timeout: float = 1.2, operation_timeout: float = 4.0) -> FastAPI:
    # Swagger assets are rendered by Backstage; services do not fetch a public CDN.
    app = FastAPI(title=config.title + " API", version="1.0.0", docs_url=None, redoc_url=None,
                  servers=[{"url": f"http://localhost:{config.port}"}])
    app.state.fault = False

    def failure(request: Request, status: int, code: str, *, dependency: Dependency | None = None,
                root: Cause | None = None) -> JSONResponse:
        value = Failure(error=code, request_id=request.state.request_id,
                        root_cause=root or Cause(service=config.name, owner=config.owner, code=code),
                        failed_dependency=dependency.name if dependency else None)
        return JSONResponse(status_code=status, content=value.model_dump(exclude_none=True))

    @app.middleware("http")
    async def correlate(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        request.state.request_id = incoming if IDENTIFIER.fullmatch(incoming) else uuid.uuid4().hex
        started = time.monotonic()
        if request.method == "POST" and len(await request.body()) > 4096:
            response = failure(request, 400, "request_too_large")
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        logging.info(json.dumps({"service": config.name, "owner": config.owner,
                                 "request_id": request.state.request_id, "path": request.url.path,
                                 "status": response.status_code, "duration_ms": round((time.monotonic() - started) * 1000, 2)}))
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _error: RequestValidationError):
        return failure(request, 400, "invalid_request")

    @app.get("/healthz", include_in_schema=False)
    async def health():
        return {"status": "alive", "service": config.name}

    @app.get("/readyz", include_in_schema=False)
    async def ready(request: Request):
        # Local readiness only. Transitive probes would amplify an outage.
        if app.state.fault:
            return failure(request, 503, "policy_unavailable")
        return {"status": "ready", "service": config.name}

    @app.get("/info", include_in_schema=False)
    async def info():
        return {"service": config.name, "owner": config.owner,
                "dependencies": [{"name": d.name, "owner": d.owner} for d in config.dependencies],
                "catalog": "component:default/" + config.name, "demo": True}

    @app.get("/openapi.yaml", include_in_schema=False)
    async def openapi_yaml():
        return Response(yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True), media_type="application/yaml")

    if config.name == "policy-service" and os.environ.get("ENABLE_DEMO_CONTROLS") == "true":
        @app.post("/demo/fault", include_in_schema=False)
        async def fault(payload: FaultRequest):
            app.state.fault = payload.enabled
            return {"enabled": app.state.fault, "service": config.name}

    async def perform(request: Request, tenant_id: str):
        if app.state.fault:
            return failure(request, 503, "policy_unavailable")
        if config.name == "tenant-service" and tenant_id not in {"tenant-acme", "tenant-suspended"}:
            return failure(request, 404, "tenant_not_found")
        checked = []
        dependency = None
        try:
            async with asyncio.timeout(operation_timeout):
                async with httpx.AsyncClient(timeout=dependency_timeout, transport=transport, trust_env=False) as client:
                    for dependency in config.dependencies:
                        url = dependency.url + dependency.path.replace("{tenantID}", tenant_id)
                        async with asyncio.timeout(dependency_timeout):
                            response = await client.get(url, headers={"X-Request-ID": request.state.request_id})
                        if response.status_code != 200:
                            try:
                                root = Failure.model_validate(response.json()).root_cause
                            except (ValueError, TypeError):
                                root = Cause(service=dependency.name, owner=dependency.owner, code="upstream_error")
                            return failure(request, 502, "dependency_failed", dependency=dependency, root=root)
                        checked.append(dependency.name)
        except (httpx.HTTPError, TimeoutError):
            assert dependency is not None
            return failure(request, 502, "dependency_unavailable", dependency=dependency,
                           root=Cause(service=dependency.name, owner=dependency.owner, code="unreachable_or_timeout"))
        if config.name == "subscription-service" and tenant_id == "tenant-suspended":
            return failure(request, 409, "subscription_suspended")
        return Success[config.result_model](service=config.name, owner=config.owner,
                    request_id=request.state.request_id, tenant_id=tenant_id,
                    checked_dependencies=checked, result=config.result(tenant_id), simulation=True)

    if config.method == "POST":
        async def endpoint(payload: ActivationRequest, request: Request, x_request_id: RequestIDHeader = None):
            return await perform(request, payload.tenant_id)
    else:
        async def endpoint(tenantID: TenantID, request: Request, x_request_id: RequestIDHeader = None):
            return await perform(request, tenantID)

    errors = {400: {"model": Failure}, 502: {"model": Failure}}
    local_status = {"tenant-service": 404, "subscription-service": 409, "policy-service": 503}.get(config.name)
    if local_status:
        errors[local_status] = {"model": Failure}
    app.add_api_route(config.route, endpoint, methods=[config.method], response_model=Success[config.result_model],
                      responses=errors, operation_id=config.name.replace("-", "") + "Lookup",
                      summary=config.title + " preview")
    default_openapi = app.openapi

    def documented_openapi():
        document = default_openapi()
        for item in document["paths"].values():
            for operation in item.values():
                # Validation is deliberately translated into the existing HTTP 400 error envelope.
                operation["responses"].pop("422", None)
                for response in operation["responses"].values():
                    response["headers"] = {"X-Request-ID": {"schema": {"type": "string"}, "description": "Correlation ID forwarded across service boundaries"}}
        # FastAPI adds these for its default validation handler, which is replaced above.
        schemas = document.get("components", {}).get("schemas", {})
        schemas.pop("HTTPValidationError", None)
        schemas.pop("ValidationError", None)
        return document

    app.openapi = documented_openapi
    return app
