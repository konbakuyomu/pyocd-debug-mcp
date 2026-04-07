"""Memory read/write/dump tools."""

from __future__ import annotations

from ..session_manager import session_mgr


def read_memory(address: int, size: int = 4) -> dict:
    """Read memory at the given address.

    Args:
        address: Memory address to read from.
        size: Number of bytes to read (1, 2, or 4 for single access; any for block).
    """
    target = session_mgr.target

    if size == 1:
        value = target.read8(address)
        return {"address": f"0x{address:08X}", "size": 1, "value": f"0x{value:02X}"}
    elif size == 2:
        value = target.read16(address)
        return {"address": f"0x{address:08X}", "size": 2, "value": f"0x{value:04X}"}
    elif size == 4:
        value = target.read32(address)
        return {"address": f"0x{address:08X}", "size": 4, "value": f"0x{value:08X}"}
    else:
        # Block read
        data = target.read_memory_block8(address, size)
        hex_str = " ".join(f"{b:02X}" for b in data)
        return {
            "address": f"0x{address:08X}",
            "size": size,
            "hex": hex_str,
            "bytes": list(data),
        }


def write_memory(address: int, value: int, size: int = 4) -> dict:
    """Write a value to memory.

    Args:
        address: Memory address to write to.
        value: Value to write.
        size: Access size (1, 2, or 4 bytes).
    """
    target = session_mgr.target

    if size == 1:
        target.write8(address, value & 0xFF)
    elif size == 2:
        target.write16(address, value & 0xFFFF)
    elif size == 4:
        target.write32(address, value & 0xFFFFFFFF)
    else:
        raise ValueError(f"Unsupported write size: {size}. Use 1, 2, or 4.")

    # Read back to verify (peripheral registers may be volatile)
    readback = read_memory(address, size)
    written_hex = f"0x{value:0{size*2}X}"
    is_peripheral = address >= 0x40000000
    verified = readback["value"] == written_hex
    result = {
        "address": f"0x{address:08X}",
        "written": written_hex,
        "readback": readback["value"],
        "verified": verified,
    }
    if is_peripheral and not verified:
        result["note"] = (
            "Peripheral register: readback differs from written value. "
            "This is normal for volatile/auto-clear registers (e.g. interrupt flags)."
        )
    return result


def write_memory_block(address: int, data: list[int]) -> dict:
    """Write a block of bytes to memory."""
    target = session_mgr.target
    target.write_memory_block8(address, bytearray(data))
    return {
        "address": f"0x{address:08X}",
        "size": len(data),
        "status": "written",
    }


def dump_memory(address: int, length: int = 256, width: int = 16) -> dict:
    """Dump memory in a hex dump format.

    Args:
        address: Start address.
        length: Number of bytes to dump.
        width: Bytes per line (default 16).
    """
    target = session_mgr.target
    data = target.read_memory_block8(address, length)

    lines = []
    for offset in range(0, length, width):
        chunk = data[offset : offset + width]
        addr_str = f"0x{(address + offset):08X}"
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{addr_str}: {hex_part:<{width * 3}} |{ascii_part}|")

    return {
        "address": f"0x{address:08X}",
        "length": length,
        "dump": "\n".join(lines),
    }
