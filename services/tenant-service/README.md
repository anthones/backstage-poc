# Tenant Directory

Owner: **identity**. This is a complete Python/FastAPI repository: implementation, metadata, generated OpenAPI snapshots, TechDocs sources, tests, container build, and CI. It runs and verifies without sibling source files or a Backstage installation.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
PYTHON="$PWD/.venv/bin/python" ./ci/check.sh
.venv/bin/python main.py
```

Requires Python 3.12+. Default listener: `127.0.0.1:8081`. Dependent service URLs default to loopback and can be overridden with `<SERVICE_NAME>_URL`, using uppercase and underscores. Tests use in-process ASGI requests and mock HTTP providers, so they require no sibling processes or listening ports.

- [Boundary and checked interface](docs/index.md)
- [L1 / L2 runbook](docs/runbook.md)
- [QA handover](docs/qa.md)
- [Catalog](catalog-info.yaml) and [committed OpenAPI snapshot](openapi.yaml)

## Interface changes

1. Change `routes.py`, its typed `Result` model, or the implementation in `service.py`.
2. Update catalog owner, endpoint annotations, dependencies, and API relationships when affected.
3. Update the checked interface table in `docs/index.md` and affected support/QA notes.
4. Explicitly run `.venv/bin/python tools/sync-api.py` to generate OpenAPI and refresh its embedded catalog definition. Review both diffs before committing.
5. Run `PYTHON="$PWD/.venv/bin/python" ./ci/check.sh`.

CI compares the entire generated FastAPI schema with the committed snapshot and checks catalog/route/owner/dependency/documentation agreement. It also validates an actual ASGI success response against the schema. CI never repairs stale files. Narrative instructions still require review by the owning team.

## TechDocs ownership and publication

```sh
PYTHON="$PWD/.venv/bin/python" ./ci/build-docs.sh
```

Sources and navigation are `docs/` and `mkdocs.yml` inside this repository. The generated artifact is this repository's ignored `site/` directory. `.gitlab-ci.yml` uses one Python image for both verification and documentation, and publishes `site/` only after verification passes. Runtime-only installations use `requirements.txt`; development, tests, and docs share `requirements-dev.txt` and the same virtual environment.

The internal publishing step copies this artifact to `default/component/tenant-service/` in Backstage's TechDocs storage. In the local integration workspace, `scripts/publish-docs.py` makes that copy in `backstage/.techdocs/`. That directory is disposable publication storage, not another source of documentation.

Backstage polls this repository's own `catalog-info.yaml`. The optional integration workspace registers a local file location; its `backstage/app-config.scm.example.yaml` shows internal GitLab URL registration for a real repository.
