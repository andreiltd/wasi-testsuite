"""Download rules for WASI runtime binaries.

Follows the same pattern as wasmono's toolchain downloads: a releases dict
maps version -> platform -> {url, shasum}, and a download macro fetches the
right archive via http_archive.

Wasmtime is already provided by wasmono and does not need to be defined here.
"""

load("@wasmono//toolchains/wasm:host.bzl", "host_arch", "host_os")
load(":releases.bzl", "WAMR_RELEASES", "WASMEDGE_RELEASES", "WASMTIME_RELEASES", "WAZERO_RELEASES")

# ---------------------------------------------------------------------------
# Provider and rules
# ---------------------------------------------------------------------------

WasiRuntimeInfo = provider(
    fields = {
        "name": provider_field(str),
        "binary": provider_field(Artifact),
    },
)

def _wasi_runtime_distribution_impl(ctx: AnalysisContext) -> list[Provider]:
    dist_output = ctx.attrs.dist[DefaultInfo].default_outputs[0]

    if ctx.attrs.prefix:
        binary = dist_output.project(ctx.attrs.prefix + "/" + ctx.attrs.binary_path + ctx.attrs.suffix)
    else:
        binary = dist_output.project(ctx.attrs.binary_path + ctx.attrs.suffix)

    run = cmd_args(
        [binary],
        hidden = [
            ctx.attrs.dist[DefaultInfo].default_outputs,
            ctx.attrs.dist[DefaultInfo].other_outputs,
        ],
    )

    return [
        DefaultInfo(default_output = binary),
        RunInfo(args = run),
        WasiRuntimeInfo(
            name = ctx.attrs.runtime_name,
            binary = binary,
        ),
    ]

_wasi_runtime_distribution = rule(
    impl = _wasi_runtime_distribution_impl,
    attrs = {
        "dist": attrs.dep(providers = [DefaultInfo]),
        "runtime_name": attrs.string(),
        "binary_path": attrs.string(),
        "prefix": attrs.string(default = ""),
        "suffix": attrs.string(default = ""),
        "lib_dir": attrs.string(default = ""),
    },
)

# ---------------------------------------------------------------------------
# Download macros
# ---------------------------------------------------------------------------

def _download_runtime(name, releases, version, runtime_name):
    arch = host_arch()
    os = host_os()
    platform = "{}-{}".format(arch, os)

    if version not in releases:
        fail("Unknown {} version '{}'. Available: {}".format(
            runtime_name,
            version,
            ", ".join(releases.keys()),
        ))

    ver = releases[version]
    if platform not in ver:
        return False

    info = ver[platform]

    archive_name = name + "-archive"
    archive_kwargs = {
        "name": archive_name,
        "urls": [info["url"]],
    }
    if info.get("shasum"):
        archive_kwargs["sha256"] = info["shasum"]

    native.http_archive(**archive_kwargs)

    _wasi_runtime_distribution(
        name = name,
        dist = ":" + archive_name,
        runtime_name = runtime_name,
        binary_path = info["binary"],
        prefix = info.get("prefix", ""),
        lib_dir = info.get("lib_dir", ""),
        suffix = ".exe" if os == "windows" else "",
        visibility = ["PUBLIC"],
    )
    return True

def download_wasmedge(name, version = "0.16.1"):
    """Download a prebuilt WasmEdge release."""
    return _download_runtime(name, WASMEDGE_RELEASES, version, "wasmedge")

def download_wazero(name, version = "1.11.0"):
    """Download a prebuilt wazero release."""
    return _download_runtime(name, WAZERO_RELEASES, version, "wazero")

def download_wamr(name, version = "2.4.4"):
    """Download a prebuilt WAMR (iwasm) release."""
    return _download_runtime(name, WAMR_RELEASES, version, "wamr")

def download_wasmtime_runtime(name, version = "43.0.0"):
    """Download a prebuilt wasmtime release for conformance testing."""
    return _download_runtime(name, WASMTIME_RELEASES, version, "wasmtime")
