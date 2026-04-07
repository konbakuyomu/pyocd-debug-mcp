"""
pyocd-debug-mcp — MCP server for AI-driven embedded MCU debugging via pyOCD.

Provides structured tools for probe management, flash programming,
target control, register/memory access, breakpoint management,
ELF symbol resolution, and SVD peripheral register access.
"""

import sys
import asyncio
from pathlib import Path

# Support direct execution: add src dir to path
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fastmcp import FastMCP
from typing import Annotated, Optional

try:
    from pyocd_debug_mcp.session_manager import session_mgr
    from pyocd_debug_mcp.tools import probe, target, register, memory
    from pyocd_debug_mcp.tools import breakpoint as bp_tools
    from pyocd_debug_mcp.tools import flash, elf, svd
    from pyocd_debug_mcp.tools import watchpoint as wp_tools
    from pyocd_debug_mcp.tools import debug as debug_tools
except ImportError:
    from .session_manager import session_mgr
    from .tools import probe, target, register, memory
    from .tools import breakpoint as bp_tools
    from .tools import flash, elf, svd
    from .tools import watchpoint as wp_tools
    from .tools import debug as debug_tools

import json
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("pyocd-debug")


# ─── Helper ──────────────────────────────────────────────────────────────────

def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _error(msg: str) -> str:
    return _json({"error": msg})


# ─── Probe tools ─────────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.probe.list",
    description="List all connected CMSIS-DAP debug probes. Call this first to discover available probes.",
)
async def tool_probe_list() -> str:
    try:
        probes = probe.list_probes()
        return _json({"probes": probes, "count": len(probes)})
    except Exception as e:
        return _error(f"Failed to list probes: {e}")


@mcp.tool(
    name="pyocd.probe.info",
    description="Get detailed information about a specific debug probe.",
)
async def tool_probe_info(
    unique_id: Annotated[str, "Probe unique ID (or partial match)"],
) -> str:
    try:
        return _json(probe.get_probe_info(unique_id))
    except Exception as e:
        return _error(str(e))


# ─── Session tools ───────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.session.connect",
    description=(
        "Connect to a debug probe and open a debug session. "
        "Must be called before any target/register/memory operations. "
        "Only one session can be active at a time."
    ),
)
async def tool_session_connect(
    target_type: Annotated[str, "Target MCU type (e.g. 'hc32f460xe', 'hc32f4a0pi')"],
    probe_id: Annotated[Optional[str], "Probe unique ID. Omit to use first available."] = None,
    frequency: Annotated[int, "SWD clock frequency in Hz (default 4MHz)"] = 4_000_000,
) -> str:
    try:
        info = session_mgr.connect(
            target_type=target_type,
            probe_id=probe_id,
            frequency=frequency,
        )
        return _json({
            "status": "connected",
            "probe_id": info.probe_id,
            "target": info.target_type,
            "frequency": info.frequency,
        })
    except Exception as e:
        return _error(f"Connection failed: {e}")


@mcp.tool(
    name="pyocd.session.disconnect",
    description="Close the current debug session and release the probe.",
)
async def tool_session_disconnect() -> str:
    try:
        session_mgr.disconnect()
        return _json({"status": "disconnected"})
    except Exception as e:
        return _error(f"Disconnect failed: {e}")


@mcp.tool(
    name="pyocd.session.status",
    description="Check if a debug session is active and get connection info.",
)
async def tool_session_status() -> str:
    if not session_mgr.is_connected:
        return _json({"connected": False})
    info = session_mgr.info
    result = {
        "connected": True,
        "probe_id": info.probe_id if info else "unknown",
        "target": info.target_type if info else "unknown",
        "frequency": info.frequency if info else 0,
        "elf_attached": info.elf_path is not None if info else False,
        "svd_attached": info.svd_path is not None if info else False,
    }
    # Add target state if connected
    try:
        state = target.get_status()
        result.update(state)
    except Exception:
        pass
    return _json(result)


# ─── Flash tools ─────────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.flash.program",
    description=(
        "Program a firmware file (.hex/.bin/.elf) to the target flash. "
        "For armclang-compiled firmware, prefer .hex format to avoid ELF compatibility issues."
    ),
)
async def tool_flash_program(
    file_path: Annotated[str, "Absolute path to firmware file (.hex, .bin, or .elf)"],
    erase: Annotated[bool, "Erase flash before programming (default True)"] = True,
) -> str:
    try:
        return _json(flash.program(file_path, erase=erase))
    except Exception as e:
        return _error(f"Flash programming failed: {e}")


