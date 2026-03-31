"""Download rules for WASI runtime binaries.

Follows the same pattern as wasmono's toolchain downloads: a releases dict
maps version -> platform -> {url, shasum}, and a download macro fetches the
right archive via http_archive.

Wasmtime is already provided by wasmono and does not need to be defined here.
"""

load("@wasmono//toolchains/wasm:host.bzl", "host_arch", "host_os")

# ---------------------------------------------------------------------------
# Release metadata
# ---------------------------------------------------------------------------

WASMEDGE_RELEASES = {
    "0.16.1": {
        "x86_64-linux": {
            "url": "https://github.com/WasmEdge/WasmEdge/releases/download/0.16.1/WasmEdge-0.16.1-manylinux_2_28_x86_64.tar.gz",
            "shasum": "",
            "prefix": "WasmEdge-0.16.1-Linux",
            "binary": "bin/wasmedge",
        },
        "aarch64-linux": {
            "url": "https://github.com/WasmEdge/WasmEdge/releases/download/0.16.1/WasmEdge-0.16.1-manylinux_2_28_aarch64.tar.gz",
            "shasum": "",
            "prefix": "WasmEdge-0.16.1-Linux",
            "binary": "bin/wasmedge",
        },
        "x86_64-macos": {
            "url": "https://github.com/WasmEdge/WasmEdge/releases/download/0.16.1/WasmEdge-0.16.1-darwin_x86_64.tar.gz",
            "shasum": "",
            "prefix": "WasmEdge-0.16.1-Darwin",
            "binary": "bin/wasmedge",
        },
        "aarch64-macos": {
            "url": "https://github.com/WasmEdge/WasmEdge/releases/download/0.16.1/WasmEdge-0.16.1-darwin_arm64.tar.gz",
            "shasum": "",
            "prefix": "WasmEdge-0.16.1-Darwin",
            "binary": "bin/wasmedge",
        },
    },
}

WAZERO_RELEASES = {
    "1.11.0": {
        "x86_64-linux": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_linux_amd64.tar.gz",
            "shasum": "",
            "binary": "wazero",
        },
        "aarch64-linux": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_linux_arm64.tar.gz",
            "shasum": "",
            "binary": "wazero",
        },
        "x86_64-macos": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_darwin_amd64.tar.gz",
            "shasum": "",
            "binary": "wazero",
        },
        "aarch64-macos": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_darwin_arm64.tar.gz",
            "shasum": "",
            "binary": "wazero",
        },
    },
}

WAMR_RELEASES = {
    "2.4.4": {
        "x86_64-linux": {
            "url": "https://github.com/bytecodealliance/wasm-micro-runtime/releases/download/WAMR-2.4.4/iwasm-2.4.4-x86_64-ubuntu-22.04.tar.gz",
            "shasum": "",
            "binary": "iwasm",
        },
        "x86_64-macos": {
            "url": "https://github.com/bytecodealliance/wasm-micro-runtime/releases/download/WAMR-2.4.4/iwasm-2.4.4-x86_64-macos-13.tar.gz",
            "shasum": "",
            "binary": "iwasm",
        },
    },
}

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
        src = dist_output.project(ctx.attrs.prefix + "/" + ctx.attrs.binary_path)
    else:
        src = dist_output.project(ctx.attrs.binary_path)

    dst = ctx.actions.declare_output(ctx.attrs.runtime_name + ctx.attrs.suffix)
    ctx.actions.copy_file(dst.as_output(), src)

    binary = cmd_args(
        [dst],
        hidden = [
            ctx.attrs.dist[DefaultInfo].default_outputs,
            ctx.attrs.dist[DefaultInfo].other_outputs,
        ],
    )

    return [
        DefaultInfo(default_output = dst),
        RunInfo(args = binary),
        WasiRuntimeInfo(
            name = ctx.attrs.runtime_name,
            binary = dst,
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
        # Runtime not available on this platform, create a stub
        return False

    info = ver[platform]

    archive_name = name + "-archive"
    native.http_archive(
        name = archive_name,
        urls = [info["url"]],
        sha256 = info.get("shasum", ""),
    )

    _wasi_runtime_distribution(
        name = name,
        dist = ":" + archive_name,
        runtime_name = runtime_name,
        binary_path = info["binary"],
        prefix = info.get("prefix", ""),
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
