# Customer Activation

**Accountable team: Customer Experience · Port: 8086 · Lifecycle: experimental POC**

Owns activation coordination and customer-visible outcome. Delegates identity, entitlement, policy, workspace, and notice decisions.

## Why this boundary matters

One customer journey crosses four teams and five direct dependencies. The coordinating team cannot fix every failure.

The catalog owner is accountable for this service and its contract. The [activation journey](http://localhost:3000/catalog/default/system/customer-activation) has a separate end-to-end owner: Customer Experience.

## Checked interface

This table is checked against `routes.py` by `python -m pytest`. Change it in the same commit as the implementation and metadata.

| Field | Value |
| --- | --- |
| Service | `onboarding-service` |
| Owner | `customer-experience` |
| HTTP endpoint | `POST /v1/activations` |
| Port | `8086` |
| Dependencies | `tenant-service, subscription-service, policy-service, provisioning-service, notification-service` |
| Result fields | `activation, message` |

## Contract

`POST /v1/activations`

Body: `{"tenant_id": "tenant-acme"}`

Every response includes `X-Request-ID`; success includes `checked_dependencies`. Failure includes the original `root_cause.service`, `root_cause.owner`, and `root_cause.code`. View the full OpenAPI contract on the entity's **API** tab.

## Runtime dependencies

| Service | Accountable team | Read contract |
| --- | --- | --- |
| [tenant-service](http://localhost:3000/catalog/default/component/tenant-service) | Identity | `/v1/tenants/{tenantID}` |
| [subscription-service](http://localhost:3000/catalog/default/component/subscription-service) | Commerce | `/v1/subscriptions/{tenantID}` |
| [policy-service](http://localhost:3000/catalog/default/component/policy-service) | Cloud Security | `/v1/policies/{tenantID}` |
| [provisioning-service](http://localhost:3000/catalog/default/component/provisioning-service) | Cloud Security | `/v1/workspaces/{tenantID}` |
| [notification-service](http://localhost:3000/catalog/default/component/notification-service) | Customer Experience | `/v1/notices/{tenantID}` |

**Consumers:** inspect incoming catalog dependency relations. Consumer repositories declare those relations; this repository does not maintain a second caller inventory.

These are real synchronous calls made by this POC. No queue, database, email delivery, or durable provisioning is implied. Readiness covers only the local process; activation is the end-to-end probe.

## Handover without a meeting

- [L1 / L2 runbook](runbook.md): symptoms, evidence, next owner, recovery.
- [QA and release](qa.md): fixtures, acceptance criteria, impact, rollback.
- [Service ownership directory](http://localhost:3000/docs/default/component/onboarding-service/handbook/ownership): find the authoritative repository and escalation procedure.

Example people and `.example` contacts are fictional. Use actual internal routing before a real deployment.
