# Read-only Jira adapter

The workspace runner starts this loopback service on port 8090. To run it separately, use `.venv/bin/python integrations/jira/main.py` from the workspace root. It uses the shared FastAPI, httpx, and PyYAML dependencies already installed by setup.

`GET /issues?source=public` requests five live public issues from Atlassian. `GET /issues?source=scenario&component=customer-portal` returns explicitly fictional work selected by the component's catalog annotations. `GET /components` lists the mapped example components. No private Jira credentials, ticket writes, or silent fixture fallback are supported.

The authenticated Backstage proxy provides the UI route. See [Jira and delivery](../../services/onboarding-service/docs/handbook/jira.md) for the presentation and company connection requirements. Behavior checks: `.venv/bin/python -m pytest scripts/test_demo_extensions.py -q`.
