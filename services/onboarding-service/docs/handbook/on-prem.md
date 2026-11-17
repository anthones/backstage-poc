# Path to a self-managed, on-premises pilot

## Demonstrated here

- Six independent service repository locations and one frontend location, periodically read from local checkouts.
- Repository-local CI verification and documentation artifacts, with no required GitHub token.
- Team, user, domain, system, component, and API entities.
- Runtime dependency relationships and discoverable OpenAPI definitions.
- Prebuilt TechDocs served from local disk, plus catalog and documentation search.
- Guest access for the local demonstration; six backend services, the customer website, and the Jira adapter on loopback.
- Optional containers for the six services and frontend through `docker compose up --build`.
- A read-only connection to Atlassian's public Jira tracker, plus an explicitly fictional service-linked work scenario.

No cloud account, external telemetry, CDN, or external service is required for the POC journey. Initial package installation and container image builds require dependency access unless you supply internal mirrors and preloaded artifacts. The existing Backstage production config is a scaffold and is not a ready deployment of this sibling workspace layout.

The optional live public Jira view requires outbound HTTPS to `jira.atlassian.com`. The fictional handover example works locally. Neither mode connects to private company Jira.

## Work needed for the company's environment

| Area | Pilot implementation decision |
| --- | --- |
| Identity | Replace Guest with the company's identity provider; map authenticated users to catalog groups |
| Authorization | Replace the scaffold allow-all policy with roles appropriate to internal catalog, docs, and actions |
| Persistence | Use the company's PostgreSQL service and persistent TechDocs storage; back up both |
| Source and metadata | Publish each self-contained service directory as an internal repository and adapt `backstage/app-config.scm.example.yaml`; keep metadata and docs in the owning repository |
| Documentation | Use each repository's supplied CI pipeline and publish its `site/` artifact to persistent TechDocs storage after verification passes |
| Networking | Internal DNS, TLS, reverse proxy, trusted ingress, and approved network routes |
| Jira | Agree instance, authentication, issue-to-service mapping, and who may view returned work; replace the public-only adapter before using private records |
| Packaging | Package the catalog sources and documentation with deployment artifacts or use internal SCM; the scaffold Dockerfile alone does not include sibling directories |
| Supply chain | Mirror approved Python environments, Node packages, Python packages, and base images; pin and review build artifacts |
| Operations | Health monitoring, logs, backups, restore rehearsal, secret rotation, resource sizing, upgrade process |
| Demo controls | Remove the policy fault route and replace seeded fixtures with actual domain integrations |

## Keep the pilot small

Start with a cross-domain customer journey, not an inventory migration of the whole company. Confirm each boundary with the team that owns it, replace fictional contacts with actual routes, and measure whether shared catalog information reduces repeated discovery. Extend only when owners can maintain the information and consumers find it useful.

## References used for the POC

The local documentation publisher follows [Backstage TechDocs configuration](https://backstage.io/docs/features/techdocs/configuration/). The presentation page uses the installed frontend APIs described by [Backstage frontend modules](https://backstage.io/docs/frontend-system/architecture/extension-overrides/). Services use [FastAPI](https://fastapi.tiangolo.com/) with typed response models and committed OpenAPI snapshots. Runtime, tests, automation, and TechDocs share the Python toolchain.