@mcp.tool(
    name="pyocd.flash.erase",
    description="Erase the target flash memory (chip erase or sector erase).",
)
async def tool_flash_erase(
    chip_erase: Annotated[bool, "True for full chip erase, False for sector erase"] = True,
) -> str:
    try:
        return _json(flash.erase(chip_erase=chip_erase))
    except Exception as e:
        return _error(f"Flash erase failed: {e}")


# ─── Target control tools ────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.target.halt",
    description="Halt (pause) the target CPU immediately. Returns current PC.",
)
async def tool_target_halt() -> str:
    try:
        return _json(target.halt())
    except Exception as e:
        return _error(f"Halt failed: {e}")


@mcp.tool(
    name="pyocd.target.step",
    description="Single-step the target CPU. Target must be halted first.",
)
async def tool_target_step(
    count: Annotated[int, "Number of instruction steps (default 1)"] = 1,
) -> str:
    try:
        return _json(target.step(count=count))
    except Exception as e:
        return _error(f"Step failed: {e}")


@mcp.tool(
    name="pyocd.target.resume",
    description="Resume target execution (run until next breakpoint or halt).",
)
async def tool_target_resume() -> str:
    try:
        return _json(target.resume())
    except Exception as e:
        return _error(f"Resume failed: {e}")


@mcp.tool(
    name="pyocd.target.reset",
    description="Reset the target MCU. By default resets and halts at the entry point.",
)
async def tool_target_reset(
    halt_after: Annotated[bool, "Halt after reset (default True)"] = True,
) -> str:
    try:
        return _json(target.reset(halt_after=halt_after))
    except Exception as e:
        return _error(f"Reset failed: {e}")


@mcp.tool(
    name="pyocd.target.status",
    description="Get current target state (halted/running) and key registers if halted.",
)
async def tool_target_status() -> str:
    try:
        return _json(target.get_status())
    except Exception as e:
        return _error(f"Status query failed: {e}")


# ─── Register tools ──────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.register.read",
    description="Read a CPU core register by name (e.g. 'pc', 'sp', 'r0', 'xpsr').",
)
async def tool_register_read(
    name: Annotated[str, "Register name (e.g. 'pc', 'sp', 'lr', 'r0'-'r12', 'xpsr')"],
) -> str:
    try:
        return _json(register.read_register(name))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.register.write",
    description="Write a value to a CPU core register.",
)
async def tool_register_write(
    name: Annotated[str, "Register name"],
    value: Annotated[int, "Value to write (integer)"],
) -> str:
    try:
        return _json(register.write_register(name, value))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.register.read_all",
    description="Read all CPU core registers at once. Useful for getting full CPU state.",
)
async def tool_register_read_all(
    include_fpu: Annotated[bool, "Include FPU registers (default False)"] = False,
) -> str:
    try:
        return _json(register.read_all_registers(include_fpu=include_fpu))
    except Exception as e:
        return _error(str(e))


# ─── Memory tools ────────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.memory.read",
    description="Read memory at a given address. Returns hex value.",
)
async def tool_memory_read(
    address: Annotated[int, "Memory address (integer, e.g. 0x20000000)"],
    size: Annotated[int, "Bytes to read: 1, 2, 4 for single access, or any number for block read"] = 4,
) -> str:
    try:
        return _json(memory.read_memory(address, size))
    except Exception as e:
        return _error(f"Memory read failed at 0x{address:08X}: {e}")


@mcp.tool(
    name="pyocd.memory.write",
    description="Write a value to memory at a given address.",
)
async def tool_memory_write(
    address: Annotated[int, "Memory address (integer)"],
    value: Annotated[int, "Value to write (integer)"],
    size: Annotated[int, "Access size in bytes: 1, 2, or 4"] = 4,
) -> str:
    try:
        return _json(memory.write_memory(address, value, size))
    except Exception as e:
        return _error(f"Memory write failed at 0x{address:08X}: {e}")


