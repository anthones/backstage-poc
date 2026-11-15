"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    template: str
    delivery: Literal["preview-only"]
    recipient_source: Literal["tenant-service"]


def make_result(tenant_id: str) -> Result:
    return Result(template="workspace-ready-v1", delivery="preview-only", recipient_source="tenant-service")


CONFIG = ServiceConfig(
    name="notification-service",
    title="Customer Notifications",
    owner="customer-experience",
    port=8085,
    method="GET",
    route="/v1/notices/{tenantID}",
    dependencies=(
        Dependency("tenant-service", "identity", 8081, "/v1/tenants/{tenantID}"),
    ),
    result_model=Result,
    result=make_result,
)
