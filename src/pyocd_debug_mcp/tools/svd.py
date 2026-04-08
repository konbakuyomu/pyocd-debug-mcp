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


def list_fields(peripheral_name: str, register_name: str) -> dict:
    """List all bit fields of a peripheral register.

    Returns each field's name, bit range, width, and description.
    Useful for understanding register layout before modifying individual fields.
    """
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached. Use pyocd.svd.attach first.")

    fields = _get_register_fields(device, peripheral_name, register_name)
    if not fields:
        raise ValueError(
            f"No fields found for {peripheral_name}.{register_name}. "
            "Ensure SVD was loaded via cmsis-svd (not raw XML fallback)."
        )

    result_fields = []
    for f in sorted(fields, key=lambda x: x["offset"]):
        high = f["offset"] + f["width"] - 1
        result_fields.append(
            {
                "name": f["name"],
                "bits": f"[{high}:{f['offset']}]",
                "width": f["width"],
                "reset_mask": f"0x{((1 << f['width']) - 1) << f['offset']:X}",
                "description": f.get("description", ""),
            }
        )

    return {
        "peripheral": peripheral_name,
        "register": register_name,
        "fields": result_fields,
        "count": len(result_fields),
    }


def set_field(
    peripheral_name: str, register_name: str, field_name: str, value: int | str
) -> dict:
    """Set a single bit field of a peripheral register (read-modify-write).

    Reads the current register value, modifies only the specified field,
    and writes back. This avoids accidentally clearing other fields.

    The *value* parameter accepts either an integer or an enumerated value name
    (case-insensitive).  Use ``_get_field_enums()`` to discover valid names.

    Example: set_field("GPIOA", "MODER", "MODER0", 1)
             set_field("GPIOA", "MODER", "MODER0", "Output")
    """
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached. Use pyocd.svd.attach first.")

    target = session_mgr.target
    addr = _resolve_register_address(device, peripheral_name, register_name)

    fields = _get_register_fields(device, peripheral_name, register_name)
    field_info = None
    for f in fields:
        if f["name"].upper() == field_name.upper():
            field_info = f
            break
    if field_info is None:
        available = [f["name"] for f in fields]
        raise ValueError(
            f"Field '{field_name}' not found in {peripheral_name}.{register_name}. "
            f"Available: {available}"
        )

    offset = field_info["offset"]
    width = field_info["width"]
    max_val = (1 << width) - 1

    # Resolve enum name → integer
    enum_name_used: str | None = None
    if isinstance(value, str):
        enums = _get_field_enums(device, peripheral_name, register_name, field_name)
        matched = None
        for ev in enums:
            if ev["name"].upper() == value.upper():
                matched = ev
                break
        if matched is None:
            available_names = [ev["name"] for ev in enums]
            raise ValueError(
                f"Enum value '{value}' not found for field '{field_name}'. "
                f"Available: {available_names}"
            )
        enum_name_used = matched["name"]
        value = matched["value"]

    if value < 0 or value > max_val:
        raise ValueError(
            f"Value {value} out of range for field '{field_name}' "
            f"(width={width}, max={max_val})"
        )

    # Read-modify-write
    old_val = target.read32(addr)
    mask = max_val << offset
    new_val = (old_val & ~mask) | ((value & max_val) << offset)
    target.write32(addr, new_val)
    readback = target.read32(addr)

    result = {
        "peripheral": peripheral_name,
        "register": register_name,
        "field": field_name,
        "address": f"0x{addr:08X}",
        "old_value": f"0x{old_val:08X}",
        "new_value": f"0x{new_val:08X}",
        "readback": f"0x{readback:08X}",
        "field_value": value,
        "bits": f"[{offset + width - 1}:{offset}]",
        "verified": readback == new_val,
    }
    if enum_name_used:
        result["enum_name"] = enum_name_used
    return result


