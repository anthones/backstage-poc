"""Domain-owned runtime configuration and typed result; CI checks the committed metadata."""
from typing import Literal

from service import Dependency, ServiceConfig, StrictModel


class Result(StrictModel):
    activation: Literal["ready"]
    message: str


def make_result(tenant_id: str) -> Result:
    return Result(activation="ready", message="All domain checks passed; workspace and welcome notice previewed")


CONFIG = ServiceConfig(
    name="onboarding-service",
    title="Customer Activation",
    owner="customer-experience",
    port=8086,
    method="POST",
    route="/v1/activations",
    dependencies=(
        Dependency("tenant-service", "identity", 8081, "/v1/tenants/{tenantID}"),
        Dependency("subscription-service", "commerce", 8082, "/v1/subscriptions/{tenantID}"),
        Dependency("policy-service", "cloud-security", 8083, "/v1/policies/{tenantID}"),
        Dependency("provisioning-service", "cloud-security", 8084, "/v1/workspaces/{tenantID}"),
        Dependency("notification-service", "customer-experience", 8085, "/v1/notices/{tenantID}"),
    ),
    result_model=Result,
    result=make_result,
)
