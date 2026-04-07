"""SVD peripheral register tools."""

from __future__ import annotations

from ..session_manager import session_mgr


def attach_svd(svd_path: str) -> dict:
    """Attach an SVD file for peripheral register access.

    SVD (System View Description) files describe the peripheral
    registers of a microcontroller, enabling named register access.
    """
    return session_mgr.attach_svd(svd_path)


def list_peripherals() -> dict:
    """List all peripherals defined in the attached SVD file."""
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached. Use pyocd.svd.attach first.")

    peripherals = []
    try:
        # cmsis-svd parser format
        for periph in device.peripherals:
            peripherals.append(
                {
                    "name": periph.name,
                    "description": (periph.description or "").strip(),
                    "base_address": f"0x{periph.base_address:08X}",
                    "register_count": len(periph.registers) if periph.registers else 0,
                }
            )
    except AttributeError:
        # Fallback XML format
        for periph in device.findall(".//peripheral"):
            name = periph.findtext("name", "")
            desc = periph.findtext("description", "").strip()
            base = periph.findtext("baseAddress", "0x0")
            regs = periph.findall(".//register")
            peripherals.append(
                {
                    "name": name,
                    "description": desc,
                    "base_address": base,
                    "register_count": len(regs),
                }
            )

    return {"peripherals": peripherals, "count": len(peripherals)}


def list_registers(peripheral_name: str) -> dict:
    """List all registers of a specific peripheral."""
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached. Use pyocd.svd.attach first.")

    periph = _find_peripheral(device, peripheral_name)
    if periph is None:
        raise ValueError(f"Peripheral not found: {peripheral_name}")

    registers = []
    try:
        base_addr = periph.base_address
        for reg in periph.registers or []:
            registers.append(
                {
                    "name": reg.name,
                    "description": (reg.description or "").strip(),
                    "address_offset": f"0x{reg.address_offset:X}",
                    "absolute_address": f"0x{base_addr + reg.address_offset:08X}",
                    "size": reg.size,
                    "reset_value": f"0x{reg.reset_value:X}" if reg.reset_value else "N/A",
                }
            )
    except AttributeError:
        # XML fallback
        base_str = periph.findtext("baseAddress", "0x0")
        base_addr = int(base_str, 0)
        for reg in periph.findall(".//register"):
            name = reg.findtext("name", "")
            offset_str = reg.findtext("addressOffset", "0x0")
            offset = int(offset_str, 0)
            registers.append(
                {
                    "name": name,
                    "description": reg.findtext("description", "").strip(),
                    "address_offset": offset_str,
                    "absolute_address": f"0x{base_addr + offset:08X}",
                }
            )

    return {"peripheral": peripheral_name, "registers": registers, "count": len(registers)}


def read_register(peripheral_name: str, register_name: str) -> dict:
    """Read a peripheral register value by name."""
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached.")

    target = session_mgr.target
    addr = _resolve_register_address(device, peripheral_name, register_name)

    value = target.read32(addr)
    result = {
        "peripheral": peripheral_name,
        "register": register_name,
        "address": f"0x{addr:08X}",
        "value": f"0x{value:08X}",
        "binary": f"0b{value:032b}",
    }

    # Decode fields if available
    fields = _get_register_fields(device, peripheral_name, register_name)
    if fields:
        decoded = {}
        for f in fields:
            mask = ((1 << f["width"]) - 1) << f["offset"]
            field_val = (value & mask) >> f["offset"]
            decoded[f["name"]] = {
                "value": field_val,
                "bits": f"[{f['offset'] + f['width'] - 1}:{f['offset']}]",
                "description": f.get("description", ""),
            }
        result["fields"] = decoded

    return result


def write_register(peripheral_name: str, register_name: str, value: int) -> dict:
    """Write a value to a peripheral register."""
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached.")

    target = session_mgr.target
    addr = _resolve_register_address(device, peripheral_name, register_name)

    target.write32(addr, value & 0xFFFFFFFF)
    readback = target.read32(addr)

    return {
        "peripheral": peripheral_name,
        "register": register_name,
        "address": f"0x{addr:08X}",
        "written": f"0x{value:08X}",
        "readback": f"0x{readback:08X}",
    }


def _find_peripheral(device, name: str):
    """Find a peripheral by name (case-insensitive)."""
    try:
        for p in device.peripherals:
            if p.name.upper() == name.upper():
                return p
    except AttributeError:
        for p in device.findall(".//peripheral"):
            if p.findtext("name", "").upper() == name.upper():
                return p
    return None


def _resolve_register_address(device, periph_name: str, reg_name: str) -> int:
    """Resolve the absolute address of a named register."""
    periph = _find_peripheral(device, periph_name)
    if periph is None:
        raise ValueError(f"Peripheral not found: {periph_name}")

    try:
        base = periph.base_address
        for reg in periph.registers or []:
            if reg.name.upper() == reg_name.upper():
                return base + reg.address_offset
    except AttributeError:
        base_str = periph.findtext("baseAddress", "0x0")
        base = int(base_str, 0)
        for reg in periph.findall(".//register"):
            if reg.findtext("name", "").upper() == reg_name.upper():
                offset = int(reg.findtext("addressOffset", "0x0"), 0)
                return base + offset

    raise ValueError(f"Register not found: {periph_name}.{reg_name}")


def _get_register_fields(device, periph_name: str, reg_name: str) -> list[dict]:
    """Get the bit fields of a register for decoding."""
    periph = _find_peripheral(device, periph_name)
    if periph is None:
        return []

    fields = []
    try:
        for reg in periph.registers or []:
            if reg.name.upper() == reg_name.upper():
                for f in reg.fields or []:
                    fields.append(
                        {
                            "name": f.name,
                            "offset": f.bit_offset,
                            "width": f.bit_width,
                            "description": (f.description or "").strip(),
                        }
                    )
                break
    except AttributeError:
        pass

    return fields
