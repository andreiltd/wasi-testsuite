"""Reusable Buck2 python_test wrapper for the WASI test runner.

Usage from python_test:
    import run_wasi_test
    run_wasi_test.main()

Expects environment variables:
    WASM_FILE     — path to the .wasm test binary
    WASI_CONFIG   — (optional) path to the .json test config
    FIXTURE_DIRS  — (optional) colon-separated list of fixture directories
    WASMTIME      — path to wasmtime binary (set by Buck2 toolchain)
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


class WasiTest(unittest.TestCase):
    def test_wasm(self):
        wasm_file = os.environ["WASM_FILE"]
        config_file = os.environ.get("WASI_CONFIG", "")
        fixture_dirs = os.environ.get("FIXTURE_DIRS", "")

        # Create temp test suite directory
        suite_dir = tempfile.mkdtemp()
        try:
            test_name = Path(wasm_file).stem
            shutil.copy2(wasm_file, os.path.join(suite_dir, f"{test_name}.wasm"))

            if config_file and os.path.isfile(config_file):
                shutil.copy2(config_file, os.path.join(suite_dir, f"{test_name}.json"))

            if fixture_dirs:
                for d in fixture_dirs.split(":"):
                    if os.path.isdir(d):
                        shutil.copytree(d, os.path.join(suite_dir, os.path.basename(d)))

            from wasi_test_runner.harness import run_all_tests
            from wasi_test_runner.runtime_adapter import RuntimeAdapter
            from wasi_test_runner.reporters.console import ConsoleTestReporter
            from wasi_test_runner.filters import UnsupportedWasiTestExcludeFilter

            adapter = RuntimeAdapter(os.environ.get("WASI_ADAPTER", "adapters/wasmtime.py"))
            reporters = [ConsoleTestReporter(colored=False, verbose=True)]
            filters = [UnsupportedWasiTestExcludeFilter()]

            result = run_all_tests([adapter], [suite_dir], reporters, filters)
            self.assertEqual(result, 0, f"WASI test {test_name} failed")
        finally:
            shutil.rmtree(suite_dir, ignore_errors=True)
