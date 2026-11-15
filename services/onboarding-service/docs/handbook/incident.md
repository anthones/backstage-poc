# Incident exercise: activation fails, Identity is healthy

## Prepare

Start the demo with `./scripts/start.sh`. Open the [engineering handbook](http://localhost:3000/demo) and a terminal in the workspace root. Commands perform read-only business previews. The policy fault flag is mutable demonstration state only.

## Healthy journey

```sh
./scripts/demo.sh happy
```

Expected HTTP 200, `result.activation=ready`, `simulation=true`, and all five direct dependencies in `checked_dependencies`.

## Inject the policy outage

```sh
./scripts/demo.sh outage
```

The command prints a valid HTTP 502 response and exits nonzero, because curl treats the deliberate outage as a failed request. Expected evidence:

```json
{
  "error": "dependency_failed",
  "request_id": "demo-outage",
  "failed_dependency": "policy-service",
  "root_cause": {
    "service": "policy-service",
    "owner": "cloud-security",
    "code": "policy_unavailable"
  }
}
```

1. Open Customer Activation in the catalog. It is owned by Customer Experience, which coordinates this incident.
2. Follow the graph to Policy. Policy also blocks Workspace Provisioning. The graph shows impact; it does not claim to be a live health dashboard.
3. Open the [Policy runbook](http://localhost:3000/docs/default/component/policy-service/runbook). L1 has a concrete next action and accountable domain, without asking every team what “not ready” means.
4. Verify that Tenant, Subscription, and Notifications still answer their documented lookup endpoints. Policy `/healthz` returns 200 while `/readyz` and its business endpoint return 503. This distinguishes process liveness from local readiness and journey success.
5. Find `demo-outage` in `.run/*.log` to correlate the observed request. These are request logs, not a distributed tracing backend.

## Recover and close

```sh
./scripts/demo.sh recover
.venv/bin/python scripts/verify.py
```

Recovery clears the fault and proves activation succeeds. Verification runs additional acceptance cases and restores the fault flag afterward. No consumer restart is needed.

## A second failure with a different owner

```sh
./scripts/demo.sh suspended
```

The directory knows `tenant-suspended`, but the subscription service returns HTTP 409 with `subscription_suspended`. Activation returns HTTP 502 preserving `root_cause.owner=commerce`. The same journey symptom has a different accountable domain, discoverable from evidence.

## What changed in the handover

Before: “Activation is down; can your team check?” sent repeatedly across silos. With the catalog and error contract: tenant, request ID, root cause, affected consumers, and a service-specific recovery procedure arrive together. Teams still collaborate on novel incidents; routine fact-finding is available as shared documentation.
