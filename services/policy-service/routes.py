"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    decision: Literal["allow"]
    policy_version: str
    controls: list[str]


def make_result(tenant_id: str) -> Result:
    return Result(decision="allow", policy_version="2026-11", controls=["encryption", "eu-residency"])


CONFIG = ServiceConfig(
    name="policy-service",
    title="Security Policy",
    owner="cloud-security",
    port=8083,
    method="GET",
    route="/v1/policies/{tenantID}",
    dependencies=(
        Dependency("tenant-service", "identity", 8081, "/v1/tenants/{tenantID}"),
    ),
    result_model=Result,
    result=make_result,
)