def update_fields(
    peripheral_name: str, register_name: str, fields: dict[str, int | str]
) -> dict:
    """Set multiple bit fields of a register in a single read-modify-write.

    *fields* maps field names to integer values (or enum name strings).
    All fields are updated atomically in one RMW cycle.

    Example::

        update_fields("GPIOA", "MODER", {"MODER0": 1, "MODER1": 2})
    """
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached.")

    target = session_mgr.target
    addr = _resolve_register_address(device, peripheral_name, register_name)
    all_fields = _get_register_fields(device, peripheral_name, register_name)

    # Build lookup by upper-case name
    field_map = {f["name"].upper(): f for f in all_fields}

    old_val = target.read32(addr)
    new_val = old_val
    updated = []

    for fname, fval in fields.items():
        fi = field_map.get(fname.upper())
        if fi is None:
            raise ValueError(
                f"Field '{fname}' not found in {peripheral_name}.{register_name}. "
                f"Available: {list(field_map.keys())}"
            )
        offset = fi["offset"]
        width = fi["width"]
        max_val = (1 << width) - 1

        enum_name_used = None
        if isinstance(fval, str):
            enums = _get_field_enums(device, peripheral_name, register_name, fname)
            matched = None
            for ev in enums:
                if ev["name"].upper() == fval.upper():
                    matched = ev
                    break
            if matched is None:
                raise ValueError(
                    f"Enum '{fval}' not found for field '{fname}'. "
                    f"Available: {[ev['name'] for ev in enums]}"
                )
            enum_name_used = matched["name"]
            fval = matched["value"]

        if fval < 0 or fval > max_val:
            raise ValueError(
                f"Value {fval} out of range for '{fname}' (width={width}, max={max_val})"
            )
        mask = max_val << offset
        new_val = (new_val & ~mask) | ((fval & max_val) << offset)
        entry = {"field": fi["name"], "value": fval, "bits": f"[{offset + width - 1}:{offset}]"}
        if enum_name_used:
            entry["enum_name"] = enum_name_used
        updated.append(entry)

    target.write32(addr, new_val)
    readback = target.read32(addr)

    return {
        "peripheral": peripheral_name,
        "register": register_name,
        "address": f"0x{addr:08X}",
        "old_value": f"0x{old_val:08X}",
        "new_value": f"0x{new_val:08X}",
        "readback": f"0x{readback:08X}",
        "verified": readback == new_val,
        "fields_updated": updated,
    }


def describe(peripheral_name: str, register_name: str | None = None) -> dict:
    """Return full description of a peripheral or specific register.

    When *register_name* is ``None``, returns peripheral-level info with all
    registers listed (name + description + address).  When given, returns
    register-level detail with all fields and their enumerated values.
    """
    device = session_mgr.svd_device
    if device is None:
        raise RuntimeError("No SVD file attached.")

    periph = _find_peripheral(device, peripheral_name)
    if periph is None:
        raise ValueError(f"Peripheral not found: {peripheral_name}")

    try:
        base = periph.base_address
    except AttributeError:
        base = int(periph.findtext("baseAddress", "0x0"), 0)

    if register_name is None:
        # Peripheral-level description
        regs = []
        try:
            for reg in periph.registers or []:
                regs.append({
                    "name": reg.name,
                    "offset": f"0x{reg.address_offset:X}",
                    "address": f"0x{base + reg.address_offset:08X}",
                    "description": (reg.description or "").strip(),
                })
        except AttributeError:
            pass
        return {
            "peripheral": peripheral_name,
            "base_address": f"0x{base:08X}",
            "description": (getattr(periph, "description", "") or "").strip(),
            "registers": regs,
        }

    # Register-level description with full field + enum detail
    reg_obj = _find_register(periph, register_name)
    if reg_obj is None:
        raise ValueError(f"Register not found: {peripheral_name}.{register_name}")

    reg_fields = []
    try:
        for f in reg_obj.fields or []:
            finfo: dict = {
                "name": f.name,
                "bits": f"[{f.bit_offset + f.bit_width - 1}:{f.bit_offset}]",
                "width": f.bit_width,
                "description": (f.description or "").strip(),
                "access": getattr(f, "access", None),
            }
            if f.enumerated_values:
                finfo["enums"] = [
                    {
                        "name": ev.name,
                        "value": ev.value,
                        "description": (ev.description or "").strip(),
                    }
                    for ev in f.enumerated_values
                    if ev.name is not None and ev.value is not None
                ]
            reg_fields.append(finfo)
    except AttributeError:
        pass

    return {
        "peripheral": peripheral_name,
        "register": register_name,
        "address": f"0x{base + reg_obj.address_offset:08X}",
        "description": (reg_obj.description or "").strip(),
        "size": getattr(reg_obj, "size", 32),
        "reset_value": f"0x{reg_obj.reset_value:X}" if reg_obj.reset_value else "N/A",
        "fields": reg_fields,
    }


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


def _find_register(periph, reg_name: str):
    """Find a register object by name within a peripheral (case-insensitive)."""
    try:
        for reg in periph.registers or []:
            if reg.name.upper() == reg_name.upper():
                return reg
    except AttributeError:
        pass
    return None


def _get_field_enums(
    device, periph_name: str, reg_name: str, field_name: str
) -> list[dict]:
    """Return enumerated values for a specific field.

    Each entry has keys: name, value, description.
    Returns an empty list if the field has no enums.
    """
    periph = _find_peripheral(device, periph_name)
    if periph is None:
        return []

    reg = _find_register(periph, reg_name)
    if reg is None:
        return []

    try:
        for f in reg.fields or []:
            if f.name.upper() == field_name.upper():
                if not f.enumerated_values:
                    return []
                return [
                    {
                        "name": ev.name,
                        "value": ev.value,
                        "description": (ev.description or "").strip(),
                    }
                    for ev in f.enumerated_values
                    if ev.name is not None and ev.value is not None
                ]
    except AttributeError:
        pass
    return []
