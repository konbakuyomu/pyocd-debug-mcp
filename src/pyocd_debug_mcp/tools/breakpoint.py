"""Breakpoint management tools."""

from __future__ import annotations

from ..session_manager import session_mgr


# Track active breakpoints (pyocd doesn't provide a list API)
_active_breakpoints: dict[int, dict] = {}


def set_breakpoint(address: int | None = None, symbol: str | None = None) -> dict:
    """Set a breakpoint at an address or symbol name.

    Args:
        address: Memory address for the breakpoint.
        symbol: Function/symbol name (requires ELF attached).
    """
    target = session_mgr.target

    if symbol is not None:
        provider = session_mgr.elf_provider
        if provider is None:
            raise RuntimeError(
                "No ELF file attached. Use pyocd.elf.attach first to set symbol breakpoints."
            )
        resolved_addr = provider.get_symbol_value(symbol)
        if resolved_addr is None:
            raise ValueError(f"Symbol not found: {symbol}")
        address = resolved_addr

    if address is None:
        raise ValueError("Must specify either 'address' or 'symbol'.")

    # Mask off Thumb bit for display but use original for breakpoint
    bp_addr = address & ~0x01 if address & 0x01 else address

    success = target.set_breakpoint(address)
    if success is False:
        raise RuntimeError(f"Failed to set breakpoint at 0x{bp_addr:08X} (no HW slots?)")

    _active_breakpoints[bp_addr] = {
        "address": f"0x{bp_addr:08X}",
        "symbol": symbol,
    }

    return {
        "status": "set",
        "address": f"0x{bp_addr:08X}",
        "symbol": symbol,
        "total_breakpoints": len(_active_breakpoints),
    }


def clear_breakpoint(address: int | None = None, symbol: str | None = None) -> dict:
    """Remove a breakpoint."""
    target = session_mgr.target

    if symbol is not None:
        provider = session_mgr.elf_provider
        if provider is None:
            raise RuntimeError("No ELF file attached.")
        address = provider.get_symbol_value(symbol)
        if address is None:
            raise ValueError(f"Symbol not found: {symbol}")

    if address is None:
        raise ValueError("Must specify either 'address' or 'symbol'.")

    bp_addr = address & ~0x01 if address & 0x01 else address
    target.remove_breakpoint(address)
    _active_breakpoints.pop(bp_addr, None)

    return {
        "status": "cleared",
        "address": f"0x{bp_addr:08X}",
        "total_breakpoints": len(_active_breakpoints),
    }


def clear_all_breakpoints() -> dict:
    """Remove all active breakpoints."""
    target = session_mgr.target
    for addr in list(_active_breakpoints.keys()):
        try:
            target.remove_breakpoint(addr)
        except Exception:
            pass
    count = len(_active_breakpoints)
    _active_breakpoints.clear()
    return {"status": "all_cleared", "cleared_count": count}


def list_breakpoints() -> dict:
    """List all active breakpoints."""
    return {
        "breakpoints": list(_active_breakpoints.values()),
        "total": len(_active_breakpoints),
    }
