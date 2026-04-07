"""Watchpoint (data breakpoint) management tools.

Watchpoints trigger a halt when a specific memory address is accessed
(read, write, or both). This is the hardware equivalent of "conditional
breakpoints on memory access" — essential for catching wild pointers,
buffer overflows, and unexpected memory writes.
"""

from __future__ import annotations

from pyocd.core.target import Target

from ..session_manager import session_mgr

# Track active watchpoints
_active_watchpoints: dict[int, dict] = {}

_WP_TYPE_MAP = {
    "read": Target.WatchpointType.READ,
    "write": Target.WatchpointType.WRITE,
    "read_write": Target.WatchpointType.READ_WRITE,
    "rw": Target.WatchpointType.READ_WRITE,
}


def set_watchpoint(
    address: int,
    size: int = 4,
    access_type: str = "write",
) -> dict:
    """Set a hardware watchpoint (data breakpoint).

    Args:
        address: Memory address to watch.
        size: Size of the watched region (1, 2, or 4 bytes).
        access_type: "read", "write", or "read_write"/"rw".
    """
    target = session_mgr.target

    wp_type = _WP_TYPE_MAP.get(access_type.lower())
    if wp_type is None:
        raise ValueError(
            f"Invalid access_type: {access_type}. Use 'read', 'write', or 'read_write'."
        )

    success = target.set_watchpoint(address, size, wp_type)
    if success is False:
        raise RuntimeError(
            f"Failed to set watchpoint at 0x{address:08X} (no DWT comparators available?)"
        )

    _active_watchpoints[address] = {
        "address": f"0x{address:08X}",
        "size": size,
        "type": access_type,
    }

    return {
        "status": "set",
        "address": f"0x{address:08X}",
        "size": size,
        "access_type": access_type,
        "total_watchpoints": len(_active_watchpoints),
    }


def clear_watchpoint(address: int) -> dict:
    """Remove a watchpoint at the given address."""
    target = session_mgr.target
    target.remove_watchpoint(address)
    _active_watchpoints.pop(address, None)
    return {
        "status": "cleared",
        "address": f"0x{address:08X}",
        "total_watchpoints": len(_active_watchpoints),
    }


def clear_all_watchpoints() -> dict:
    """Remove all active watchpoints."""
    target = session_mgr.target
    for addr in list(_active_watchpoints.keys()):
        try:
            target.remove_watchpoint(addr)
        except Exception:
            pass
    count = len(_active_watchpoints)
    _active_watchpoints.clear()
    return {"status": "all_cleared", "cleared_count": count}


def list_watchpoints() -> dict:
    """List all active watchpoints."""
    return {
        "watchpoints": list(_active_watchpoints.values()),
        "total": len(_active_watchpoints),
    }
