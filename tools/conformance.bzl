"""Macro for generating per-runtime WASI conformance test targets."""

load("@wasmono//toolchains/wasm:transition.bzl", "wasm_transition")
load("//tools:wasip1_transition.bzl", "wasm_transition_p1")

def _wasi_conformance_test_impl(ctx: AnalysisContext) -> list[Provider]:
    component_file = ctx.attrs.component[DefaultInfo].default_outputs[0]

    test_cmd = cmd_args(
        "python3",
        ctx.attrs._run_wasi_test,
        "--wasm",
        component_file,
        "--adapter",
        ctx.attrs.adapter,
        "--wasi-version",
        ctx.attrs.wasi_version,
    )
    if ctx.attrs.config:
        test_cmd.add("--config", ctx.attrs.config)

    test_env = {}
    if ctx.attrs.runtime:
        runtime_cmd = ctx.attrs.runtime[RunInfo].args
        test_env[ctx.attrs.runtime_env_var] = runtime_cmd
        test_cmd.add(cmd_args(hidden = runtime_cmd))
        if ctx.attrs.runtime[DefaultInfo].default_outputs:
            test_cmd.add(cmd_args(hidden = ctx.attrs.runtime[DefaultInfo].default_outputs))

    return [
        DefaultInfo(default_output = component_file),
        ExternalRunnerTestInfo(
            type = "custom",
            command = [test_cmd],
            env = test_env,
        ),
    ]

_ATTRS = {
    "component": None,  # set per rule (different transition)
    "adapter": attrs.string(),
    "wasi_version": attrs.string(default = "wasm32-wasip1"),
    "config": attrs.option(attrs.string(), default = None),
    "runtime": attrs.option(attrs.dep(), default = None),
    "runtime_env_var": attrs.string(default = "WASMTIME"),
    "_run_wasi_test": attrs.source(default = "//tools:run_wasi_test.py"),
    "labels": attrs.list(attrs.string(), default = []),
}

_wasi_conformance_test = rule(
    impl = _wasi_conformance_test_impl,
    attrs = dict(_ATTRS, component = attrs.transition_dep(cfg = wasm_transition)),
)

_wasi_conformance_test_p1 = rule(
    impl = _wasi_conformance_test_impl,
    attrs = dict(_ATTRS, component = attrs.transition_dep(cfg = wasm_transition_p1)),
)

def wasi_conformance_tests(
        name,
        adapter,
        suites,
        runtime = None,
        runtime_env_var = "WASMTIME",
        skip = [],
        labels = []):
    """Generate per-test conformance targets for a single runtime."""
    all_tests = []

    for suite_name, suite in suites.items():
        config_dir = suite.get("config_dir", "")
        component_prefix = suite.get("component_prefix", "")
        component_suffix = suite.get("component_suffix", "_component")
        wasi_version = suite.get("wasi_version", "wasm32-wasip1")
        suite_tests = []

        for test_name in suite["tests"]:
            if test_name in skip:
                continue

            target_name = "{}_{}_{}".format(name, suite_name, test_name)
            component_target = "{}:{}{}".format(component_prefix, test_name, component_suffix)

            config_path = None
            if config_dir:
                config_path = "{}/{}.json".format(config_dir, test_name)

            test_rule = _wasi_conformance_test_p1 if wasi_version == "wasm32-wasip1" else _wasi_conformance_test
            test_rule(
                name = target_name,
                component = component_target,
                adapter = adapter,
                wasi_version = wasi_version,
                config = config_path,
                runtime = runtime,
                runtime_env_var = runtime_env_var,
                labels = [name, suite_name] + labels,
            )
            all_tests.append(":" + target_name)
            suite_tests.append(":" + target_name)

        if suite_tests:
            native.test_suite(
                name = "{}_{}".format(name, suite_name),
                tests = suite_tests,
            )

    native.test_suite(name = name, tests = all_tests)
