"""Reusable Buck2 python_test wrapper for the WASI test runner.

Usage from python_test:
    import run_wasi_test
    run_wasi_test.main()

Expects environment variables:
    WASM_FILE:    path to the .wasm test binary
    WASI_CONFIG:  (optional) path to the .json test config
    WASI_ADAPTER: path to the runtime adapter
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


class WasiTest(unittest.TestCase):
    """Buck2 python_test wrapper for running a single WASI test."""

    def test_wasm(self):
        """Run one WASI test via the manifest-based runner."""
        wasm_file = os.environ["WASM_FILE"]
        config_file = os.environ.get("WASI_CONFIG", "")
        suite_dir = tempfile.mkdtemp()

        try:
            test_name = Path(wasm_file).stem
            if test_name.endswith(".component"):
                test_name = test_name[:-len(".component")]

            # Copy wasm and config into a flat directory
            wasm_dst = os.path.join(suite_dir, f"{test_name}.wasm")
            shutil.copy2(wasm_file, wasm_dst)

            if config_file and os.path.isfile(config_file):
                shutil.copy2(config_file, os.path.join(suite_dir, f"{test_name}.json"))

            # Generate a minimal manifest
            manifest = {
                "version": 1,
                "suites": [{
                    "name": "test",
                    "wasi_version": "wasm32-wasip1",
                    "tests": [{
                        "name": test_name,
                        "wasm": f"{test_name}.wasm",
                    }],
                }],
            }

            manifest_path = os.path.join(suite_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)

            from wasi_test_runner.harness import run_tests_from_manifest
            from wasi_test_runner.runtime_adapter import RuntimeAdapter

            adapter = RuntimeAdapter(os.environ.get("WASI_ADAPTER", "adapters/wasmtime.py"))

            result = run_tests_from_manifest(
                [adapter],
                manifest_path=manifest_path,
                base_dir=suite_dir,
                color=False,
                verbose=True,
            )
            self.assertEqual(result, 0, f"WASI test {test_name} failed")
        finally:
            shutil.rmtree(suite_dir, ignore_errors=True)
