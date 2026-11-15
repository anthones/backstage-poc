"""Prove periodic catalog ingestion from a service checkout, without restarting.

Temporarily adds one nonfunctional annotation and removes only that annotation.
"""
import json
from pathlib import Path
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:7007"
KEY = "acmesecure.example/poll-check"


def get(path, token=None):
    headers = {"X-Requested-With": "XMLHttpRequest"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=headers), timeout=10) as response:
        return json.load(response)


def wait_for_annotation(token, expected):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        entity = get("/api/catalog/entities/by-name/component/default/policy-service", token)
        if entity["metadata"]["annotations"].get(KEY) == expected:
            return
        time.sleep(1)
    raise AssertionError(f"Repository annotation was not refreshed to {expected!r}; inspect catalog processing")


def main():
    token = get("/api/auth/guest/refresh")["backstageIdentity"]["token"]
    catalog = ROOT / "services/policy-service/catalog-info.yaml"
    original = catalog.read_text()
    assert KEY not in original, "A refresh exercise marker already exists; finish that exercise first"
    marker = f"    {KEY}: check-{uuid.uuid4().hex}\n"
    value = marker.split(": ", 1)[1].strip()
    try:
        catalog.write_text(original.replace("  annotations:\n", "  annotations:\n" + marker, 1))
        wait_for_annotation(token, value)
        print("PASS: Backstage periodically reread policy-service/catalog-info.yaml without a restart or explicit refresh request.", flush=True)
    finally:
        catalog.write_text(catalog.read_text().replace(marker, "", 1))
        wait_for_annotation(token, None)
        print("PASS: temporary annotation removed from source and ingested catalog.", flush=True)


if __name__ == "__main__":
    main()
