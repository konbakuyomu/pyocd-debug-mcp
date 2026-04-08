"""Target control tools: halt, step, resume, reset."""

from __future__ import annotations

from pyocd.core.target import Target

from ..session_manager import session_mgr


def _state_str(state: Target.State) -> str:
    """Convert Target.State enum to string."""
    return {
        Target.State.HALTED: "halted",
        Target.State.RUNNING: "running",
        Target.State.RESET: "reset",
        Target.State.SLEEPING: "sleeping",
        Target.State.LOCKUP: "lockup",
    }.get(state, str(state))


def halt() -> dict:
    """Halt the target CPU immediately."""
    target = session_mgr.target
    target.halt()
    pc = target.read_core_register("pc")
    return {"status": "halted", "pc": f"0x{pc:08X}"}


def step(count: int = 1) -> dict:
    """Single-step the target CPU."""
    target = session_mgr.target
    pcs = []
    for _ in range(count):
        target.step()
        pc = target.read_core_register("pc")
        pcs.append(f"0x{pc:08X}")
    return {"status": "stepped", "steps": count, "pc_trace": pcs}


def resume() -> dict:
    """Resume target execution."""
    target = session_mgr.target
    target.resume()
    return {"status": "running"}


def reset(halt_after: bool = True) -> dict:
    """Reset the target. By default resets and halts."""
    target = session_mgr.target
    if halt_after:
        target.reset_and_halt()
        # Re-enable fault vector catches (reset_and_halt may modify DEMCR)
        session_mgr._enable_fault_vector_catch()
        pc = target.read_core_register("pc")
        result = {"status": "halted", "reset": True, "pc": f"0x{pc:08X}"}
        # Auto-restore breakpoints
        bp_result = session_mgr.restore_breakpoints()
        result["breakpoints_restored"] = bp_result.get("breakpoints_restored", 0)
        if "failed" in bp_result:
            result["breakpoints_failed"] = bp_result["failed"]
        return result
    else:
        target.reset()
        return {"status": "running", "reset": True}


def get_status() -> dict:
    """Get current target state (halted/running/etc)."""
    target = session_mgr.target
    state = target.get_state()
    result = {"state": _state_str(state)}
    if state == Target.State.HALTED:
        result["pc"] = f"0x{target.read_core_register('pc'):08X}"
        result["sp"] = f"0x{target.read_core_register('sp'):08X}"
        result["lr"] = f"0x{target.read_core_register('lr'):08X}"
    elif state == Target.State.LOCKUP:
        result["message"] = (
            "CPU is in LOCKUP state (double fault: a fault occurred inside "
            "HardFault/NMI handler). Use pyocd_target_halt() to halt, then "
            "pyocd_debug_fault_analyze() for crash analysis."
        )
    return result
