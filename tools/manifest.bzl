"""Buck2 rules for generating a wasi-testsuite manifest and dist archive.

Usage in BUCK:

    load("//tools:manifest.bzl", "wasi_manifest", "wasi_dist")

    wasi_manifest(
        name = "manifest",
        suites = { ... },
    )

    wasi_dist(
        name = "dist",
        manifest = ":manifest",
        components = { "wasm/wasm32-wasip1/lseek.component.wasm": "//tests/c:lseek_component", ... },
        configs = { "configs/c/lseek.json": "tests/c/src/lseek.json", ... },
        fixtures = { "fixtures/fs-tests.dir": "tests/c/src/fs-tests.dir", ... },
    )
"""

def _wasi_manifest_impl(ctx: AnalysisContext) -> list[Provider]:
    output = ctx.actions.declare_output("manifest.json")
    tests_json = ctx.actions.declare_output("_tests.json")

    entries = []
    for suite_name, suite in ctx.attrs.suites.items():
        wasi_version = suite.get("wasi_version", "wasm32-wasip1")
        config_dir = suite.get("config_dir", None)
        for name in suite["tests"]:
            entry = {
                "name": name,
                "suite": suite_name,
                "wasi_version": wasi_version,
            }
            wasm_ext = suite.get("wasm_ext", ".component.wasm")
            entry["wasm"] = "wasm/{}/{}{}".format(suite_name, name, wasm_ext)
            if config_dir:
                entry["config_dir"] = config_dir
            entries.append(entry)

    ctx.actions.write_json(tests_json, entries)

    ctx.actions.run(
        cmd_args(
            "python3",
            ctx.attrs._generate_script,
            "--tests-json",
            tests_json,
            "--base-dir",
            ".",
            "--output",
            output.as_output(),
        ),
        category = "generate_manifest",
        local_only = True,
    )

    return [DefaultInfo(default_output = output)]

wasi_manifest = rule(
    impl = _wasi_manifest_impl,
    attrs = {
        "suites": attrs.dict(
            key = attrs.string(),
            value = attrs.dict(
                key = attrs.string(),
                value = attrs.any(),
            ),
            doc = "Dict of suite_name -> {wasi_version, config_dir?, tests: [name, ...]}",
        ),
        "_generate_script": attrs.source(
            default = "//tools:generate_manifest.py",
        ),
    },
    doc = "Generate a wasi-testsuite manifest.json listing all tests and their metadata.",
)

def _wasi_dist_impl(ctx: AnalysisContext) -> list[Provider]:
    """Package manifest + components + configs + fixtures into a .tar.gz."""
    tarball = ctx.actions.declare_output("wasi-testsuite.tar.gz")
    staging = ctx.actions.declare_output("_staging/wasi-testsuite", dir = True)

    manifest_file = ctx.attrs.manifest[DefaultInfo].default_outputs[0]

    # Build src:dst argument list
    items = []
    for rel_path, dep in ctx.attrs.components.items():
        src = dep[DefaultInfo].default_outputs[0]
        items.append(cmd_args(src, format = "{}:" + rel_path))

    for rel_path, src in ctx.attrs.fixtures.items():
        items.append(cmd_args(src, format = "{}:" + rel_path))

    cmd = cmd_args(
        "python3",
        ctx.attrs._package_script,
        "--staging",
        staging.as_output(),
        "--output",
        tarball.as_output(),
        "--manifest",
        manifest_file,
    )

    # Pass config_dir specs for auto-discovery
    for suite_name, config_dir in ctx.attrs.config_dirs.items():
        cmd.add("--config-dir", "{}:{}".format(suite_name, config_dir))

    for item in items:
        cmd.add(item)

    ctx.actions.run(cmd, category = "dist", local_only = True)

    return [DefaultInfo(default_output = tarball)]

wasi_dist = rule(
    impl = _wasi_dist_impl,
    attrs = {
        "manifest": attrs.dep(
            doc = "The manifest target (wasi_manifest output)",
        ),
        "components": attrs.dict(
            key = attrs.string(),
            value = attrs.dep(),
            default = {},
            doc = "Dict of 'wasm/<wasi_version>/<name>.component.wasm' -> component dep",
        ),
        "config_dirs": attrs.dict(
            key = attrs.string(),
            value = attrs.string(),
            default = {},
            doc = "Dict of 'suite_name' -> 'config_dir_path' for auto-discovering test configs",
        ),
        "fixtures": attrs.dict(
            key = attrs.string(),
            value = attrs.string(),
            default = {},
            doc = "Dict of 'fixtures/<dir>' -> path to source dir (relative to repo root)",
        ),
        "_package_script": attrs.source(
            default = "//tools:package_dist.py",
        ),
    },
    doc = "Package the wasi-testsuite into a distributable .tar.gz archive.",
)

def manifest_suites(suites):
    """Strip component_prefix/suffix from suite defs and add wasm_ext for the manifest rule."""
    result = {}
    for k, v in suites.items():
        suite = {kk: vv for kk, vv in v.items() if kk not in ("component_prefix", "component_suffix", "fixture_dir")}
        suffix = v.get("component_suffix", "")
        suite["wasm_ext"] = ".wasm" if not suffix else ".component.wasm"
        result[k] = suite
    return result

def dist_components(suites):
    """Build the components dict from suite definitions."""
    result = {}

    for suite_name, suite in suites.items():
        prefix = suite["component_prefix"]
        suffix = suite["component_suffix"]
        for t in suite["tests"]:
            ext = ".wasm" if not suffix else ".component.wasm"
            result["wasm/{}/{}{}".format(suite_name, t, ext)] = "{}:{}{}".format(prefix, t, suffix)

    return result

def dist_fixtures(suites):
    """Build fixture dirs mapping from suites that have a fixture_dir."""
    result = {}
    for suite_name, suite in suites.items():
        fixture_dir = suite.get("fixture_dir")
        if fixture_dir:
            result["wasm/{}/fs-tests.dir".format(suite_name)] = fixture_dir
    return result

def dist_config_dirs(suites):
    """Build config_dirs mapping from suite definitions."""
    return {k: v["config_dir"] for k, v in suites.items() if "config_dir" in v}
