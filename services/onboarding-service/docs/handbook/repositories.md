# Repository ingestion and CI checks

## Ownership boundary

Each `services/<name>/` directory is an independent Python/FastAPI repository. Code, runtime requirements, typed models, catalog YAML, API snapshot, TechDocs source, runbook, QA handover, Dockerfile, and CI stay inside that boundary. Tests run without sibling source files or running services.

Customer Experience also owns the activation journey's handbook, architecture, Mermaid source, and shared vocabulary. Those sources live in this repository's `docs/handbook/` directory and are included in its `mkdocs.yml`. There is no separate handbook component or floating TechDocs source directory.

## Build and read paths

```text
Team repository
  routes.py + typed Result model + service.py
  catalog-info.yaml + openapi.yaml + docs/
          |
          v
  ci/check.sh: check committed metadata against the FastAPI application
          |
          v
  ci/build-docs.sh: build this repository's site/ artifact
          |
          v
  CI publisher -> internal TechDocs storage

Backstage catalog processor -> this repository's catalog-info.yaml
Backstage TechDocs reader  -> its published documentation artifact
```

The local workspace uses one `.venv/` for service execution, tests, automation, and MkDocs. A standalone repository creates its own environment from `requirements-dev.txt`. Runtime-only containers install `requirements.txt`. Backstage still requires Node/Yarn.

The local app registers six independent file locations representing SCM checkouts and periodically rereads them. Its 15-second suggested minimum makes updates observable during the exercise; processing remains asynchronous. `backstage/app-config.scm.example.yaml` provides equivalent internal GitLab URL registrations. No remote SCM is running here.

## Source, artifact, and publisher cache

- `services/<name>/docs/` and `mkdocs.yml`: authored and reviewed by the domain team.
- `services/<name>/site/`: the generated artifact produced by that repository's build.
- `backstage/.techdocs/default/component/<name>/`: a published copy used by the local Backstage server.

The publisher cache is ignored by Git and can be deleted and rebuilt. It is not a source of truth. The root `scripts/build-docs.sh` harness invokes each repository's contract checks and build, then copies artifacts through `scripts/publish-docs.py`. It does not edit source metadata.

## CI contract

Run `./ci/check.sh` using the repository's Python environment. The tests compare:

- Runtime name, owner, method, route, and port with catalog metadata.
- Dependencies with `dependsOn` and consumed APIs.
- The complete generated FastAPI OpenAPI schema with committed `openapi.yaml`.
- Actual registered routes and an actual ASGI success response with that schema.
- The embedded catalog API definition with the committed snapshot.
- The documented interface table with runtime facts.
- Required support/QA sources and all MkDocs navigation targets with repository-local files.

The pipeline verifies before building the documentation artifact. The owning team's repository policy should require this job for merge; this POC does not alter remote branch protection.

## Reproduce a stale change

1. In a disposable Policy checkout, change `/v1/policies/{tenantID}` in `routes.py` to `/v2/policies/{tenantID}`.
2. Run the repository's CI check.
3. Observe stale catalog endpoint annotations, OpenAPI snapshot, and interface summary.
4. Update the affected metadata and notes, then explicitly run `python tools/sync-api.py` in the active Python environment. Review the generated API and catalog diff.
5. Rerun CI. CI never performs step 4 automatically.

From the complete workspace, `.venv/bin/python scripts/verify-repositories.py` proves isolated checkout behavior and six stale-change rejection cases in temporary copies. `.venv/bin/python scripts/verify-catalog-refresh.py` separately proves automatic Backstage polling by adding and removing one nonfunctional Policy annotation.

## Limits

These checks verify structural consistency and a checked documentation summary. They cannot prove all narrative instructions remain correct, discover arbitrary dynamic dependencies, or choose domain boundaries. Those remain responsibilities of the owning team and integration reviewers.

[Backstage's catalog processing interval](https://backstage.io/docs/features/software-catalog/configuration/#processing-interval) describes the polling schedule. [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/) describe the typed schemas used for the API snapshots.