@mcp.tool(
    name="pyocd.memory.write_block",
    description="Write a block of bytes to memory.",
)
async def tool_memory_write_block(
    address: Annotated[int, "Start address"],
    data: Annotated[list[int], "List of byte values (0-255)"],
) -> str:
    try:
        return _json(memory.write_memory_block(address, data))
    except Exception as e:
        return _error(f"Block write failed at 0x{address:08X}: {e}")


@mcp.tool(
    name="pyocd.memory.dump",
    description="Dump memory in hex dump format (address, hex bytes, ASCII). Useful for inspecting data structures.",
)
async def tool_memory_dump(
    address: Annotated[int, "Start address"],
    length: Annotated[int, "Number of bytes to dump (default 256)"] = 256,
) -> str:
    try:
        return _json(memory.dump_memory(address, length))
    except Exception as e:
        return _error(f"Memory dump failed at 0x{address:08X}: {e}")


# ─── Breakpoint tools ────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.breakpoint.set",
    description="Set a hardware breakpoint at an address or symbol name (requires ELF).",
)
async def tool_breakpoint_set(
    address: Annotated[Optional[int], "Breakpoint address (integer)"] = None,
    symbol: Annotated[Optional[str], "Function/symbol name (requires ELF attached)"] = None,
) -> str:
    if address is None and symbol is None:
        return _error("Must specify 'address' or 'symbol'.")
    try:
        return _json(bp_tools.set_breakpoint(address=address, symbol=symbol))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.breakpoint.clear",
    description="Remove a breakpoint at an address or symbol.",
)
async def tool_breakpoint_clear(
    address: Annotated[Optional[int], "Breakpoint address"] = None,
    symbol: Annotated[Optional[str], "Symbol name"] = None,
) -> str:
    if address is None and symbol is None:
        return _error("Must specify 'address' or 'symbol'.")
    try:
        return _json(bp_tools.clear_breakpoint(address=address, symbol=symbol))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.breakpoint.clear_all",
    description="Remove all active breakpoints.",
)
async def tool_breakpoint_clear_all() -> str:
    try:
        return _json(bp_tools.clear_all_breakpoints())
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.breakpoint.list",
    description="List all active breakpoints.",
)
async def tool_breakpoint_list() -> str:
    try:
        return _json(bp_tools.list_breakpoints())
    except Exception as e:
        return _error(str(e))


# ─── ELF tools ───────────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.elf.attach",
    description=(
        "Attach an ELF file for symbol resolution. "
        "Enables using function names for breakpoints and provides richer debug info. "
        "Note: For flashing, prefer .hex format over .elf for armclang compatibility."
    ),
)
async def tool_elf_attach(
    elf_path: Annotated[str, "Absolute path to the ELF file"],
) -> str:
    try:
        return _json(elf.attach_elf(elf_path))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.elf.symbols",
    description="List symbols (functions/variables) from the attached ELF file.",
)
async def tool_elf_symbols(
    filter_text: Annotated[str, "Filter symbols by name (case-insensitive)"] = "",
    limit: Annotated[int, "Maximum results (default 50)"] = 50,
) -> str:
    try:
        return _json(elf.list_symbols(filter_text=filter_text, limit=limit))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.elf.lookup",
    description="Look up a symbol's address by name.",
)
async def tool_elf_lookup(
    name: Annotated[str, "Symbol/function name to look up"],
) -> str:
    try:
        return _json(elf.lookup_symbol(name))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.elf.info",
    description="Get information about the attached ELF file (arch, entry point, sections).",
)
async def tool_elf_info() -> str:
    try:
        return _json(elf.get_elf_info())
    except Exception as e:
        return _error(str(e))


