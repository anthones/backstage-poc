"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    workspace: str
    region: str
    readiness: Literal["ready-to-provision"]


def make_result(tenant_id: str) -> Result:
    return Result(workspace="ws-" + tenant_id, region="eu-onprem-1", readiness="ready-to-provision")


CONFIG = ServiceConfig(
    name="provisioning-service",
    title="Workspace Provisioning",
    owner="cloud-security",
    port=8084,
    method="GET",
    route="/v1/workspaces/{tenantID}",
    dependencies=(
        Dependency("policy-service", "cloud-security", 8083, "/v1/policies/{tenantID}"),
        Dependency("subscription-service", "commerce", 8082, "/v1/subscriptions/{tenantID}"),
    ),
    result_model=Result,
    result=make_result,
)
