"""Flash programming tools."""

from __future__ import annotations

from pathlib import Path

from pyocd.flash.eraser import FlashEraser

from ..session_manager import session_mgr


def program(file_path: str, erase: bool = True) -> dict:
    """Program a firmware file to the target flash.

    Supports .hex, .bin, and .elf formats. For best compatibility with
    armclang-compiled firmware, use .hex format (avoids ELF segment issues).

    Args:
        file_path: Path to the firmware file.
        erase: Whether to erase before programming (default True).
    """
    return session_mgr.flash_program(file_path, erase=erase)


def erase(chip_erase: bool = True) -> dict:
    """Erase the target flash memory.

    Args:
        chip_erase: If True, performs full chip erase. If False, erases only
                    sectors covered by the last programmed firmware.
    """
    session = session_mgr.session
    eraser = FlashEraser(session, FlashEraser.Mode.CHIP if chip_erase else FlashEraser.Mode.SECTOR)
    eraser.erase()
    return {"status": "erased", "mode": "chip" if chip_erase else "sector"}
