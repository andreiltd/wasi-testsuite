from typing import List
from pathlib import Path

from .filters import (
    TestFilter, JSONTestExcludeFilter, UnsupportedWasiTestExcludeFilter
)
from .reporters import TestReporter
from .reporters.console import ConsoleTestReporter
from .reporters.json import JSONTestReporter
from .test_suite_runner import run_tests_from_generated_manifest
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
    """Run tests listed in a manifest.

    This is the primary entry point. It reads a manifest that lists all
    tests and their metadata, then runs them through each runtime adapter.
    """
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
