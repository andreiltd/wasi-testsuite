"""WASI p1 platform transition.

Like wasmono's wasm_transition but also sets the wasip1 constraint,
allowing the Rust toolchain to select wasm32-wasip1 target triple.
"""

_REFS = {
    "cpu": "config//cpu/constraints:cpu",
    "os": "config//os/constraints:os",
    "wasm32": "config//cpu/constraints:wasm32",
    "wasi": "config//os/constraints:wasi",
    "wasi_version": "//constraints:wasi_version",
    "wasip1": "//constraints:wasip1",
}

def _impl(platform: PlatformInfo, refs: struct) -> PlatformInfo:
    cpu_setting = refs.cpu[ConstraintSettingInfo]
    os_setting = refs.os[ConstraintSettingInfo]
    version_setting = refs.wasi_version[ConstraintSettingInfo]
    wasm32_value = refs.wasm32[ConstraintValueInfo]
    wasi_value = refs.wasi[ConstraintValueInfo]
    wasip1_value = refs.wasip1[ConstraintValueInfo]

    new_constraints = {}
    for setting_label, value in platform.configuration.constraints.items():
        if (setting_label != cpu_setting.label and
            setting_label != os_setting.label and
            setting_label != version_setting.label):
            new_constraints[setting_label] = value

    new_constraints[cpu_setting.label] = wasm32_value
    new_constraints[os_setting.label] = wasi_value
    new_constraints[version_setting.label] = wasip1_value

    return PlatformInfo(
        label = "wasm32-wasip1-transitioned",
        configuration = ConfigurationInfo(
            constraints = new_constraints,
            values = platform.configuration.values,
        ),
    )

wasm_transition_p1 = transition(impl = _impl, refs = _REFS)
