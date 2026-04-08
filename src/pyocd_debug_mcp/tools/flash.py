"""Flash programming tools."""

from __future__ import annotations

import logging
from pathlib import Path

from pyocd.flash.eraser import FlashEraser

from ..session_manager import session_mgr

logger = logging.getLogger(__name__)


def program(file_path: str, erase: bool = True) -> dict:
    """Program a firmware file to the target flash.

    Supports .hex, .bin, and .elf formats. For best compatibility with
    armclang-compiled firmware, use .hex format (avoids ELF segment issues).

    When programming a .elf file, automatically attaches it for symbol
    resolution after successful programming.

    Args:
        file_path: Path to the firmware file.
        erase: Whether to erase before programming (default True).
    """
    result = session_mgr.flash_program(file_path, erase=erase)

    # Auto-attach ELF for symbol resolution
    path = Path(file_path)
    if path.suffix.lower() in (".elf", ".axf"):
        try:
            session_mgr.attach_elf(str(path))
            result["elf_auto_attached"] = True
            logger.info("Auto-attached ELF after flash: %s", path.name)
        except Exception as e:
            result["elf_auto_attached"] = False
            result["elf_attach_error"] = str(e)
            logger.warning("Auto-attach ELF failed: %s", e)

    return result


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


def verify(file_path: str, base_address: int | None = None) -> dict:
    """Verify Flash content matches a firmware file.

    Reads Flash contents and compares segment by segment against the source
    file. Supports .hex, .bin, and .elf formats.

    Args:
        file_path: Path to the firmware file to verify against.
        base_address: Base address for .bin files (default: 0x00000000).
                      Ignored for .hex and .elf which carry address info.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Firmware file not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix not in (".hex", ".bin", ".elf", ".axf"):
        raise ValueError(f"Unsupported format: {suffix}. Use .hex, .bin, .elf, or .axf")

    # Normalize .axf to .elf for segment loading
    load_suffix = ".elf" if suffix == ".axf" else suffix
    segments = _load_firmware_segments(str(path), load_suffix, base_address)
    if not segments:
        raise ValueError(f"No data segments found in: {file_path}")

    target = session_mgr.target
    total_bytes = sum(len(data) for _, data in segments)
    verified_bytes = 0

    for seg_addr, seg_data in segments:
        chunk_size = 1024
        for offset in range(0, len(seg_data), chunk_size):
            chunk = seg_data[offset : offset + chunk_size]
            addr = seg_addr + offset

            flash_data = bytes(target.read_memory_block8(addr, len(chunk)))

            if flash_data != chunk:
                # Find first mismatch byte
                for i, (expected, actual) in enumerate(zip(chunk, flash_data)):
                    if expected != actual:
                        mismatch_addr = addr + i
                        return {
                            "verified": False,
                            "file": str(path),
                            "total_bytes": total_bytes,
                            "verified_bytes": verified_bytes + i,
                            "mismatch_address": f"0x{mismatch_addr:08X}",
                            "expected": f"0x{expected:02X}",
                            "actual": f"0x{actual:02X}",
                        }

            verified_bytes += len(chunk)

    return {
        "verified": True,
        "file": str(path),
        "total_bytes": total_bytes,
        "segments": len(segments),
    }


def _load_firmware_segments(
    file_path: str, suffix: str, base_address: int | None
) -> list[tuple[int, bytes]]:
    """Load firmware file into (address, data) segments."""
    if suffix == ".hex":
        from intelhex import IntelHex

        ih = IntelHex(file_path)
        segments = []
        for start, end in ih.segments():
            data = bytes(ih.tobinarray(start=start, size=end - start))
            segments.append((start, data))
        return segments

    elif suffix == ".bin":
        base = base_address if base_address is not None else 0x00000000
        data = Path(file_path).read_bytes()
        return [(base, data)]

    elif suffix == ".elf":
        from elftools.elf.elffile import ELFFile

        segments = []
        with open(file_path, "rb") as f:
            elf = ELFFile(f)
            for seg in elf.iter_segments():
                if seg.header["p_type"] == "PT_LOAD" and seg.header["p_filesz"] > 0:
                    addr = seg.header["p_paddr"]
                    data = seg.data()[: seg.header["p_filesz"]]
                    segments.append((addr, data))
        return segments

    return []
