"""RTT (Real-Time Transfer) tools using pyOCD native RTT support."""

from __future__ import annotations

import logging

from ..session_manager import session_mgr

logger = logging.getLogger(__name__)

# Module-level state — cleared on disconnect via _cleanup_tool_state
_rtt_cb = None  # GenericRTTControlBlock instance


def start(
    address: int | None = None,
    size: int | None = None,
    control_block_id: str = "SEGGER RTT",
) -> dict:
    """Start RTT and discover channels.

    If *address* is None, pyOCD will search RAM for the control block.
    Returns channel info (up/down names, sizes).
    """
    global _rtt_cb

    if _rtt_cb is not None:
        raise RuntimeError(
            "RTT already started. Call rtt.stop() first to restart."
        )

    target = session_mgr.target

    from pyocd.debug.rtt import GenericRTTControlBlock

    kwargs: dict = {}
    if address is not None:
        kwargs["address"] = address
    if size is not None:
        kwargs["size"] = size
    kwargs["control_block_id"] = control_block_id.encode("ascii")

    cb = GenericRTTControlBlock.from_target(target, **kwargs)
    cb.start()
    _rtt_cb = cb

    up_channels = []
    for i, ch in enumerate(cb.up_channels):
        up_channels.append({
            "index": i,
            "name": ch.name if ch.name else f"up{i}",
            "size": ch.size,
        })

    down_channels = []
    for i, ch in enumerate(cb.down_channels):
        down_channels.append({
            "index": i,
            "name": ch.name if ch.name else f"down{i}",
            "size": ch.size,
        })

    logger.info(
        "RTT started: %d up, %d down channels",
        len(up_channels), len(down_channels),
    )
    return {
        "status": "started",
        "control_block_address": f"0x{cb.address:08X}" if hasattr(cb, "address") else "auto",
        "up_channels": up_channels,
        "down_channels": down_channels,
    }


def stop() -> dict:
    """Stop RTT and release resources."""
    global _rtt_cb

    if _rtt_cb is None:
        return {"status": "not_running"}

    try:
        _rtt_cb.stop()
    except Exception as e:
        logger.warning("Error stopping RTT: %s", e)
    finally:
        _rtt_cb = None

    return {"status": "stopped"}


def read(channel: int = 0, max_bytes: int = 1024, encoding: str = "utf-8") -> dict:
    """Read data from an RTT up channel.

    Returns the data as text (decoded with *encoding*) and as hex.
    If no data is available, returns empty strings.
    """
    if _rtt_cb is None:
        raise RuntimeError("RTT not started. Call rtt.start() first.")

    if channel < 0 or channel >= len(_rtt_cb.up_channels):
        raise ValueError(
            f"Up channel {channel} out of range (0-{len(_rtt_cb.up_channels) - 1})"
        )

    ch = _rtt_cb.up_channels[channel]
    raw = ch.read()

    if not raw:
        return {
            "channel": channel,
            "bytes_read": 0,
            "text": "",
            "hex": "",
        }

    # Limit to max_bytes
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]

    try:
        text = raw.decode(encoding, errors="replace")
    except Exception:
        text = raw.decode("ascii", errors="replace")

    return {
        "channel": channel,
        "bytes_read": len(raw),
        "text": text,
        "hex": raw.hex(),
    }


def write(data: str, channel: int = 0, encoding: str = "utf-8") -> dict:
    """Write data to an RTT down channel.

    The *data* string is encoded with *encoding* before sending.
    Returns the number of bytes actually written.
    """
    if _rtt_cb is None:
        raise RuntimeError("RTT not started. Call rtt.start() first.")

    if channel < 0 or channel >= len(_rtt_cb.down_channels):
        raise ValueError(
            f"Down channel {channel} out of range (0-{len(_rtt_cb.down_channels) - 1})"
        )

    ch = _rtt_cb.down_channels[channel]
    raw = data.encode(encoding)
    written = ch.write(raw, blocking=False)

    return {
        "channel": channel,
        "bytes_sent": len(raw),
        "bytes_written": written,
    }


def status() -> dict:
    """Get RTT status: running/stopped, channel info, bytes available."""
    if _rtt_cb is None:
        return {"running": False}

    cb = _rtt_cb
    up_info = []
    for i, ch in enumerate(cb.up_channels):
        info: dict = {
            "index": i,
            "name": ch.name if ch.name else f"up{i}",
            "size": ch.size,
        }
        try:
            info["bytes_available"] = ch.bytes_available
        except Exception:
            pass
        up_info.append(info)

    down_info = []
    for i, ch in enumerate(cb.down_channels):
        info = {
            "index": i,
            "name": ch.name if ch.name else f"down{i}",
            "size": ch.size,
        }
        try:
            info["bytes_free"] = ch.bytes_free
        except Exception:
            pass
        down_info.append(info)

    return {
        "running": True,
        "up_channels": up_info,
        "down_channels": down_info,
    }
