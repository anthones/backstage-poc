"""Local orchestration reads service-owned YAML; no duplicate runtime inventory."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_model():
    model = []
    for name in json.loads((ROOT / "scripts/services.json").read_text()):
        component = next(entity for entity in yaml.safe_load_all((ROOT / "services" / name / "catalog-info.yaml").read_text()) if entity["kind"] == "Component")
        annotations = component["metadata"]["annotations"]
        model.append({"name": name, "port": int(annotations["acmesecure.example/http-port"]),
                      "owner": component["spec"]["owner"].split("/")[-1],
                      "route": annotations["acmesecure.example/http-route"],
                      "dependencies": [ref.split("/")[-1] for ref in component["spec"]["dependsOn"]]})
    return model
