# Support routing and ownership directory

Customer Experience coordinates the cross-domain activation journey. Each provider's catalog owner retains responsibility for that provider's decisions, operating instructions, and API contract.

## Authoritative service documentation

| Repository | Boundary and interface | Support | QA handover |
| --- | --- | --- | --- |
| Tenant | [Service docs](http://localhost:3000/docs/default/component/tenant-service) | [Runbook](http://localhost:3000/docs/default/component/tenant-service/runbook) | [QA](http://localhost:3000/docs/default/component/tenant-service/qa) |
| Subscription | [Service docs](http://localhost:3000/docs/default/component/subscription-service) | [Runbook](http://localhost:3000/docs/default/component/subscription-service/runbook) | [QA](http://localhost:3000/docs/default/component/subscription-service/qa) |
| Policy | [Service docs](http://localhost:3000/docs/default/component/policy-service) | [Runbook](http://localhost:3000/docs/default/component/policy-service/runbook) | [QA](http://localhost:3000/docs/default/component/policy-service/qa) |
| Provisioning | [Service docs](http://localhost:3000/docs/default/component/provisioning-service) | [Runbook](http://localhost:3000/docs/default/component/provisioning-service/runbook) | [QA](http://localhost:3000/docs/default/component/provisioning-service/qa) |
| Notifications | [Service docs](http://localhost:3000/docs/default/component/notification-service) | [Runbook](http://localhost:3000/docs/default/component/notification-service/runbook) | [QA](http://localhost:3000/docs/default/component/notification-service/qa) |
| Activation | [Service docs](http://localhost:3000/docs/default/component/onboarding-service) | [Runbook](http://localhost:3000/docs/default/component/onboarding-service/runbook) | [QA](http://localhost:3000/docs/default/component/onboarding-service/qa) |
| Customer Portal frontend | [Website docs](http://localhost:3000/docs/default/component/customer-portal) | [Runbook](http://localhost:3000/docs/default/component/customer-portal/runbook) | [QA](http://localhost:3000/docs/default/component/customer-portal/qa) |

Boundaries and service-level instructions are maintained in those repositories. This directory links to them rather than keeping a second copy.

## Cross-domain escalation agreement

1. L1 records tenant ID, request ID, UTC time, response status, root cause, and last relevant release.
2. The named `root_cause.owner` receives that evidence. For an unreachable process with no response, use the service's catalog owner.
3. The journey owner coordinates customer updates and end-to-end verification. The provider domain owns its diagnosis and repair.
4. If ownership or contract semantics are disputed, affected leads resolve the issue and update the owning repositories in the same change.

Organizational users and `.example` contacts are fictional. Replace them with actual support routes and on-call details before a real pilot.

## Maintenance

Each repository's CI checks code, catalog, API, and the documented interface summary. The owner still reviews narrative support and QA instructions. See [repository ingestion and CI checks](repositories.md) for the executable procedure and its limits.
