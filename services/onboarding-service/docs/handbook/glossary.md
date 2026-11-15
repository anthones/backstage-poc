# Customer activation

A customer becomes able to use an AcmeSecure workspace when its tenant, subscription, policy, and workspace agree that access is permitted.

## Language

**Tenant**: A customer organization and its stable identity. Identity owns its name and contact details.
_Avoid_: Account, workspace, subscription

**Subscription**: The commercial entitlement of a tenant to a plan. Commerce owns whether it is active or suspended.
_Avoid_: Tenant status, policy

**Policy**: A decision about the security controls required for a tenant's workspace. Cloud Security owns the decision.
_Avoid_: Commercial entitlement, plan

**Workspace**: The protected execution environment allocated to a tenant. Cloud Security owns its placement and readiness.
_Avoid_: Tenant, account

**Activation**: The coordinated decision that a tenant is eligible for a workspace and a welcome notice. Customer Experience owns the journey, while the constituent decisions retain their domain owners.
_Avoid_: Provisioning, signup

**Welcome notice**: A customer-facing explanation that activation is ready. Customer Experience owns its content and routing; Identity owns the recipient contact.
_Avoid_: Activation, provisioning