# ─── SVD tools ───────────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.svd.attach",
    description=(
        "Attach an SVD file for peripheral register access. "
        "SVD files describe the register layout of MCU peripherals (GPIO, UART, SPI, etc)."
    ),
)
async def tool_svd_attach(
    svd_path: Annotated[str, "Absolute path to the SVD file"],
) -> str:
    try:
        return _json(svd.attach_svd(svd_path))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.list_peripherals",
    description="List all peripherals defined in the attached SVD file.",
)
async def tool_svd_list_peripherals() -> str:
    try:
        return _json(svd.list_peripherals())
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.list_registers",
    description="List all registers of a specific peripheral.",
)
async def tool_svd_list_registers(
    peripheral: Annotated[str, "Peripheral name (e.g. 'GPIOA', 'USART1', 'SPI1')"],
) -> str:
    try:
        return _json(svd.list_registers(peripheral))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.read",
    description=(
        "Read a peripheral register by name. Returns value with bit-field decoding. "
        "Example: pyocd.svd.read('GPIOA', 'IDR') to read GPIO input data register."
    ),
)
async def tool_svd_read(
    peripheral: Annotated[str, "Peripheral name (e.g. 'GPIOA')"],
    register: Annotated[str, "Register name (e.g. 'IDR', 'ODR', 'CR1')"],
) -> str:
    try:
        return _json(svd.read_register(peripheral, register))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.write",
    description="Write a value to a peripheral register by name.",
)
async def tool_svd_write(
    peripheral: Annotated[str, "Peripheral name"],
    register: Annotated[str, "Register name"],
    value: Annotated[int, "Value to write (integer)"],
) -> str:
    try:
        return _json(svd.write_register(peripheral, register, value))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.list_fields",
    description="List all bit fields of a peripheral register, showing name, bit range, width, and description.",
)
async def tool_svd_list_fields(
    peripheral: Annotated[str, "Peripheral name"],
    register: Annotated[str, "Register name"],
) -> str:
    try:
        return _json(svd.list_fields(peripheral, register))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.svd.set_field",
    description=(
        "Set a single bit field of a peripheral register using read-modify-write. "
        "Only the specified field is changed; other fields are preserved. "
        "Example: set_field('GPIOA', 'MODER', 'MODER0', 1) sets pin 0 to output mode."
    ),
)
async def tool_svd_set_field(
    peripheral: Annotated[str, "Peripheral name"],
    register: Annotated[str, "Register name"],
    field: Annotated[str, "Bit field name within the register"],
    value: Annotated[int, "Value to set (must fit within field width)"],
) -> str:
    try:
        return _json(svd.set_field(peripheral, register, field, value))
    except Exception as e:
        return _error(str(e))


# ─── Watchpoint tools ────────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.watchpoint.set",
    description=(
        "Set a hardware watchpoint (data breakpoint). Triggers a halt when "
        "the target reads/writes a specific memory address. Essential for "
        "catching wild pointers, buffer overflows, and unexpected memory writes. "
        "Cortex-M4 typically has 4 DWT comparators available."
    ),
)
async def tool_watchpoint_set(
    address: Annotated[int, "Memory address to watch"],
    size: Annotated[int, "Watched region size: 1, 2, or 4 bytes"] = 4,
    access_type: Annotated[str, "'write' (default), 'read', or 'read_write'"] = "write",
) -> str:
    try:
        return _json(wp_tools.set_watchpoint(address, size, access_type))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.watchpoint.clear",
    description="Remove a watchpoint at the given address.",
)
async def tool_watchpoint_clear(
    address: Annotated[int, "Watchpoint address to clear"],
) -> str:
    try:
        return _json(wp_tools.clear_watchpoint(address))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.watchpoint.clear_all",
    description="Remove all active watchpoints.",
)
async def tool_watchpoint_clear_all() -> str:
    try:
        return _json(wp_tools.clear_all_watchpoints())
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.watchpoint.list",
    description="List all active watchpoints.",
)
async def tool_watchpoint_list() -> str:
    try:
        return _json(wp_tools.list_watchpoints())
    except Exception as e:
        return _error(str(e))


# ─── Advanced debug tools ────────────────────────────────────────────────────

