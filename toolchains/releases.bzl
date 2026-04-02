"""Release metadata for WASI runtime binaries."""

WASMTIME_RELEASES = {
    "43.0.0": {
        "aarch64-linux": {
            "url": "https://github.com/bytecodealliance/wasmtime/releases/download/v43.0.0/wasmtime-v43.0.0-aarch64-linux.tar.xz",
            "shasum": "1cbec3240f7ee7a7d4bd5bc6248e66035f53d31cdb987bca8a57cb129bc539d9",
            "prefix": "wasmtime-v43.0.0-aarch64-linux",
            "binary": "wasmtime",
        },
        "aarch64-macos": {
            "url": "https://github.com/bytecodealliance/wasmtime/releases/download/v43.0.0/wasmtime-v43.0.0-aarch64-macos.tar.xz",
            "shasum": "abee7cf0f459f189b8a27f41bc3f645c0569198fdc52bc87fbe0a3b5bb83074f",
            "prefix": "wasmtime-v43.0.0-aarch64-macos",
            "binary": "wasmtime",
        },
        "x86_64-linux": {
            "url": "https://github.com/bytecodealliance/wasmtime/releases/download/v43.0.0/wasmtime-v43.0.0-x86_64-linux.tar.xz",
            "shasum": "e75a4933253fbc7b027c670b699490f163e3c86784f1db66581ae80fc0eb652c",
            "prefix": "wasmtime-v43.0.0-x86_64-linux",
            "binary": "wasmtime",
        },
        "x86_64-macos": {
            "url": "https://github.com/bytecodealliance/wasmtime/releases/download/v43.0.0/wasmtime-v43.0.0-x86_64-macos.tar.xz",
            "shasum": "57b4cf9de7f2f250ca6f5d14e0f1d063e19766add3842b7c888260a746e9ca51",
            "prefix": "wasmtime-v43.0.0-x86_64-macos",
            "binary": "wasmtime",
        },
        "x86_64-windows": {
            "url": "https://github.com/bytecodealliance/wasmtime/releases/download/v43.0.0/wasmtime-v43.0.0-x86_64-windows.zip",
            "shasum": "3d8b9dcfadbd7317a65b981d8a197f5dfd2373cbd5c7f6c86bd5287ce90c719b",
            "prefix": "wasmtime-v43.0.0-x86_64-windows",
            "binary": "wasmtime",
        },
    },
}

WASMEDGE_RELEASES = {
    "0.16.1": {
        "x86_64-linux": {
            "url": "https://github.com/WasmEdge/WasmEdge/releases/download/0.16.1/WasmEdge-0.16.1-manylinux_2_28_x86_64.tar.gz",
            "shasum": "43756d546b580fa8cd874190ab1abc868de80a00c80551ae4d1d359d5f9628bc",
            "binary": "bin/wasmedge",
            "lib_dir": "lib64",
        },
    },
}

WAZERO_RELEASES = {
    "1.11.0": {
        "x86_64-linux": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_linux_amd64.tar.gz",
            "shasum": "cb61ba01f493f889180e7a79b1683313dc5fdabf7e63a62fee7154085ffac9f5",
            "binary": "wazero",
        },
        "aarch64-macos": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_darwin_arm64.tar.gz",
            "shasum": "69a90e1860ae90dbdda881c929c4cdee7a2171eab1d0cb8f7fc7b76c6d7d79d0",
            "binary": "wazero",
        },
        "x86_64-macos": {
            "url": "https://github.com/wazero/wazero/releases/download/v1.11.0/wazero_1.11.0_darwin_amd64.tar.gz",
            "shasum": "a53a9cb3d22d62035c4571991e0c6f910380211c178e6a595dd8503669ed312b",
            "binary": "wazero",
        },
    },
}

WAMR_RELEASES = {
    "2.4.4": {
        "x86_64-linux": {
            "url": "https://github.com/bytecodealliance/wasm-micro-runtime/releases/download/WAMR-2.4.4/iwasm-2.4.4-x86_64-ubuntu-22.04.tar.gz",
            "shasum": "ec60ff8daed26319dfc4371843c56ac2dfadd20e2218cbbca97aecb8b390b7a8",
            "binary": "iwasm",
        },
    },
}
