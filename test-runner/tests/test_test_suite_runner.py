from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import json
import tempfile
import os

import wasi_test_runner.test_case as tc
import wasi_test_runner.test_suite_runner as tsr
from wasi_test_runner.runtime_adapter import RuntimeMeta


def _make_runtime() -> Mock:
    """Create a mock runtime adapter."""
    meta = RuntimeMeta(
        "rt1", "4.2",
        frozenset([tc.WasiVersion.WASM32_WASIP1]),
        frozenset([tc.WasiWorld.CLI_COMMAND]),
    )
    runtime = Mock()
    runtime.get_name.return_value = meta.name
    runtime.get_meta.return_value = meta
    runtime.compute_argv.return_value = [meta.name, "<test>"]
    return runtime


def _make_process() -> Mock:
    """Create a mock subprocess."""
    process = Mock()
    process.stdin = mock_open().return_value
    process.stdout = mock_open(read_data='').return_value
    process.stderr = mock_open(read_data='').return_value
    process.returncode = 0
    process.communicate.return_value = ('', '')
    return process


def test_runner_end_to_end_with_manifest() -> None:
    """Test the manifest-based runner with a generated manifest."""
    runtime = _make_runtime()
    process = _make_process()
    reporters = [Mock(), Mock()]
    filt = Mock()
    filt.should_skip.return_value = (False, None)

    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ["test1", "test2"]:
            Path(tmpdir, f"{name}.wasm").write_bytes(b"fake wasm")

        with open(os.path.join(tmpdir, "test2.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"exit_code": 1, "args": ["a", "b"]}, f)

        manifest_path = os.path.join(tmpdir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": 1,
                "suites": [{
                    "name": "test-suite",
                    "wasi_version": "wasm32-wasip1",
                    "tests": [
                        {"name": "test1", "wasm": "test1.wasm"},
                        {"name": "test2", "wasm": "test2.wasm",
                         "config": "test2.json"},
                    ],
                }],
            }, f)

        with patch("wasi_test_runner.test_suite_runner._cleanup_test_output"), \
             patch("subprocess.Popen", return_value=process):
            suites = tsr.run_tests_from_generated_manifest(
                manifest_path, tmpdir, runtime,
                reporters, [filt])  # type: ignore

    assert len(suites) == 1
    assert suites[0].meta.name == "test-suite"
    assert suites[0].test_count == 2
    assert process.communicate.call_count == 2
    for reporter in reporters:
        assert reporter.report_test.call_count == 2
