"""Probe management tools: list and inspect connected debug probes."""

from __future__ import annotations

from pyocd.core.helpers import ConnectHelper
from pyocd.probe.debug_probe import DebugProbe


def list_probes() -> list[dict]:
    """List all connected CMSIS-DAP debug probes."""
    probes = ConnectHelper.get_all_connected_probes(blocking=False)
    result = []
    for p in probes:
        result.append(
            {
                "unique_id": p.unique_id or "unknown",
                "description": p.description or "",
                "vendor_name": getattr(p, "vendor_name", ""),
                "product_name": getattr(p, "product_name", ""),
            }
        )
    return result


def get_probe_info(unique_id: str) -> dict:
    """Get detailed info about a specific probe."""
    probes = ConnectHelper.get_all_connected_probes(blocking=False)
    for p in probes:
        if p.unique_id and unique_id in p.unique_id:
            return {
                "unique_id": p.unique_id,
                "description": p.description or "",
                "vendor_name": getattr(p, "vendor_name", ""),
                "product_name": getattr(p, "product_name", ""),
            }
    raise ValueError(f"Probe not found: {unique_id}")
