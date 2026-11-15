# [Backstage](https://backstage.io)

This app hosts the AcmeSecure service catalog POC. Start with the [workspace README](../README.md) to prepare the six sibling Python/FastAPI services, catalog, and local TechDocs.

To start the integration workspace from the parent directory:

```sh
./scripts/setup.sh
./scripts/start.sh
```

Open http://localhost:3000/ for the default catalog or `/demo` for the engineering handbook. Each service is a separate repository location. Starting only Backstage does not start the service repositories or build documentation. Local catalog paths resolve from `packages/backend`; `app-config.scm.example.yaml` shows internal GitLab registrations for a real deployment.

Each service owns its TechDocs source and generated `site/` artifact. `.techdocs/` here contains only published copies used by the Backstage server. The activation handbook is part of onboarding-service, not a separate documentation entity.
