"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    plan: str
    entitlement: Literal["active"]
    workspace_limit: int


def make_result(tenant_id: str) -> Result:
    return Result(plan="enterprise", entitlement="active", workspace_limit=3)


CONFIG = ServiceConfig(
    name="subscription-service",
    title="Subscription Entitlements",
    owner="commerce",
    port=8082,
    method="GET",
    route="/v1/subscriptions/{tenantID}",
    dependencies=(
        Dependency("tenant-service", "identity", 8081, "/v1/tenants/{tenantID}"),
    ),
    result_model=Result,
    result=make_result,
)
