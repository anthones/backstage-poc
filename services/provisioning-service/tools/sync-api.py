"""Explicit developer command: generate the API snapshots; CI never runs this."""
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from main import app

catalog = ROOT / "catalog-info.yaml"
head, separator, tail = catalog.read_text().partition("\n  definition: |\n")
if not separator or any(line.strip() and not line.startswith("    ") for line in tail.splitlines()):
    raise SystemExit("Expected the API definition literal as the final field in catalog-info.yaml")
contract = yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True)
(ROOT / "openapi.yaml").write_text(contract)
catalog.write_text(head + separator + "".join("    " + line if line.strip() else line for line in contract.splitlines(keepends=True)))
print("Updated generated OpenAPI and embedded catalog API; review both before committing.")
