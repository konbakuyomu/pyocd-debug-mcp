"""Advanced debug analysis tools.

Provides HardFault analysis, stack backtrace, stack overflow detection,
periodic variable sampling, and other crash diagnosis utilities.
Based on Cortex-M debug techniques from user's Obsidian notes.
"""

from __future__ import annotations

import time
import logging
from typing import Optional

from pyocd.core.target import Target

from ..session_manager import session_mgr

logger = logging.getLogger(__name__)


# ─── Cortex-M SCB Fault Register Addresses ────────────────────────────────────

SCB_ICSR = 0xE000ED04  # Interrupt Control and State
SCB_CFSR = 0xE000ED28  # Configurable Fault Status Register
SCB_HFSR = 0xE000ED2C  # HardFault Status Register
SCB_DFSR = 0xE000ED30  # Debug Fault Status Register
SCB_MMFAR = 0xE000ED34  # MemManage Fault Address
SCB_BFAR = 0xE000ED38  # BusFault Address
SCB_AFSR = 0xE000ED3C  # Auxiliary Fault Status Register

# CFSR sub-register bit definitions
MMFSR_BITS = {
    0: ("IACCVIOL", "Instruction access violation"),
    1: ("DACCVIOL", "Data access violation"),
    3: ("MUNSTKERR", "MemManage fault on unstacking"),
    4: ("MSTKERR", "MemManage fault on stacking"),
    5: ("MLSPERR", "MemManage fault during FP lazy state preservation"),
    7: ("MMARVALID", "MMFAR holds valid address"),
}

BFSR_BITS = {
    0: ("IBUSERR", "Instruction bus error"),
    1: ("PRECISERR", "Precise data bus error"),
    2: ("IMPRECISERR", "Imprecise data bus error"),
    3: ("UNSTKERR", "BusFault on unstacking"),
    4: ("STKERR", "BusFault on stacking"),
    5: ("LSPERR", "BusFault during FP lazy state preservation"),
    7: ("BFARVALID", "BFAR holds valid address"),
}

UFSR_BITS = {
    0: ("UNDEFINSTR", "Undefined instruction"),
    1: ("INVSTATE", "Invalid state (Thumb bit)"),
    2: ("INVPC", "Invalid PC load"),
    3: ("NOCP", "No coprocessor"),
    4: ("STKOF", "Stack overflow (ARMv8-M)"),
    8: ("UNALIGNED", "Unaligned access"),
    9: ("DIVBYZERO", "Divide by zero"),
}

HFSR_BITS = {
    1: ("VECTTBL", "BusFault on vector table read"),
    30: ("FORCED", "Forced HardFault (escalated)"),
    31: ("DEBUGEVT", "Debug event"),
}


def _decode_bits(value: int, bit_defs: dict, offset: int = 0) -> list[dict]:
    """Decode register bits using definitions.

    Args:
        value: The (already-extracted) sub-register value with bits starting at 0.
        bit_defs: Dict mapping bit position (relative to value) to (name, description).
        offset: Display offset — added to bit position in output only, NOT used for masking.
    """
    active = []
    for bit, (name, desc) in bit_defs.items():
        if value & (1 << bit):
            active.append({"bit": bit + offset, "name": name, "description": desc})
    return active


