# Incident exercise: activation fails, Identity is healthy


## What the three commands demonstrate

They are a controlled support rehearsal. The customer website on port 8080 makes the same activation request through its own API bridge. The commands give the presenter repeatable controls and readable responses.

| Command | What it changes | What it requests | Why we use it |
| --- | --- | --- | --- |
| `happy` | Nothing; it does not reset the fault | Activation for `tenant-acme` | Establish a successful baseline when Policy is available. If an earlier fault is still enabled, it will fail. |
| `outage` | Enables the demo-only Policy fault | The same activation | Produce a known customer symptom and error evidence, then use Backstage to find the owner and runbook. |
| `recover` | Disables the demo-only Policy fault | The same activation | Reset the exercise and prove the full request succeeds again. |

Before a presentation, use **recover** to ensure a clean starting state. During the talk, show **happy → outage → recover**, and repeat the website preview after each change. The website's displayed result is the last response, not a live monitor.

### What the audience should learn

A customer-visible failure may come from a service several steps away from the frontend. Evidence identifies the failing boundary; the catalog identifies responsibility and declared relationships; the runbook provides the next action; a fresh customer request checks recovery. Passing that evidence between L1, L2, and the journey coordinator is the handover being demonstrated.

**Backstage does not inject, detect, or repair this outage.** The service code propagates the error and request ID; the demo control sets and clears the fault. This exercise does not demonstrate automated discovery, paging, production remediation, or measured productivity gains. Those need their own integrations and validation.

If presenting all three commands feels repetitive, use `recover` only during preparation, show the successful website request as the baseline, then use `outage` and `recover` as presenter controls. Explain each action before running it.

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
