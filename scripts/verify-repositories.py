"""Prove Python repository isolation and CI rejection in disposable copies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
NAMES = json.loads((ROOT / "scripts/services.json").read_text())
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
IGNORE = shutil.ignore_patterns(".git", ".run", ".venv", "site", "__pycache__", ".pytest_cache")


def check(directory):
    return subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_contract.py"], cwd=directory,
                          env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main():
    for name in NAMES:
        with tempfile.TemporaryDirectory(prefix="standalone-catalog-") as temporary:
            repo = Path(temporary) / name
            shutil.copytree(ROOT / "services" / name, repo, ignore=IGNORE)
            result = check(repo)
            assert result.returncode == 0, result.stdout
            print(f"PASS standalone: {name}", flush=True)
    with tempfile.TemporaryDirectory(prefix="catalog-drift-") as temporary:
        repo = Path(temporary) / "policy-service"
        shutil.copytree(ROOT / "services/policy-service", repo, ignore=IGNORE)
        cases = [
            ("route", "routes.py", "/v1/policies/{tenantID}", "/v2/policies/{tenantID}"),
            ("owner", "routes.py", 'owner="cloud-security"', 'owner="identity"'),
            ("dependency", "routes.py", 'Dependency("tenant-service"', 'Dependency("shadow-service"'),
            ("response field", "routes.py", "policy_version", "policy_revision"),
            ("documentation", "docs/index.md", "`GET /v1/policies/{tenantID}`", "`POST /v1/policies/{tenantID}`"),
            ("embedded API", "catalog-info.yaml", "    openapi: 3.1.0", "    openapi: 3.0.3"),
        ]
        for label, file, original, replacement in cases:
            path = repo / file
            committed = path.read_text()
            assert original in committed, f"Mutation target missing: {label}"
            try:
                path.write_text(committed.replace(original, replacement))
                result = check(repo)
                assert result.returncode != 0 and "drift" in result.stdout, f"CI did not reject {label}: {result.stdout}"
                print(f"PASS rejected stale {label}", flush=True)
            finally:
                path.write_text(committed)
    print("PASS: six standalone Python repositories; six stale-change cases rejected. Source repositories were not modified.")


if __name__ == "__main__":
    main()
