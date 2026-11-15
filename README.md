# AcmeSecure Backstage integration workspace

Six independent Python/FastAPI service repositories run alongside Backstage. `/` is the default software catalog; `/demo` opens the domain-owned engineering handbook through TechDocs. Services, tests, automation, and TechDocs use one local Python virtual environment. Backstage retains its Node/Yarn toolchain. No Go toolchain is required.

## Start locally

Prerequisites: Python 3.12+, Node 22 or 24, and a shell. Initial setup downloads dependencies; Docker is optional.

```sh
./scripts/setup.sh
./scripts/check-services.sh
./scripts/start.sh
```

Open **http://localhost:3000/** and choose Guest if prompted. Use **http://localhost:3000/demo** for the manual. Keep the runner active; Ctrl-C stops its processes. Logs are `.run/*.log`. Backstage uses ports 3000/7007; the services use 8081–8086.

Setup installs all six repositories' development requirements into `.venv/` and uses Backstage's checked-in Yarn release. Every service also installs and runs independently using its own requirements files.

## Repository ownership

```text
services/<name>/
  main.py                 # Uvicorn process entry point
  routes.py               # owner, route, dependencies, typed fixture result
  service.py              # repository-local FastAPI HTTP implementation
  requirements.txt        # pinned direct runtime dependencies
  requirements-dev.txt    # runtime + tests + TechDocs in the same environment
  catalog-info.yaml       # Component and API entities owned by this repository
  openapi.yaml            # committed snapshot generated from FastAPI
  tests/                  # contract consistency and HTTP behavior tests
  mkdocs.yml / docs/      # team-owned TechDocs sources and navigation
  site/                   # generated documentation artifact, ignored by Git
  Dockerfile / ci/        # standalone container build and CI entry points
  CODEOWNERS              # example domain team ownership
```

| Repository | Port | Source documentation |
| --- | --- | --- |
| [Tenant Directory](services/tenant-service/README.md) | 8081 | [TechDocs](services/tenant-service/docs/index.md) |
| [Subscription Entitlements](services/subscription-service/README.md) | 8082 | [TechDocs](services/subscription-service/docs/index.md) |
| [Security Policy](services/policy-service/README.md) | 8083 | [TechDocs](services/policy-service/docs/index.md) |
| [Workspace Provisioning](services/provisioning-service/README.md) | 8084 | [TechDocs](services/provisioning-service/docs/index.md) |
| [Customer Notifications](services/notification-service/README.md) | 8085 | [TechDocs](services/notification-service/docs/index.md) |
| [Customer Activation](services/onboarding-service/README.md) | 8086 | [TechDocs](services/onboarding-service/docs/index.md) |

The activation handbook, integration procedures, domain vocabulary, architecture SVG, and [Mermaid source](services/onboarding-service/docs/handbook/architecture.mmd) belong to Customer Experience and live under [onboarding-service/docs/handbook/](services/onboarding-service/docs/handbook/index.md). There is no floating documentation site or separate handbook catalog component. `catalog/` contains only organization/system catalog YAML.

## Documentation build and serving

1. Each repository checks its committed metadata and generates its own `site/` artifact through `ci/build-docs.sh`.
2. `scripts/publish-docs.py` copies those artifacts into `backstage/.techdocs/default/component/<name>/`.
3. Backstage serves those published copies. `backstage/.techdocs/` is disposable cache/storage, not authored documentation.

```sh
./scripts/build-docs.sh
```

That command verifies each repository's contract, invokes its own documentation build, and publishes the six artifacts locally. In real CI, each team's pipeline builds and publishes its own artifact to persistent internal TechDocs storage. It does not depend on this workspace's scripts.

## Catalog ingestion

Backstage registers each service's `catalog-info.yaml` as a separate file location and periodically rereads it. The local suggested minimum interval is 15 seconds; processing is asynchronous. [app-config.scm.example.yaml](backstage/app-config.scm.example.yaml) shows equivalent internal GitLab repository URL locations. It is an example and is not loaded locally. This workspace does not create remote repositories.

## Metadata drift and CI

Inside an independent service repository:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
PYTHON="$PWD/.venv/bin/python" ./ci/check.sh
.venv/bin/python main.py
```

`routes.py` and the typed result model generate FastAPI's OpenAPI schema. CI compares that complete schema with the committed `openapi.yaml`, checks its embedded catalog definition, and checks runtime owner/route/port/dependencies against the YAML and documented interface table. An actual in-process HTTP success response is checked against its schema as well.

When changing a contract, update the affected metadata and documentation, explicitly run `.venv/bin/python tools/sync-api.py`, review the generated API/catalog diff, and rerun CI. CI does not repair stale snapshots or prove arbitrary narrative instructions are correct.

From the workspace root:

```sh
./scripts/check-services.sh
.venv/bin/python scripts/verify-repositories.py
```

The second command copies all six repositories into isolated temporary directories and checks each without sibling source files. It also proves that stale route, owner, dependency, response field, documentation, and embedded-API changes are rejected in a disposable Policy checkout. The original repositories are not modified.

## Integration exercise

With the workspace running:

```sh
./scripts/demo.sh happy
./scripts/demo.sh outage
./scripts/demo.sh recover
./scripts/demo.sh suspended
.venv/bin/python scripts/verify.py
.venv/bin/python scripts/verify-backstage.py
.venv/bin/python scripts/verify-catalog-refresh.py
```

Deliberate failure commands print JSON evidence and exit nonzero. Use `recover` afterward. Acceptance checks restore the policy fault before exiting. The refresh check adds and removes a temporary, nonfunctional annotation in Policy's own catalog file and waits for automatic ingestion without restarting Backstage.

These are seeded business previews: no actual tenants, subscriptions, workspaces, or email are created. Example contacts are fictional.

[Repository and CI procedure](services/onboarding-service/docs/handbook/repositories.md) · [Walkthrough](services/onboarding-service/docs/handbook/presentation.md) · [On-premises configuration](services/onboarding-service/docs/handbook/on-prem.md)

## Containers

Each service builds independently with `docker build services/<name>`. `docker compose up --build` runs all six using separate contexts and internal DNS. Do not run Compose alongside the native service runner on the same ports. Backstage starts separately when using Compose. `./scripts/start.sh --services-only` runs the native services without Backstage.
