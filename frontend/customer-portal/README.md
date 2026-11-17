# Customer Portal

Customer-facing UI on port 8080, separate from Backstage. Start with the workspace runner, or install `requirements.txt` in a Python environment and run `python main.py`. Configure `ONBOARDING_SERVICE_URL` and `SUBSCRIPTION_SERVICE_URL` when the services are not on loopback ports 8086 and 8082.

The browser calls the same-origin bridge, which calls the two APIs and preserves failure evidence. Catalog metadata declares both dependencies. [Documentation](docs/index.md) includes support and QA instructions.

TechDocs builds with the workspace environment: from this folder, run `../../.venv/bin/python -m mkdocs build --strict`. The workspace builder and publisher include this site.
