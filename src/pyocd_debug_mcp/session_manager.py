"""
pyocd-debug-mcp session manager.

Manages the lifecycle of pyOCD debug sessions, ensuring only one session
is active at a time and providing safe access to the target.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pyocd.core.helpers import ConnectHelper
from pyocd.core.session import Session
from pyocd.core.target import Target
from pyocd.debug.elf.symbols import ELFSymbolProvider
from pyocd.flash.file_programmer import FileProgrammer

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about the current debug session."""

    probe_id: str
    target_type: str
    frequency: int
    elf_path: Optional[str] = None
    svd_path: Optional[str] = None


class SessionManager:
    """Singleton manager for pyOCD debug sessions.

    Ensures only one session is active at a time, provides safe access
    to the target, and handles cleanup on disconnect.
    """

    _instance: Optional[SessionManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> SessionManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._session: Optional[Session] = None
        self._info: Optional[SessionInfo] = None
        self._elf_provider: Optional[ELFSymbolProvider] = None
        self._svd_device = None
        self._initialized = True

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("No active debug session. Call pyocd.session.connect first.")
        return self._session

    @property
    def target(self) -> Target:
        return self.session.target

    @property
    def info(self) -> Optional[SessionInfo]:
        return self._info

    @property
    def elf_provider(self) -> Optional[ELFSymbolProvider]:
        return self._elf_provider

    @property
    def svd_device(self):
        return self._svd_device

    def connect(
        self,
        target_type: str,
        probe_id: Optional[str] = None,
        frequency: int = 4_000_000,
        auto_fix_memory_map: bool = True,
    ) -> SessionInfo:
        """Connect to a debug probe and open a session."""
        if self._session is not None:
            raise RuntimeError(
                "Session already active. Disconnect first with pyocd.session.disconnect."
            )

        options = {
            "frequency": frequency,
            "target_override": target_type,
        }

        kwargs = {"options": options, "return_first": True}
        if probe_id:
            kwargs["unique_id"] = probe_id

        try:
            session = ConnectHelper.session_with_chosen_probe(**kwargs)
            if session is None:
                raise RuntimeError("No debug probe found. Check USB connection.")

            session.open()
            self._session = session

            if auto_fix_memory_map:
                self._fix_peripheral_memory_map()

            self._info = SessionInfo(
                probe_id=session.probe.unique_id or "unknown",
                target_type=target_type,
                frequency=frequency,
            )

            logger.info(
                "Connected to %s via probe %s @ %d Hz",
                target_type,
                self._info.probe_id,
                frequency,
            )
            return self._info

        except Exception:
            self._session = None
            self._info = None
            raise

    def disconnect(self) -> None:
        """Close the current debug session and release the probe."""
        if self._session is None:
            return

        try:
            self._session.close()
        except Exception as e:
            logger.warning("Error closing session: %s", e)
        finally:
            self._session = None
            self._info = None
            self._elf_provider = None
            self._svd_device = None
            # Clean up module-level tracking state
            self._cleanup_tool_state()
            logger.info("Session disconnected.")

    @staticmethod
    def _cleanup_tool_state() -> None:
        """Clear module-level mutable state in tool modules on disconnect."""
        try:
            from .tools.breakpoint import _active_breakpoints
            _active_breakpoints.clear()
        except Exception:
            pass
        try:
            from .tools.watchpoint import _active_watchpoints
            _active_watchpoints.clear()
        except Exception:
            pass

    def attach_elf(self, elf_path: str) -> dict:
        """Attach an ELF file for symbol resolution."""
        path = Path(elf_path)
        if not path.exists():
            raise FileNotFoundError(f"ELF file not found: {elf_path}")

        self.target.elf = str(path)
        self._elf_provider = ELFSymbolProvider(self.target.elf)

        if self._info:
            self._info.elf_path = str(path)

        logger.info("ELF attached: %s", path.name)
        return {"elf_path": str(path), "status": "attached"}

    def attach_svd(self, svd_path: str) -> dict:
        """Attach an SVD file for peripheral register access."""
        path = Path(svd_path)
        if not path.exists():
            raise FileNotFoundError(f"SVD file not found: {svd_path}")

        try:
            from cmsis_svd.parser import SVDParser

            parser = SVDParser.for_xml_file(str(path))
            self._svd_device = parser.get_device()
        except ImportError:
            # Fallback: try pyocd's built-in SVD support if available
            from xml.etree import ElementTree

            tree = ElementTree.parse(str(path))
            self._svd_device = tree.getroot()

        if self._info:
            self._info.svd_path = str(path)

        logger.info("SVD attached: %s", path.name)
        return {"svd_path": str(path), "status": "attached"}

    def flash_program(self, file_path: str, erase: bool = True) -> dict:
        """Program a firmware file (hex/bin/elf) to the target."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Firmware file not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in (".hex", ".bin", ".elf"):
            raise ValueError(f"Unsupported firmware format: {suffix}. Use .hex, .bin, or .elf")

        programmer = FileProgrammer(self.session)
        programmer.program(str(path), erase=erase)

        logger.info("Flash programmed: %s (erase=%s)", path.name, erase)
        return {"file": str(path), "format": suffix, "erase": erase, "status": "programmed"}

    def _fix_peripheral_memory_map(self) -> None:
        """Auto-inject peripheral address space to fix SVD read failures.

        Many CMSIS-Pack .pdsc files only define Flash and RAM regions,
        omitting peripheral address space. This causes GDB/pyOCD to reject
        reads to 0x40000000+ addresses. We add it automatically.
        """
        try:
            from pyocd.core.memory_map import DeviceRegion

            target = self.session.target
            memory_map = target.memory_map

            # Check if peripheral region already exists
            for region in memory_map:
                if hasattr(region, "start") and region.start == 0x40000000:
                    return

            periph_region = DeviceRegion(
                name="Peripheral",
                start=0x40000000,
                end=0x5FFFFFFF,
            )
            memory_map.add_region(periph_region)

            ppb_region = DeviceRegion(
                name="PPB",
                start=0xE0000000,
                end=0xE00FFFFF,
            )
            memory_map.add_region(ppb_region)

            logger.info("Auto-injected peripheral memory regions (0x40000000-0x5FFFFFFF, PPB)")
        except Exception as e:
            logger.warning("Failed to fix peripheral memory map: %s", e)


# Global singleton
session_mgr = SessionManager()