def fault_analyze() -> dict:
    """Analyze the current HardFault state.

    Reads all SCB fault registers, decodes fault bits, extracts the
    exception stack frame (PC = fault address, LR = caller), and
    determines the EXC_RETURN type for FPU/stack pointer context.

    The target should be halted in a fault handler when calling this.
    """
    target = session_mgr.target

    # Ensure target is halted
    state = target.get_state()
    if state != Target.State.HALTED:
        target.halt()

    # Read fault registers
    cfsr = target.read32(SCB_CFSR)
    hfsr = target.read32(SCB_HFSR)
    dfsr = target.read32(SCB_DFSR)
    mmfar = target.read32(SCB_MMFAR)
    bfar = target.read32(SCB_BFAR)
    icsr = target.read32(SCB_ICSR)

    # Decode CFSR sub-registers
    mmfsr = cfsr & 0xFF
    bfsr = (cfsr >> 8) & 0xFF
    ufsr = (cfsr >> 16) & 0xFFFF

    result = {
        "fault_registers": {
            "CFSR": f"0x{cfsr:08X}",
            "HFSR": f"0x{hfsr:08X}",
            "DFSR": f"0x{dfsr:08X}",
            "MMFAR": f"0x{mmfar:08X}",
            "BFAR": f"0x{bfar:08X}",
            "ICSR": f"0x{icsr:08X}",
        },
        "active_faults": [],
        "fault_type": "unknown",
    }

    # Decode active faults
    faults = []
    faults.extend(_decode_bits(mmfsr, MMFSR_BITS, 0))
    faults.extend(_decode_bits(bfsr, BFSR_BITS, 8))
    faults.extend(_decode_bits(ufsr, UFSR_BITS, 16))
    hf = _decode_bits(hfsr, HFSR_BITS, 0)
    faults.extend(hf)
    result["active_faults"] = faults

    # Determine fault type
    if mmfsr:
        result["fault_type"] = "MemManage"
    elif bfsr:
        result["fault_type"] = "BusFault"
    elif ufsr:
        result["fault_type"] = "UsageFault"
    elif hfsr & (1 << 30):
        result["fault_type"] = "HardFault (escalated)"
    elif hfsr:
        result["fault_type"] = "HardFault"

    # Fault address
    if mmfsr & (1 << 7):  # MMARVALID
        result["fault_address"] = f"0x{mmfar:08X}"
        result["fault_address_source"] = "MMFAR"
    elif bfsr & (1 << 7):  # BFARVALID
        result["fault_address"] = f"0x{bfar:08X}"
        result["fault_address_source"] = "BFAR"

    # Read EXC_RETURN from LR
    lr = target.read_core_register("lr")
    result["exc_return"] = _decode_exc_return(lr)

    # Read exception stack frame
    stack_frame = _read_exception_stack_frame(target, lr)
    if stack_frame:
        result["exception_frame"] = stack_frame

    # Active exception number from ICSR
    exception_num = icsr & 0x1FF
    result["active_exception"] = exception_num
    result["exception_name"] = _exception_name(exception_num)

    return result


def _decode_exc_return(lr: int) -> dict:
    """Decode EXC_RETURN value from LR register."""
    if (lr & 0xFFFFFF00) != 0xFFFFFF00:
        return {"raw": f"0x{lr:08X}", "is_exc_return": False}

    return {
        "raw": f"0x{lr:08X}",
        "is_exc_return": True,
        "return_to": "Thread" if lr & (1 << 3) else "Handler",
        "stack_used": "PSP" if lr & (1 << 2) else "MSP",
        "fpu_context": "Extended (FPU active)" if not (lr & (1 << 4)) else "Basic (no FPU)",
        "frame_size": 26 if not (lr & (1 << 4)) else 8,
    }


def _read_exception_stack_frame(target, lr: int) -> Optional[dict]:
    """Read the exception stack frame based on EXC_RETURN."""
    try:
        # Determine which stack pointer
        if lr & (1 << 2):  # PSP
            sp = target.read_core_register("psp")
            sp_name = "PSP"
        else:  # MSP
            sp = target.read_core_register("msp")
            sp_name = "MSP"

        has_fpu = not (lr & (1 << 4))

        # Standard exception frame: R0,R1,R2,R3,R12,LR,PC,xPSR
        # If FPU: + S0-S15, FPSCR (additional 18 words)
        frame_data = target.read_memory_block32(sp, 8)

        frame = {
            "stack_pointer": f"0x{sp:08X}",
            "stack_type": sp_name,
            "R0": f"0x{frame_data[0]:08X}",
            "R1": f"0x{frame_data[1]:08X}",
            "R2": f"0x{frame_data[2]:08X}",
            "R3": f"0x{frame_data[3]:08X}",
            "R12": f"0x{frame_data[4]:08X}",
            "LR_saved": f"0x{frame_data[5]:08X}",
            "PC_fault": f"0x{frame_data[6]:08X}",
            "xPSR": f"0x{frame_data[7]:08X}",
        }

        # PC is the instruction that caused the fault
        pc_fault = frame_data[6]
        frame["fault_instruction_address"] = f"0x{pc_fault:08X}"

        # LR_saved tells us the caller
        saved_lr = frame_data[5]
        lr_addr = saved_lr & ~1  # Clear Thumb bit
        if saved_lr & 1:
            frame["caller_address"] = f"0x{lr_addr:08X}"
        else:
            frame["caller_address"] = f"0x{saved_lr:08X}"

        # Resolve PC and LR to function names via ELF symbol decoder
        try:
            elf_file = target.elf
            if elf_file is not None:
                decoder = elf_file.symbol_decoder
                pc_sym = decoder.get_symbol_for_address(pc_fault)
                if pc_sym:
                    frame["fault_function"] = pc_sym.name
                    frame["fault_offset"] = f"+0x{pc_fault - pc_sym.address:X}"
                lr_sym = decoder.get_symbol_for_address(lr_addr)
                if lr_sym:
                    frame["caller_function"] = lr_sym.name
                    frame["caller_offset"] = f"+0x{lr_addr - lr_sym.address:X}"
        except Exception:
            pass

        return frame
    except Exception as e:
        return {"error": f"Failed to read stack frame: {e}"}


