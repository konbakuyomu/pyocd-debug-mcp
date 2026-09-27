"""The server must stay responsive when the probe is missing, slow or stuck."""

import asyncio
import json
import threading
import time

import pytest
from fastmcp import Client

from pyocd_debug_mcp import server, session_manager
from pyocd_debug_mcp.tools import probe


def result(r) -> dict:
    return json.loads(r.content[0].text)


@pytest.mark.asyncio
async def test_connect_without_a_probe_fails_at_once(monkeypatch):
    seen = {}

    def no_probe(**kwargs):
        seen.update(kwargs)
        return None  # what pyOCD returns with blocking=False and nothing attached

    monkeypatch.setattr(session_manager.ConnectHelper, "session_with_chosen_probe", no_probe)
    async with Client(server.mcp) as c:
        started = time.monotonic()
        r = await c.call_tool("pyocd_session_connect", {"target_type": "hc32f460"})
        assert time.monotonic() - started < 5
    assert seen["blocking"] is False
    assert "No debug probe found" in result(r)["error"]


@pytest.mark.asyncio
async def test_a_stuck_probe_does_not_freeze_the_server(monkeypatch):
    release = threading.Event()

    def stuck():
        release.wait(10)
        return []

    monkeypatch.setattr(probe, "list_probes", stuck)
    async with Client(server.mcp) as c:
        slow = asyncio.create_task(c.call_tool("pyocd_probe_list", {}))
        await asyncio.sleep(0.2)
        started = time.monotonic()
        r = await c.call_tool("pyocd_session_status", {})
        assert time.monotonic() - started < 2, "status must answer while the probe is busy"
        assert result(r) == {"connected": False}
        assert not slow.done()
        release.set()
        assert result(await slow) == {"probes": [], "count": 0}


@pytest.mark.asyncio
async def test_probe_calls_report_busy_instead_of_queueing_forever(monkeypatch):
    monkeypatch.setattr(server, "PROBE_WAIT_S", 0.2)
    assert server._probe_lock.acquire(timeout=1)
    try:
        async with Client(server.mcp) as c:
            r = await c.call_tool("pyocd_memory_read", {"address": "0x20000000"})
            assert "Probe busy" in result(r)["error"]
            with pytest.raises(server.ProbeBusy):
                await server._probe_call(lambda: None)
    finally:
        server._probe_lock.release()


@pytest.mark.asyncio
async def test_probe_operations_never_overlap(monkeypatch):
    active, overlaps = [0], [0]

    def op():
        active[0] += 1
        if active[0] > 1:
            overlaps[0] += 1
        time.sleep(0.05)
        active[0] -= 1
        return []

    monkeypatch.setattr(probe, "list_probes", op)
    async with Client(server.mcp) as c:
        await asyncio.gather(
            *(c.call_tool("pyocd_probe_list", {}) for _ in range(4)),
            *(server._probe_call(op) for _ in range(4)),
        )
    assert overlaps[0] == 0
