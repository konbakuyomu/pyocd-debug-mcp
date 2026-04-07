"""ELF file support tools: symbol lookup and info."""

from __future__ import annotations

from pathlib import Path

from ..session_manager import session_mgr


def attach_elf(elf_path: str) -> dict:
    """Attach an ELF file for symbol resolution.

    This enables using function names for breakpoints and provides
    richer debug information.
    """
    return session_mgr.attach_elf(elf_path)


def lookup_symbol(name: str) -> dict:
    """Look up a symbol (function/variable) address by name."""
    provider = session_mgr.elf_provider
    if provider is None:
        raise RuntimeError("No ELF file attached. Use pyocd.elf.attach first.")

    addr = provider.get_symbol_value(name)
    if addr is None:
        raise ValueError(f"Symbol not found: {name}")

    return {"symbol": name, "address": f"0x{addr:08X}"}


def list_symbols(filter_text: str = "", limit: int = 50) -> dict:
    """List symbols from the attached ELF file.

    Args:
        filter_text: Optional text to filter symbol names (case-insensitive).
        limit: Maximum number of symbols to return.
    """
    provider = session_mgr.elf_provider
    if provider is None:
        raise RuntimeError("No ELF file attached. Use pyocd.elf.attach first.")

    # Get ELF path from session info (target.elf returns ELFBinaryFile, not path)
    info = session_mgr.info
    if info is None or info.elf_path is None:
        raise RuntimeError("ELF file path not available.")

    symbols = []
    try:
        from elftools.elf.elffile import ELFFile

        with open(info.elf_path, "rb") as f:
            ef = ELFFile(f)
            symtab = ef.get_section_by_name(".symtab")
            if symtab:
                for sym in symtab.iter_symbols():
                    name = sym.name
                    if not name or name.startswith("$"):
                        continue
                    if filter_text and filter_text.lower() not in name.lower():
                        continue
                    # Only include function and object symbols
                    sym_type = sym.entry.st_info.type
                    if sym_type in ("STT_FUNC", "STT_OBJECT"):
                        symbols.append(
                            {
                                "name": name,
                                "address": f"0x{sym.entry.st_value:08X}",
                                "size": sym.entry.st_size,
                                "type": "function" if sym_type == "STT_FUNC" else "variable",
                            }
                        )
                    if len(symbols) >= limit:
                        break
    except Exception as e:
        raise RuntimeError(f"Failed to enumerate symbols: {e}")

    return {"symbols": symbols, "count": len(symbols), "truncated": len(symbols) >= limit}


def address_to_symbol(address: int) -> dict:
    """Resolve an address to its symbol name (function or variable).

    Uses pyOCD's ElfSymbolDecoder for efficient address→symbol reverse lookup.
    Essential for interpreting PC, LR, and stack return addresses during debugging.

    Args:
        address: Memory address to resolve.
    """
    target = session_mgr.target
    if target.elf is None:
        raise RuntimeError("No ELF file attached. Use pyocd.elf.attach first.")

    decoder = target.elf.symbol_decoder
    sym_info = decoder.get_symbol_for_address(address)
    if sym_info is None:
        return {
            "address": f"0x{address:08X}",
            "resolved": False,
            "symbol": None,
        }

    offset = address - sym_info.address
    return {
        "address": f"0x{address:08X}",
        "resolved": True,
        "symbol": sym_info.name,
        "symbol_address": f"0x{sym_info.address:08X}",
        "offset": offset,
        "display": f"{sym_info.name}+0x{offset:X}" if offset else sym_info.name,
        "size": sym_info.size,
        "type": str(sym_info.type),
    }


def get_elf_info() -> dict:
    """Get information about the attached ELF file."""
    info = session_mgr.info
    if info is None or info.elf_path is None:
        return {"status": "no_elf_attached"}

    path = Path(info.elf_path)
    result = {
        "elf_path": str(path),
        "file_name": path.name,
        "file_size": path.stat().st_size,
    }

    try:
        from elftools.elf.elffile import ELFFile

        with open(str(path), "rb") as f:
            ef = ELFFile(f)
            result["arch"] = ef.get_machine_arch()
            result["entry_point"] = f"0x{ef.header.e_entry:08X}"
            result["sections"] = [s.name for s in ef.iter_sections() if s.name]
    except Exception:
        pass

    return result