def _exception_name(num: int) -> str:
    """Convert exception number to name."""
    names = {
        0: "Thread",
        1: "Reset",
        2: "NMI",
        3: "HardFault",
        4: "MemManage",
        5: "BusFault",
        6: "UsageFault",
        11: "SVCall",
        12: "DebugMonitor",
        14: "PendSV",
        15: "SysTick",
    }
    if num in names:
        return names[num]
    elif num >= 16:
        return f"IRQ{num - 16}"
    return f"Exception_{num}"


def stack_overflow_check(
    tcb_address: Optional[int] = None,
    stack_addr_offset: int = 0x24,
    stack_size_offset: int = 0x28,
) -> dict:
    """Check if the current thread's stack has overflowed.

    For RT-Thread: offsets are 0x24 (stack_addr) and 0x28 (stack_size).
    For FreeRTOS: offset 0x00 is pxTopOfStack, stack bounds differ.

    Args:
        tcb_address: Thread Control Block address. If None, reads PSP directly.
        stack_addr_offset: Offset of stack_addr in TCB struct.
        stack_size_offset: Offset of stack_size in TCB struct.
    """
    target = session_mgr.target
    psp = target.read_core_register("psp")
    msp = target.read_core_register("msp")

    result = {
        "PSP": f"0x{psp:08X}",
        "MSP": f"0x{msp:08X}",
    }

    if tcb_address is not None:
        stack_addr = target.read32(tcb_address + stack_addr_offset)
        stack_size = target.read32(tcb_address + stack_size_offset)
        stack_end = stack_addr + stack_size

        result["tcb_address"] = f"0x{tcb_address:08X}"
        result["stack_addr"] = f"0x{stack_addr:08X}"
        result["stack_size"] = stack_size
        result["stack_end"] = f"0x{stack_end:08X}"

        # Check PSP against stack bounds
        psp_in_range = stack_addr <= psp < stack_end
        result["psp_in_range"] = psp_in_range
        result["overflow"] = not psp_in_range

        if psp_in_range:
            used = stack_end - psp
            result["stack_used"] = used
            result["stack_free"] = stack_size - used
            result["usage_percent"] = round(used / stack_size * 100, 1)
        else:
            if psp < stack_addr:
                result["overflow_direction"] = "underflow"
                result["overflow_bytes"] = stack_addr - psp
            else:
                result["overflow_direction"] = "overflow"
                result["overflow_bytes"] = psp - stack_end

        # Check stack watermark (look for 0xDEADBEEF or 0x23 pattern)
        try:
            bottom_words = target.read_memory_block32(stack_addr, 8)
            magic_count = sum(1 for w in bottom_words if w == 0x23232323 or w == 0xDEADBEEF)
            result["watermark_intact"] = magic_count > 0
            result["bottom_8_words"] = [f"0x{w:08X}" for w in bottom_words]
        except Exception:
            pass

        # Read thread name (first bytes of TCB for RT-Thread)
        try:
            name_bytes = target.read_memory_block8(tcb_address, 12)
            name = bytes(name_bytes).split(b"\x00")[0].decode("ascii", errors="replace")
            result["thread_name"] = name
        except Exception:
            pass
    else:
        result["note"] = "Provide tcb_address for full stack analysis"

    return result


def list_supported_targets(filter_text: str = "") -> dict:
    """List all MCU targets supported by pyocd (built-in + installed packs).

    Args:
        filter_text: Optional filter string (case-insensitive).
    """
    from pyocd.target.builtin import BUILTIN_TARGETS

    targets = sorted(BUILTIN_TARGETS.keys())

    if filter_text:
        ft = filter_text.lower()
        targets = [t for t in targets if ft in t.lower()]

    # Group by vendor prefix
    groups = {}
    for t in targets:
        # Heuristic grouping
        if t.startswith("hc32"):
            vendor = "HDSC/XHSC"
        elif t.startswith("stm32"):
            vendor = "STMicroelectronics"
        elif t.startswith("nrf"):
            vendor = "Nordic"
        elif t.startswith("air"):
            vendor = "Luat/Air"
        elif t.startswith("lpc") or t.startswith("mk") or t.startswith("mimx"):
            vendor = "NXP"
        elif t.startswith("cy"):
            vendor = "Cypress/Infineon"
        elif t.startswith("max"):
            vendor = "Maxim/ADI"
        elif t.startswith("m4"):
            vendor = "Nuvoton"
        else:
            vendor = "Other"
        groups.setdefault(vendor, []).append(t)

    return {
        "total": len(targets),
        "targets": targets,
        "by_vendor": {k: {"count": len(v), "targets": v} for k, v in sorted(groups.items())},
        "note": "Additional targets available via CMSIS-Pack: pyocd pack find <keyword>",
    }
