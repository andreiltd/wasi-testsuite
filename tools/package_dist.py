"""Package wasi-testsuite into a distributable .tar.gz archive.

Usage:
    python3 package_dist.py --staging DIR --output FILE --manifest FILE \
        [--config-dir SUITE:DIR ...] [SRC:DST ...]
"""

import argparse
import json
import os
import shutil
import sys
import tarfile
from pathlib import Path


def _copy_item(src, dst):
    """Copy a file or directory to dst, creating parents as needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def _copy_configs_and_rewrite_manifest(manifest_path, config_dirs, staging):
    """Copy configs next to wasm files and rewrite manifest with correct paths."""
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    for suite in manifest.get("suites", []):
        config_dir = config_dirs.get(suite["name"])
        if not config_dir:
            # Remove stale config refs for suites without a config_dir
            for test in suite.get("tests", []):
                test.pop("config", None)
            continue

        for test in suite.get("tests", []):
            wasm_path = test.get("wasm", "")
            if not wasm_path:
                continue

            config_src = Path(config_dir) / f"{test['name']}.json"
            if not config_src.is_file():
                test.pop("config", None)
                continue

            # Place config next to the wasm file
            stem = Path(wasm_path).stem
            if stem.endswith(".component"):
                stem = stem[:-len(".component")]
            config_rel = str(Path(wasm_path).parent / f"{stem}.json")
            _copy_item(str(config_src), staging / config_rel)
            test["config"] = config_rel

    # Write corrected manifest
    with open(staging / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Package wasi-testsuite into a .tar.gz"
    )
    parser.add_argument("--staging", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--config-dir", action="append", default=[])
    parser.add_argument("items", nargs="*")
    args = parser.parse_args()

    staging = Path(args.staging)
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # Copy manifest (will be rewritten later if config_dirs are provided)
    shutil.copy2(args.manifest, staging / "manifest.json")

    # Copy components and fixtures
    for item in args.items:
        if ":" not in item:
            print(f"warning: skipping malformed item: {item}", file=sys.stderr)
            continue
        src, dst = item.split(":", 1)
        _copy_item(src, staging / dst)

    # Copy configs and rewrite manifest with correct archive-relative paths
    config_dirs = {}
    for spec in args.config_dir:
        if ":" in spec:
            name, path = spec.split(":", 1)
            config_dirs[name] = path

    if config_dirs:
        _copy_configs_and_rewrite_manifest(args.manifest, config_dirs, staging)

    with tarfile.open(args.output, "w:gz") as tar:
        tar.add(staging, arcname=staging.name)

    total = sum(1 for _ in staging.rglob("*") if _.is_file())
    print(f"Packaged {total} files into {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
