"""Run a single WASI test via the runner + adapter.

Usage:
    python3 run_wasi_test.py --wasm FILE --adapter FILE \
        [--wasi-version VER] [--config FILE]
"""
import argparse
import os
import sys
from pathlib import Path


def main():
    """Run one WASI test."""
    parser = argparse.ArgumentParser(description="Run a single WASI test")
    parser.add_argument("--wasm", required=True, help="Path to .wasm file")
    parser.add_argument("--adapter", required=True, help="Path to adapter .py")
    parser.add_argument("--wasi-version", default="wasm32-wasip1")
    parser.add_argument("--config", help="Path to test .json config")
    args = parser.parse_args()

    # Add test-runner to path
    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir.parent, Path.cwd()]:
        runner_dir = candidate / "test-runner"
        if runner_dir.is_dir():
            sys.path.insert(0, str(runner_dir))
            break

    # Set LD_LIBRARY_PATH for runtimes with shared libs (e.g. wasmedge)
    for env_var in ("WASMEDGE", "WASMTIME", "WAZERO", "IWASM"):
        binary = os.environ.get(env_var)
        if binary:
            lib_dir = os.path.join(
                os.path.dirname(os.path.abspath(binary)), "..", "lib64",
            )
            if os.path.isdir(lib_dir):
                existing = os.environ.get("LD_LIBRARY_PATH", "")
                os.environ["LD_LIBRARY_PATH"] = (
                    lib_dir + (":" + existing if existing else "")
                )

    from wasi_test_runner.harness import run_single_test
    from wasi_test_runner.runtime_adapter import RuntimeAdapter

    adapter = RuntimeAdapter(args.adapter)
    sys.exit(run_single_test(
        wasm_path=args.wasm,
        adapter=adapter,
        wasi_version=args.wasi_version,
        config_path=args.config,
    ))


if __name__ == "__main__":
    main()
