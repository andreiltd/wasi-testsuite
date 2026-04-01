import os
import shutil
import tempfile
from datetime import datetime
from typing import List
from pathlib import Path

from .filters import (
    TestFilter, JSONTestExcludeFilter, UnsupportedWasiTestExcludeFilter
)
from .reporters import TestReporter
from .reporters.console import ConsoleTestReporter
from .reporters.json import JSONTestReporter
from .test_suite_runner import (
    run_tests_from_generated_manifest,
    _execute_single_test,
    _read_test_config,
)
from .test_suite import TestSuite, TestSuiteMeta
from .test_case import WasiVersion, Config, Run, Operation
from .runtime_adapter import RuntimeAdapter


# pylint: disable-msg=unknown-option-value
# pylint: disable-msg=too-many-arguments
# pylint: disable-msg=too-many-positional-arguments
def run_tests_from_manifest(
    runtimes: List[RuntimeAdapter],
    manifest_path: str,
    base_dir: str | None = None,
    exclude_filters: List[Path] | None = None,
    color: bool = True,
    verbose: bool = False,
    json_log_file: str | None = None,
) -> int:
    """Run tests listed in a manifest."""
    if base_dir is None:
        base_dir = str(Path(manifest_path).parent)

    reporters: List[TestReporter] = [ConsoleTestReporter(color, verbose=verbose)]
    if json_log_file:
        reporters.append(JSONTestReporter(json_log_file))
    filters: List[TestFilter] = [UnsupportedWasiTestExcludeFilter()]
    if exclude_filters is not None:
        filters += [JSONTestExcludeFilter(str(filt)) for filt in exclude_filters]

    ret = 0
    for runtime in runtimes:
        suites = run_tests_from_generated_manifest(
            manifest_path, base_dir, runtime, reporters, filters,
        )
        for suite in suites:
            if suite.fail_count > 0:
                ret = 1

    for reporter in reporters:
        reporter.finalize()

    return ret


def _get_dirs_from_config(config: Config) -> list:
    """Extract directory pairs from config operations."""
    for op in config.operations:
        if isinstance(op, Run) and op.dirs:
            return list(op.dirs)
    return []


def _isolate_dirs(dirs: list, scratch: str) -> list:
    """Copy dirs to scratch and return new (host, guest) pairs."""
    new_dirs = []
    for host_path, guest_name in dirs:
        dst = Path(scratch) / guest_name
        if host_path.is_dir():
            shutil.copytree(str(host_path), str(dst), symlinks=True)
        new_dirs.append((dst, guest_name))
    return new_dirs


def _config_with_isolated_dirs(config: Config, scratch: str) -> Config:
    """Return a new Config with dirs copied to scratch."""
    new_ops: list[Operation] = []
    for op in config.operations:
        if isinstance(op, Run) and op.dirs:
            new_dirs = _isolate_dirs(op.dirs, scratch)
            new_ops.append(Run(args=op.args, env=op.env, dirs=new_dirs))
        else:
            new_ops.append(op)
    return Config(operations=new_ops, proposals=config.proposals, world=config.world)


def run_single_test(
    wasm_path: str,
    adapter: RuntimeAdapter,
    wasi_version: str = "wasm32-wasip1",
    config_path: str | None = None,
) -> int:
    """Run a single WASI test directly.

    Returns 0 on success, 1 on failure.
    """
    version = WasiVersion(wasi_version)
    meta = TestSuiteMeta("test", version, adapter.get_meta())

    test_name = Path(wasm_path).stem
    if test_name.endswith(".component"):
        test_name = test_name[:-len(".component")]

    if config_path and os.path.isfile(config_path):
        config = Config.from_file(config_path)
    else:
        config = _read_test_config(wasm_path)

    # Isolate fixture directories to avoid parallel test interference
    scratch = None
    dirs = _get_dirs_from_config(config)
    if dirs:
        scratch = tempfile.mkdtemp()
        config = _config_with_isolated_dirs(config, scratch)

    try:
        reporter = ConsoleTestReporter(colored=False, verbose=True)
        test_case = _execute_single_test(
            adapter, meta, wasm_path, test_name, config)
        reporter.report_test(meta, test_case)
        reporter.report_test_suite(TestSuite(
            meta=meta, time=datetime.now(),
            duration_s=test_case.duration_s, test_cases=[test_case],
        ))
        reporter.finalize()
    finally:
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)

    return 1 if test_case.result.failed else 0
