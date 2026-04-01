import argparse
import sys
from pathlib import Path

from .runtime_adapter import RuntimeAdapter
from .harness import run_tests_from_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WebAssembly System Interface test executor"
    )

    parser.add_argument(
        "test_suite",
        help="Path to a test suite directory containing manifest.json.",
    )
    parser.add_argument(
        "-r", "--runtime-adapter",
        required=True,
        help="Path to a runtime adapter.",
    )
    parser.add_argument(
        "-f",
        "--exclude-filter",
        required=False,
        nargs="+",
        default=[],
        help="Locations of test exclude filters (JSON files).",
    )
    parser.add_argument(
        "--json-output-location",
        help="JSON test result destination.",
    )
    parser.add_argument(
        "--disable-colors",
        action="store_true",
        default=False,
        help="Disables color for console output reporter.",
    )

    options = parser.parse_args()

    suite_dir = Path(options.test_suite)
    manifest_path = suite_dir / "manifest.json"

    if not manifest_path.is_file():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        return 1

    return run_tests_from_manifest(
        [RuntimeAdapter(options.runtime_adapter)],
        manifest_path=str(manifest_path),
        base_dir=str(suite_dir),
        color=not options.disable_colors,
        json_log_file=options.json_output_location,
        exclude_filters=options.exclude_filter or None,
    )


if __name__ == "__main__":
    sys.exit(main())
