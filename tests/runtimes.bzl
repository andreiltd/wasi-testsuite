"""Platform-aware runtime configuration for conformance tests."""

load("@wasmono//toolchains/wasm:host.bzl", "host_arch", "host_os")

# Platforms where each runtime has prebuilt binaries (must match releases.bzl)
_RUNTIME_PLATFORMS = {
    "wasmedge": ["x86_64-linux"],
    "wazero": ["x86_64-linux", "aarch64-macos", "x86_64-macos"],
    "wamr": ["x86_64-linux"],
}

_RUNTIME_CONFIG = {
    "wasmedge": ("adapters/wasmedge.py", "toolchains//:wasmedge", "WASMEDGE"),
    "wazero": ("adapters/wazero.py", "toolchains//:wazero", "WAZERO"),
    "wamr": ("adapters/wasm-micro-runtime.py", "toolchains//:wamr", "IWASM"),
}

def available_runtimes():
    """Return list of (name, adapter, target, env_var) for runtimes available on this platform."""
    platform = "{}-{}".format(host_arch(), host_os())
    return [
        (name,) + _RUNTIME_CONFIG[name]
        for name, platforms in _RUNTIME_PLATFORMS.items()
        if platform in platforms
    ]
