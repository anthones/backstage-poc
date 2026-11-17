# QA and release — Customer Portal

Owner: Customer Experience. Direct API providers: Customer Activation and Subscription Entitlements.

| Scenario | Browser evidence |
| --- | --- |
| `tenant-acme`, subscription | Active subscription; HTTP 200 in evidence |
| `tenant-acme`, activation | Workspace ready for activation; HTTP 200; `simulation=true` |
| Suspended customer | Subscription unsuccessful / activation blocked; Commerce root cause |
| Unknown customer | Customer not found; Identity root cause |
| Policy fault enabled | Subscription still succeeds; activation fails with Cloud Security root cause |
| Policy fault cleared | New activation request succeeds; no browser or consumer restart |
| Customer selection changes | Previous result is cleared; an earlier in-flight response cannot replace the new selection |

Attach the frontend version, API compatibility evidence, customer/action, request IDs, expected results, consumer acknowledgement, known gaps, deployment order, and concrete rollback artifact to the release record. The fictional Jira example links this website to work; it is not evidence of a real release or approval.
