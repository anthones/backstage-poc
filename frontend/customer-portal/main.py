"""Customer-facing preview and same-origin API bridge; Backstage is separate."""
import os
from pathlib import Path
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
import httpx
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent


class Activation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(pattern=r"^[a-zA-Z0-9-]{1,64}$")


def create_app(transport=None):
    app = FastAPI(docs_url=None, redoc_url=None)

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "static/index.html")

    @app.get("/healthz")
    async def health():
        return {"status": "alive", "component": "customer-portal"}

    async def forward(request, service, port, path, body=None):
        base = os.environ.get(service.upper().replace("-", "_") + "_URL", f"http://127.0.0.1:{port}")
        # One ID follows the browser request through the downstream service calls.
        request_id = uuid.uuid4().hex
        try:
            async with httpx.AsyncClient(transport=transport, timeout=6, trust_env=False) as client:
                result = await client.request("POST" if body is not None else "GET", base.rstrip("/") + path,
                                              json=body, headers={"X-Request-ID": request_id})
                content = result.json()
                status = result.status_code
        except (httpx.HTTPError, ValueError):
            status = 502
            content = {"error": "dependency_unavailable", "request_id": request_id,
                       "root_cause": {"service": service,
                                      "owner": "customer-experience" if service == "onboarding-service" else "commerce",
                                      "code": "unreachable_or_timeout"}}
        return JSONResponse(content, status_code=status, headers={"X-Request-ID": request_id})

    @app.get("/api/subscription")
    async def subscription(request: Request, tenant: str = Query(pattern=r"^[a-zA-Z0-9-]{1,64}$")):
        return await forward(request, "subscription-service", 8082, f"/v1/subscriptions/{tenant}")

    @app.post("/api/activation")
    async def activation(payload: Activation, request: Request):
        return await forward(request, "onboarding-service", 8086, "/v1/activations", payload.model_dump())

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("LISTEN_ADDR", "127.0.0.1"), port=int(os.environ.get("PORT", "8080")))
