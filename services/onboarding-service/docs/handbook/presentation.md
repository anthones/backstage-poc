# Integration walkthrough

For a shared-screen meeting, use the [live presentation script](live-event-script.md). It includes timed speaking notes, stakeholder benefits, and recovery cues.

## Preparation

From the workspace root:

```sh
./scripts/setup.sh
./scripts/check-services.sh
.venv/bin/python scripts/verify-repositories.py
./scripts/start.sh
```

Open the default catalog at `http://localhost:3000/`. The engineering manual is at `/demo`. Keep a terminal and one service folder available beside the browser.

## Inspect a repository boundary

Open `services/policy-service/`. Show `routes.py`, its independent `requirements-dev.txt`, `catalog-info.yaml`, `openapi.yaml`, `docs/`, `tests/test_contract.py`, and `.gitlab-ci.yml`. Run `./ci/check.sh` from that directory. No sibling code or Backstage package is needed for this check.

Use `.venv/bin/python scripts/verify-repositories.py` from the workspace root to show isolated checkout checks and stale-change rejections without changing the actual sources. Review the route mutation in that script: CI reports stale catalog annotations, API paths, and the checked docs table.

## Inspect ingestion

In Backstage, open the Policy component and its API and TechDocs. Metadata and documentation originate inside the owning repository. The app has a separate catalog location for each service and periodically rereads the local files. The internal GitLab configuration example shows how to replace these file locations with repository URLs.

Open the catalog graph to inspect cross-team dependencies. Use the service documentation links to read authoritative boundaries and support instructions. The system handbook links to those sources rather than maintaining duplicate service runbooks.

## Run the integration exercise

```sh
./scripts/demo.sh happy
./scripts/demo.sh outage
./scripts/demo.sh recover
.venv/bin/python scripts/verify.py
.venv/bin/python scripts/verify-backstage.py
```

The outage command deliberately returns nonzero. Use the response's root cause and request ID, the catalog owner, and the owning service's runbook to trace the failure. The graph shows declared relationships, not live health.

## Review a change handover

Open a service's QA TechDocs. The repository owner changes code, metadata, interface summary, and affected operating notes together. CI verifies structural agreement; reviewers check domain meaning and narrative instructions. Integration QA follows catalog consumers for regression coverage.

## Shutdown

Ctrl-C in the workspace runner stops its child processes. If the exercise is interrupted after injecting an outage, use `./scripts/demo.sh recover` before continuing. Logs are in `.run/`.
