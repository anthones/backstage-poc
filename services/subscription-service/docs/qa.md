# QA and release handover — Subscription Entitlements

**Provider sign-off: Commerce · Journey acceptance: Customer Experience / QA**

## Repeatable acceptance

| Fixture / scenario | Expected evidence |
| --- | --- |
| `tenant-acme` | `GET /v1/subscriptions/{tenantID}` → HTTP 200; service `subscription-service`; owner `commerce`; `simulation=true` |
| `tenant-suspended` | Tenant directory HTTP 200; subscription HTTP 409; subscription consumers HTTP 502 with Commerce root cause |
| `tenant-missing` | Tenant directory HTTP 404; transitive consumers HTTP 502 with Identity root cause |
| Invalid tenant ID / missing POST body | HTTP 400; no dependency calls |
| Policy outage | Policy HTTP 503; policy consumers HTTP 502 preserving Cloud Security root cause; Tenant, Subscription, and Notification still answer |
| Recovery | Reset fault, rerun happy path; HTTP 200; no restart of unaffected services |
| Request correlation | Pass `X-Request-ID: qa-release-001`; the same ID appears in responses and downstream logs |

Run in this repository first:

```sh
./ci/check.sh
```

The optional cross-service exercise requires the complete POC running. From the POC workspace root:

```sh
./scripts/demo.sh happy
./scripts/demo.sh suspended
./scripts/demo.sh missing
./scripts/demo.sh outage
./scripts/demo.sh recover
.venv/bin/python scripts/verify.py
```

`verify.py` checks all six service contracts, compares runtime `/info` dependencies with catalog declarations, and exercises failure, recovery, and invalid input. The Python tests separately cover timeout semantics. It restores the policy fault in a `finally` block. Run it against a dedicated local POC, since it deliberately changes the demo fault flag.

## Change impact and release gate

- Obtain the current consumer list from incoming catalog relations. Those declarations are maintained in consumer repositories; include the list and acknowledgement evidence in this release record.
- Confirm the API schema and these expected outcomes before handover. For field removal or semantic changes, version the contract and obtain acknowledgement from each direct consumer listed in the catalog. QA follows the graph for transitive regression coverage.
- Owner attaches: version/commit, changed contract fields, fixture outcomes, dependency assumptions, rollback command, and known limitations. QA records acceptance evidence; a verbal “ready for QA” is insufficient.
- Schema change: update `routes.py`, catalog relations, and docs together. Explicitly generate and review `openapi.yaml` and the embedded API with `python tools/sync-api.py` when the API changes, then `./ci/check.sh`. Build TechDocs through `ci/build-docs.sh` in this repository.
- Deploy providers compatibly before consumers. For rollback in this POC, rebuild and restart the previous service version, then rerun the journey; there are no migrations or persistent writes. In production, the release record must specify a concrete approved artifact and rollback procedure.

## Known limits

Seeded fixtures, synchronous reads, no authentication, no durable activation state, no email delivery, no real entitlement or policy engine. “Ready to provision” is a preview, not a provisioned workspace. The catalog makes existing ownership and dependencies discoverable; teams still need to agree on boundary decisions and keep metadata reviewed.
