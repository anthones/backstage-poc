# L1 / L2 runbook — Customer Portal

## L1: capture the customer symptom

1. Record the selected customer, action, UTC time, and support reference from **Support evidence**. The demo customers are `tenant-acme`, `tenant-suspended`, and `tenant-missing`.
2. Open the website's catalog entry, owner, and dependencies. Customer Experience owns this website and coordinates activation incidents.
3. Attach the JSON response and its `request_id`. Follow `root_cause.owner` when the response identifies a provider failure. If no response exists, start with Customer Experience.
4. A suspended subscription belongs to Commerce; an unknown customer belongs to Identity. An activation failure with `policy_unavailable` goes to Cloud Security, with Customer Experience coordinating the journey.

## L2: isolate the boundary

Check `http://localhost:8080/healthz`, the browser request, and `.run/customer-portal.log`. Follow the same request ID into the named backend logs. Subscription success does not prove activation works: activation also needs Policy, Provisioning, Tenant, and Notifications.

For the deliberate local Policy fault only, the presenter runs `./scripts/demo.sh recover` from the workspace root. Repeat **Preview activation** for the original customer. The frontend's last displayed result is a snapshot and changes only after a new request.

Customer Experience confirms the whole journey works before closing the incident. A real recovery must use the affected team's approved procedure.
