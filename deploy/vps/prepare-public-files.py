"""Stage VPS catalog/docs and replace Backstage's local navigation origin.

Usage: python3 deploy/vps/prepare-public-files.py RELEASE_DIR https://catalog.example.com
The release directory must not already exist. Authored source files stay intact.
"""
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[2]
release = Path(sys.argv[1]).resolve()
origin = sys.argv[2].rstrip("/")
url = urlsplit(origin)
if url.scheme != "https" or not url.hostname or url.path or url.query or url.fragment or url.username:
    raise SystemExit("Expected an HTTPS origin without a path, query, or credentials")
if release.exists():
    raise SystemExit(f"Release already exists: {release}; use a new release ID")
docs = root / "backstage/.techdocs"
if not (docs / "default/component/customer-portal/techdocs_metadata.json").is_file():
    raise SystemExit("Build TechDocs first with scripts/build-docs.sh")
public = release / "public"
public.mkdir(parents=True)
shutil.copy2(root / "deploy/vps/app-config.vps.yaml", release / "app-config.vps.yaml")
shutil.copytree(root / "catalog", public / "catalog")
for source in sorted((root / "services").glob("*/catalog-info.yaml")):
    target = public / "services" / source.parent.name
    target.mkdir(parents=True)
    shutil.copy2(source, target / source.name)
    shutil.copy2(source.with_name("openapi.yaml"), target / "openapi.yaml")
portal = public / "frontend/customer-portal"
portal.mkdir(parents=True)
shutil.copy2(root / "frontend/customer-portal/catalog-info.yaml", portal / "catalog-info.yaml")
shutil.copy2(root / "frontend/customer-portal/static/index.html", public / "portal-index.html")
shutil.copytree(docs, public / "techdocs")
for path in public.rglob("*"):
    if path.is_file() and path.suffix in {".yaml", ".yml", ".html", ".json", ".js", ".svg", ".css", ".md"}:
        content = path.read_text(encoding="utf-8")
        updated = content.replace("http://localhost:3000", origin)
        if updated != content:
            path.write_text(updated, encoding="utf-8")
print(f"Prepared {release}; local service API/health links still require SSH tunnels.")
