"""Macro for generating per-runtime WASI conformance test targets.

Usage in BUCK:

    load("//tools:conformance.bzl", "wasi_conformance_tests")

    wasi_conformance_tests(
        name = "wasmtime",
        adapter = "adapters/wasmtime.py",
        suites = {
            "c-wasip1": {
                "wasi_version": "wasm32-wasip1",
                "config_dir": "tests/c/src",
                "component_prefix": "//tests/c",
                "component_suffix": "",
                "tests": ["lseek", "clock_getres-monotonic", ...],
            },
            ...
        },
    )

This generates one python_test per test, using the Python runner + adapter.
"""

def wasi_conformance_tests(
        name,
        adapter,
        suites,
        labels = []):
    """Generate per-test conformance targets for a single runtime.

    Args:
        name: Runtime name prefix for generated targets (e.g. "wasmtime").
        adapter: Path to the Python runtime adapter file.
        suites: Dict of suite definitions, same structure as wasi_manifest.
        labels: Extra labels for all generated test targets.
    """
    all_tests = []

    for suite_name, suite in suites.items():
        config_dir = suite.get("config_dir", "")
        component_prefix = suite.get("component_prefix", "")
        component_suffix = suite.get("component_suffix", "_component")

        for test_name in suite["tests"]:
            target_name = "{}_{}_{}".format(name, suite_name, test_name)
            component_target = "{}:{}{}".format(
                component_prefix,
                test_name,
                component_suffix,
            )

            config_path = ""
            if config_dir:
                config_path = "{}/{}.json".format(config_dir, test_name)

            native.python_test(
                name = target_name,
                main_module = "run_wasi_test",
                deps = ["//tools:run_wasi_test"],
                env = {
                    "WASM_FILE": "$(location {})".format(component_target),
                    "WASI_CONFIG": config_path,
                    "WASI_ADAPTER": adapter,
                },
                labels = [name, suite_name] + labels,
            )

            all_tests.append(":" + target_name)

    # Aggregate target for all tests on this runtime
    native.test_suite(
        name = name,
        tests = all_tests,
    )
