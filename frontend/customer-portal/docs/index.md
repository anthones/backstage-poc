# Customer Portal

Customer Experience owns this customer-facing website at [localhost:8080](http://localhost:8080). It runs separately from Backstage, which is the internal portal used to discover and support it.

The browser uses the website's same-origin API bridge. **Check subscription** calls Commerce's `GET /v1/subscriptions/{tenantID}`. **Preview activation** calls Customer Activation's `POST /v1/activations`, which checks all five of its providers. The frontend has two direct dependencies and further indirect dependencies; it does not call Policy directly.

The bridge forwards upstream status and error evidence and generates a request ID that follows the downstream calls. **Support evidence** exposes that response for this demonstration. A real customer UI would expose only the appropriate customer-safe reference and message.

These requests are seeded previews. No workspace is created, no email is sent, and no customer data is changed. The website cannot inject or clear the Policy fault; the presenter uses the workspace's explicit demo controls.

[Runbook](runbook.md) · [QA handover](qa.md) · [Catalog](http://localhost:3000/catalog/default/component/customer-portal)