@mcp.tool(
    name="pyocd.target.wait_halt",
    description=(
        "Resume target execution and wait for it to halt (breakpoint hit, watchpoint "
        "triggered, or manual halt). This is the KEY tool for 'set breakpoint → run → "
        "wait for hit → inspect' debugging workflow. Returns halt reason, PC, and "
        "registers when the target stops."
    ),
)
async def tool_target_wait_halt(
    timeout: Annotated[float, "Max seconds to wait (default 30)"] = 30.0,
    resume_first: Annotated[bool, "Resume target before waiting (default True)"] = True,
) -> str:
    try:
        result = await asyncio.to_thread(
            debug_tools.wait_halt, timeout=timeout, resume_first=resume_first
        )
        return _json(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.debug.fault_analyze",
    description=(
        "Analyze a HardFault/BusFault/MemManage/UsageFault crash. Reads all SCB "
        "fault registers, decodes fault bits, reads the exception stack frame to "
        "find the fault PC (crash address) and caller LR. Also decodes EXC_RETURN "
        "for FPU/MSP/PSP context. Call this when target is halted in a fault handler."
    ),
)
async def tool_debug_fault_analyze() -> str:
    try:
        return _json(debug_tools.fault_analyze())
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.debug.stack_overflow_check",
    description=(
        "Check if a thread's stack has overflowed by comparing SP against the "
        "TCB's stack bounds. For RT-Thread: provide TCB address, offsets default "
        "to 0x24 (stack_addr) and 0x28 (stack_size). Reports usage percentage "
        "and watermark integrity."
    ),
)
async def tool_debug_stack_overflow_check(
    tcb_address: Annotated[Optional[int], "Thread Control Block address (from .map file or symbol)"] = None,
    stack_addr_offset: Annotated[int, "Offset of stack_addr in TCB (RT-Thread=0x24)"] = 0x24,
    stack_size_offset: Annotated[int, "Offset of stack_size in TCB (RT-Thread=0x28)"] = 0x28,
) -> str:
    try:
        return _json(debug_tools.stack_overflow_check(
            tcb_address=tcb_address,
            stack_addr_offset=stack_addr_offset,
            stack_size_offset=stack_size_offset,
        ))
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.debug.sample_variable",
    description=(
        "Periodically sample a memory location (global variable). Reads a variable "
        "every N seconds for M samples while target is running. Returns all samples "
        "with timestamps and statistics. Example: monitor a sensor reading every 0.5s "
        "for 100s = 200 samples."
    ),
)
async def tool_debug_sample_variable(
    address: Annotated[int, "Memory address of the variable"],
    size: Annotated[int, "Variable size: 1, 2, or 4 bytes"] = 4,
    interval: Annotated[float, "Seconds between samples (default 0.5)"] = 0.5,
    count: Annotated[int, "Number of samples (default 200)"] = 200,
    halt_on_read: Annotated[bool, "Halt target for each read (safer but slower)"] = False,
) -> str:
    try:
        result = await asyncio.to_thread(
            debug_tools.sample_variable,
            address=address, size=size, interval=interval,
            count=count, halt_on_read=halt_on_read,
        )
        return _json(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool(
    name="pyocd.target.list_supported",
    description=(
        "List all MCU targets supported by pyocd (206+ built-in targets). "
        "Includes HC32, STM32, NXP, Nordic, Cypress and more. "
        "Use filter_text to search (e.g. 'hc32', 'stm32f4')."
    ),
)
async def tool_target_list_supported(
    filter_text: Annotated[str, "Filter targets by name (case-insensitive)"] = "",
) -> str:
    try:
        return _json(debug_tools.list_supported_targets(filter_text=filter_text))
    except Exception as e:
        return _error(str(e))


# ─── Main entry point ────────────────────────────────────────────────────────

def main():
    import signal
    import os
    import threading

    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    # Signal handling (main thread only)
    if threading.current_thread() is threading.main_thread():
        def handle_shutdown(signum, frame):
            # Clean up pyocd session before exit
            try:
                session_mgr.disconnect()
            except Exception:
                pass
            os._exit(0)

        signal.signal(signal.SIGINT, handle_shutdown)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, handle_shutdown)

    # Windows parent process monitor
    if sys.platform == "win32":
        import time
        import ctypes

        parent_pid = os.getppid()

        def is_parent_alive(pid):
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return True
            exit_code = ctypes.c_ulong()
            result = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            return result and exit_code.value == STILL_ACTIVE

        def monitor_parent():
            while True:
                if not is_parent_alive(parent_pid):
                    try:
                        session_mgr.disconnect()
                    except Exception:
                        pass
                    os._exit(0)
                time.sleep(2)

        threading.Thread(target=monitor_parent, daemon=True).start()

    try:
        mcp.run(transport="stdio", show_banner=False)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            session_mgr.disconnect()
        except Exception:
            pass
        os._exit(0)


if __name__ == "__main__":
    main()
