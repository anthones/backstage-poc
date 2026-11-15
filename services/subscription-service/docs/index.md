# Subscription Entitlements

**Accountable team: Commerce · Port: 8082 · Lifecycle: experimental POC**

Owns active or suspended commercial entitlement. A valid tenant is not necessarily entitled to a workspace.

## Why this boundary matters

Support often called a valid tenant “active” even when Commerce had suspended its subscription.

The catalog owner is accountable for this service and its contract. The [activation journey](http://localhost:3000/catalog/default/system/customer-activation) has a separate end-to-end owner: Customer Experience.

## Checked interface

This table is checked against `routes.py` by `python -m pytest`. Change it in the same commit as the implementation and metadata.

| Field | Value |
| --- | --- |
| Service | `subscription-service` |
| Owner | `commerce` |
| HTTP endpoint | `GET /v1/subscriptions/{tenantID}` |
| Port | `8082` |
| Dependencies | `tenant-service` |
| Result fields | `entitlement, plan, workspace_limit` |

## Contract

`GET /v1/subscriptions/{tenantID}`

Fixture: `tenant-acme` (valid); `tenant-suspended` (identity exists but Commerce rejects entitlement).

Every response includes `X-Request-ID`; success includes `checked_dependencies`. Failure includes the original `root_cause.service`, `root_cause.owner`, and `root_cause.code`. View the full OpenAPI contract on the entity's **API** tab.

## Runtime dependencies

| Service | Accountable team | Read contract |
| --- | --- | --- |
| [tenant-service](http://localhost:3000/catalog/default/component/tenant-service) | Identity | `/v1/tenants/{tenantID}` |

**Consumers:** inspect incoming catalog dependency relations. Consumer repositories declare those relations; this repository does not maintain a second caller inventory.

These are real synchronous calls made by this POC. No queue, database, email delivery, or durable provisioning is implied. Readiness covers only the local process; activation is the end-to-end probe.

## Handover without a meeting

- [L1 / L2 runbook](runbook.md): symptoms, evidence, next owner, recovery.
- [QA and release](qa.md): fixtures, acceptance criteria, impact, rollback.
- [Service ownership directory](http://localhost:3000/docs/default/component/onboarding-service/handbook/ownership): find the authoritative repository and escalation procedure.

Example people and `.example` contacts are fictional. Use actual internal routing before a real deployment.
