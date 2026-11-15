"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    name: str
    contact: str
    identity_status: Literal["verified"]


def make_result(tenant_id: str) -> Result:
    return Result(name="Acme Manufacturing", contact="ops@acme.example", identity_status="verified")


CONFIG = ServiceConfig(
    name="tenant-service",
    title="Tenant Directory",
    owner="identity",
    port=8081,
    method="GET",
    route="/v1/tenants/{tenantID}",
    dependencies=(
    ),
    result_model=Result,
    result=make_result,
)
