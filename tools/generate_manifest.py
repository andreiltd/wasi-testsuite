"""Generate a wasi-testsuite manifest from test definitions.

The manifest is the integration contract: it lists every test in the suite
along with the metadata a runner needs to execute it (WASI version, config
path, fixture directories, required proposals, etc.).

Usage from buck2 (via genrule):
    python3 generate_manifest.py --output manifest.json --tests-json <file>

Usage standalone (scan a prebuilt testsuite directory):
    python3 generate_manifest.py --output manifest.json --scan-dir testsuite/

The --tests-json file is a JSON array of test entries, one per test:
    [
      {
        "name": "fd_readdir",
        "wasm": "wasm/wasm32-wasip1/fd_readdir.component.wasm",
        "config": "configs/wasm32-wasip1/fd_readdir.json",
        "suite": "rust-wasip1",
        "wasi_version": "wasm32-wasip1"
      },
      ...
    ]
"""

import argparse
import json
import os
import sys
from pathlib import Path

MANIFEST_VERSION = 1


def load_test_config(config_path):
    """Load a test's .json config and extract metadata from it."""
    if not config_path or not os.path.isfile(config_path):
        return {}
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def infer_metadata_from_config(config):
    """Extract proposals, world, and fixture dirs from a test config."""
    meta = {}

    # Operation-based config
    if "proposals" in config:
        meta["proposals"] = config["proposals"]
    if "world" in config:
        meta["world"] = config["world"]

    # Extract dirs from either legacy or operation-based format
    dirs = []
    if "dirs" in config:
        dirs = config["dirs"]
    elif "operations" in config:
        for op in config["operations"]:
            if op.get("type") == "run" and "dirs" in op:
                dirs = op["dirs"]
                break
    if dirs:
        meta["fixtures"] = dirs

    return meta


def build_manifest_from_tests_json(tests_json_path, base_dir=None):
    """Build manifest from an explicit list of test definitions.

    Each entry may have either:
      - "config": explicit path to a .json config, or
      - "config_dir": directory to probe for <name>.json (auto-discovery)
    If neither is present, the test uses default expectations.
    """
    with open(tests_json_path, encoding="utf-8") as f:
        tests = json.load(f)

    suites = {}
    for t in tests:
        suite_name = t.get("suite", "default")
        if suite_name not in suites:
            suites[suite_name] = {
                "name": suite_name,
                "wasi_version": t.get("wasi_version", "wasm32-wasip1"),
                "tests": [],
            }

        # Resolve config path: explicit > auto-discovered > none
        config_rel = t.get("config", "")
        if not config_rel and t.get("config_dir"):
            candidate = os.path.join(t["config_dir"], t["name"] + ".json")
            if base_dir and os.path.isfile(os.path.join(base_dir, candidate)):
                config_rel = candidate
            elif not base_dir and os.path.isfile(candidate):
                config_rel = candidate

        config_path = ""
        if config_rel:
            config_path = os.path.join(base_dir, config_rel) if base_dir else config_rel

        config = load_test_config(config_path)
        meta = infer_metadata_from_config(config)

        entry = {
            "name": t["name"],
            "wasm": t["wasm"],
        }
        if config_rel:
            entry["config"] = config_rel
        if meta.get("proposals"):
            entry["proposals"] = meta["proposals"]
        if meta.get("world"):
            entry["world"] = meta["world"]
        if meta.get("fixtures"):
            entry["fixtures"] = meta["fixtures"]

        suites[suite_name]["tests"].append(entry)

    return {
        "version": MANIFEST_VERSION,
        "suites": list(suites.values()),
    }


def _infer_wasi_version(parts):
    """Infer WASI version from path components."""
    for part in parts:
        if "wasip3" in part:
            return "wasm32-wasip3"
        if "wasip2" in part:
            return "wasm32-wasip2"
    return "wasm32-wasip1"


def _find_config(wasm_file, test_name, scan_path):
    """Find a test config file next to a wasm file."""
    for candidate in [wasm_file.with_suffix(".json"),
                      wasm_file.parent / (test_name + ".json")]:
        if candidate.exists():
            config = load_test_config(str(candidate))
            config_rel = str(candidate.relative_to(scan_path))
            return config_rel, config
    return None, {}


def scan_testsuite_dir(scan_dir):
    """Build manifest by scanning a prebuilt testsuite directory.

    Expected layout (matches the dist archive):
        scan_dir/
          <suite>/           e.g. "wasm32-wasip1/"
            *.wasm           test binaries
            *.json           per-test configs (optional)
            manifest.json    suite-level manifest (optional)
            *.dir/           fixture directories (optional)
    """
    scan_path = Path(scan_dir)
    suites = {}

    for wasm_file in sorted(scan_path.rglob("*.wasm")):
        rel = wasm_file.relative_to(scan_path)

        suite_name = str(rel.parent) if len(rel.parts) > 1 else "default"
        wasi_version = _infer_wasi_version(rel.parts)

        if suite_name not in suites:
            suite_display = suite_name
            manifest_path = wasm_file.parent / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, encoding="utf-8") as f:
                    suite_display = json.load(f).get("name", suite_name)
            suites[suite_name] = {
                "name": suite_display,
                "wasi_version": wasi_version,
                "tests": [],
            }

        test_name = wasm_file.stem
        if test_name.endswith(".component"):
            test_name = test_name[:-len(".component")]

        config_rel, config = _find_config(wasm_file, test_name, scan_path)
        meta = infer_metadata_from_config(config)

        entry = {
            "name": test_name,
            "wasm": str(rel),
        }
        if config_rel:
            entry["config"] = config_rel
        if meta.get("proposals"):
            entry["proposals"] = meta["proposals"]
        if meta.get("world"):
            entry["world"] = meta["world"]
        if meta.get("fixtures"):
            entry["fixtures"] = meta["fixtures"]

        suites[suite_name]["tests"].append(entry)

    return {
        "version": MANIFEST_VERSION,
        "suites": list(suites.values()),
    }


def main():
    """CLI entry point for manifest generation."""
    parser = argparse.ArgumentParser(
        description="Generate a wasi-testsuite manifest."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output manifest.json path",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--tests-json",
        help="Path to JSON file with explicit test definitions",
    )
    group.add_argument(
        "--scan-dir",
        help="Path to a prebuilt testsuite directory to scan",
    )

    parser.add_argument(
        "--base-dir",
        help="Base directory for resolving relative config paths (used with --tests-json)",
    )

    args = parser.parse_args()

    if args.tests_json:
        manifest = build_manifest_from_tests_json(args.tests_json, args.base_dir)
    else:
        manifest = scan_testsuite_dir(args.scan_dir)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    total = sum(len(s["tests"]) for s in manifest["suites"])
    print(
        f"Generated manifest: {len(manifest['suites'])} suites, {total} tests",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
