# L1 / L2 runbook — Customer Activation

## L1: first five minutes

1. Record the customer tenant ID, symptom, UTC time, and `X-Request-ID`. Use `tenant-acme` for this demonstration. Do not paste customer secrets in an incident.
2. Check `curl -i http://localhost:8086/healthz` and `/readyz`. A healthy process does not prove that its dependencies are healthy.
3. Reproduce the read-only preview:

```sh
curl -sS -X POST http://localhost:8086/v1/activations -H 'Content-Type: application/json' -d '{"tenant_id":"tenant-acme"}'
```

4. A dependency failure is HTTP **502**. Read `root_cause` rather than guessing from the service at the top of the customer journey. Attach the response and matching request ID logs.
5. Route the evidence to **`root_cause.owner`**. If this service itself is unreachable, route to **Customer Experience**. Customer Experience keeps the customer incident coordinated; the receiving domain owns its repair.

## Symptom → action

| Evidence | Meaning | Next action |
| --- | --- | --- |
| `/healthz` unreachable | Process or local port issue | Customer Experience checks the service process logs (workspace harness: `.run/onboarding-service.log`); verify process / Compose status |
| HTTP 400 | Malformed request or missing tenant | Fix input from the API contract; no escalation needed |
| `tenant_not_found` | ID absent from seeded directory | Identity validates the tenant ID; do not create a second tenant as a workaround |
| `subscription_suspended` | Identity exists; entitlement is blocked | Commerce decides reinstatement; do not bypass policy or provision manually |
| `policy_unavailable` | Deliberate outage in the demo | Cloud Security follows the recovery below |
| `unreachable_or_timeout` | Named dependency cannot answer in time | Named dependency owner checks its process; do not restart every consumer |

## L2: isolate the failing boundary

- Owner: **Customer Experience**. Scope: Owns activation coordination and customer-visible outcome. Delegates identity, entitlement, policy, workspace, and notice decisions.
- Direct dependencies: **tenant-service, subscription-service, policy-service, provisioning-service, notification-service**. Query the failing dependency directly with the same tenant and `X-Request-ID`.
- Before changing a contract, inspect incoming catalog dependency relations and attach the current consumer list to the release. Those declarations belong to the consuming repositories.
- Inspect service stdout with the same request ID (the workspace harness collects it in `.run/*.log`); each service records its name, owner, status, and duration. A dependency timeout is 1.2 seconds; each inbound operation has a 4-second total budget. No automatic retries.
- There is no mutable business state in this POC. Restarting clears only the injected policy fault. Do not infer a production recovery process from these fixtures.

## Demonstration recovery and verification

The following commands belong to the optional multi-repository POC harness, not this service repository. In an independent checkout, use the local endpoint and the owning team's deployment tooling.

The fault is an explicit demonstration control available only when `ENABLE_DEMO_CONTROLS=true` on policy-service. Services bind to loopback in the local runner; Compose publishes loopback ports.

```sh
./scripts/demo.sh recover
./scripts/demo.sh happy
```

Expected: activation HTTP 200, `result.activation=ready`, `simulation=true`. Verify the original affected tenant as well as process readiness. L1 closes only after Customer Experience confirms the journey is restored.

## Escalation handover packet

`tenant_id` · `request_id` · observed UTC time · failing endpoint/status · `root_cause` · health/readiness results · last relevant release. Send one evidence packet to the accountable domain, and keep the journey owner attached. This replaces repeated symptom discovery between teams.
