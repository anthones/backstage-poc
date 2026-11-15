"""Copy repository-built artifacts to Backstage's local publication cache.

This cache contains no authored documentation and can be rebuilt at any time.
"""
from pathlib import Path
import shutil
import tempfile

from load_model import load_model

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "backstage/.techdocs/default/component"


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    for service in load_model():
        name = service["name"]
        source = ROOT / "services" / name / "site"
        assert (source / "techdocs_metadata.json").is_file(), f"Build {name}'s documentation first"
        target = CACHE / name
        with tempfile.TemporaryDirectory(prefix="publish-", dir=CACHE.parent) as temporary:
            staged = Path(temporary) / name
            shutil.copytree(source, staged)
            if target.exists():
                shutil.rmtree(target)
            staged.rename(target)
    # The handbook now belongs to onboarding-service; no floating seventh site.
    old_handbook = CACHE / "activation-handbook"
    if old_handbook.exists():
        shutil.rmtree(old_handbook)
    shutil.copyfile(ROOT / "services/onboarding-service/docs/handbook/assets/architecture.svg",
                    ROOT / "backstage/packages/app/public/activation-architecture.svg")
    print("Published six repository-owned site/ artifacts to Backstage's generated cache.")


if __name__ == "__main__":
    main()
