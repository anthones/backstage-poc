# QA and change handover

## A concrete change: Policy adds a required control

Cloud Security changes `controls` semantics. Workspace Provisioning and Customer Activation consume the policy API directly. Provisioning also consumes Commerce entitlement; QA must prove that neither prerequisite is bypassed. Customer Experience coordinates the journey regression.

1. Open Policy's API contract and its catalog **Relations** graph. Identify direct consumers before making the change.
2. Provider owner supplies the version/commit, changed fields and semantics, fixture outcomes, dependency assumptions, and rollback artifact.
3. QA uses [Provisioning's handover](http://localhost:3000/docs/default/component/provisioning-service/qa) to reproduce successful, suspended, missing-tenant, outage, and recovery outcomes.
4. For a breaking schema or semantic change, version the API and capture acknowledgement from each direct consumer. A graph reveals consumers; it does not itself enforce approval or notify people.
5. Update implementation, OpenAPI, catalog relations, runbook, and acceptance notes together. Rebuild TechDocs. Release compatible providers before consumers.

## Shared regression matrix

| Case | Tenant | Subscription | Policy | Provisioning | Notifications | Activation |
| --- | --- | --- | --- | --- | --- | --- |
| `tenant-acme` | 200 | 200 | 200 | 200 | 200 | 200 |
| `tenant-suspended` | 200 | 409 | 200 | 502 / Commerce | 200 | 502 / Commerce |
| `tenant-missing` | 404 | 502 / Identity | 502 / Identity | 502 / Identity | 502 / Identity | 502 / Identity |
| Policy outage, `tenant-acme` | 200 | 200 | 503 | 502 / Cloud Security | 200 | 502 / Cloud Security |
| Recovery, `tenant-acme` | 200 | 200 | 200 | 200 | 200 | 200 |

`.venv/bin/python scripts/verify.py` checks this matrix, correlation IDs, health versus readiness, malformed input, contract existence, and agreement between runtime and catalog dependencies. Python tests exercise the HTTP failure mechanics and timeouts. Run verification against an isolated local POC because it toggles the policy fault.

## Release record template

- Provider / owner / version / immutable artifact:
- Changed contract and reason:
- Direct consumers and acknowledgement evidence:
- QA fixture results and request IDs:
- Deployment sequence and dependency assumptions:
- Concrete rollback artifact / command / verification:
- Known limitations and owner of remaining work:

## Why this is useful

QA receives an executable scenario and expected evidence rather than a verbal handoff. Provider teams can see who will be affected. Support inherits the same vocabulary and failure contract. Each repository now runs a CI gate for code/catalog/API/interface-summary consistency before building its documentation artifact. Teams still review narrative accuracy and record consumer acknowledgement. See [repository checks](repositories.md) for the exact scope.
