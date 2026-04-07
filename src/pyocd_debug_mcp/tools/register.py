"""Register read/write tools."""

from __future__ import annotations

import struct

from ..session_manager import session_mgr

# Standard Cortex-M core registers
CORE_REGISTERS = [
    "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7",
    "r8", "r9", "r10", "r11", "r12",
    "sp", "lr", "pc", "xpsr",
    "msp", "psp",
    "control", "faultmask", "basepri", "primask",
]

# FPU registers (if available)
FPU_REGISTERS = [f"s{i}" for i in range(32)] + ["fpscr"]


def read_register(name: str) -> dict:
    """Read a single core register by name."""
    target = session_mgr.target
    name_lower = name.lower()
    try:
        value = target.read_core_register(name_lower)
        return {"register": name_lower, "value": f"0x{value:08X}", "decimal": value}
    except Exception as e:
        raise ValueError(f"Failed to read register '{name}': {e}")


def write_register(name: str, value: int) -> dict:
    """Write a value to a core register."""
    target = session_mgr.target
    name_lower = name.lower()
    try:
        target.write_core_register(name_lower, value)
        # Read back to verify
        readback = target.read_core_register(name_lower)
        return {
            "register": name_lower,
            "written": f"0x{value:08X}",
            "readback": f"0x{readback:08X}",
            "verified": readback == value,
        }
    except Exception as e:
        raise ValueError(f"Failed to write register '{name}': {e}")


def read_all_registers(include_fpu: bool = False) -> dict:
    """Read all core registers at once."""
    target = session_mgr.target
    result = {}

    for reg in CORE_REGISTERS:
        try:
            val = target.read_core_register(reg)
            result[reg] = f"0x{val:08X}"
        except Exception:
            result[reg] = "N/A"

    if include_fpu:
        fpu_result = {}
        for reg in FPU_REGISTERS:
            try:
                val = target.read_core_register(reg)
                if reg == "fpscr":
                    # FPSCR may be returned as float; bitcast to get raw IEEE-754 bits
                    if isinstance(val, float):
                        raw = struct.unpack("<I", struct.pack("<f", val))[0]
                    else:
                        raw = int(val)
                    fpu_result[reg] = f"0x{raw:08X}"
                else:
                    fpu_result[reg] = f"{val}"
            except Exception:
                pass
        if fpu_result:
            result["fpu"] = fpu_result

    return result
