"""Precise ARM stack unwinder for Cortex-M targets.

Supports three unwinding methods:
- DWARF CFI (.debug_frame): Works with all toolchains (AC5/AC6/GCC).
  Handles armcc's custom 'armcc+' augmentation via monkey-patch.
- EHABI (.ARM.exidx): Works with AC6/GCC when -funwind-tables is enabled.
  Implements a VRS (Virtual Register Set) interpreter for bytecode execution.
- Heuristic fallback: Stack scanning with BL validation (existing method).

Coverage matrix:
  | Toolchain     | .ARM.exidx | .debug_frame | Precise method           |
  |---------------|-----------|-------------|---------------------------|
  | armcc  (AC5)  | No        | Yes (armcc+)| DWARF CFI                 |
  | armclang (AC6)| Yes       | Yes         | EHABI preferred, CFI alt  |
  | GCC           | Yes*      | Yes         | EHABI preferred, CFI alt  |
  * GCC requires -funwind-tables or -fexceptions for .ARM.exidx
"""

from __future__ import annotations

import struct
import logging
from bisect import bisect_right
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Type alias: read 4 bytes from target memory
ReadMemoryFunc = Callable[[int], int]  # address -> uint32 value


# ─── DWARF CFI Unwinder ──────────────────────────────────────────────────────


def _patch_pyelftools_armcc():
    """Monkey-patch pyelftools to handle armcc+ augmentation in .debug_frame.

    armcc (AC5) produces CIE entries with augmentation string "armcc+" which
    causes pyelftools to crash at an assert that expects 'z'-prefixed augmentation.

    The 'armcc+' augmentation means:
    - Standard CFA semantics (CFA = register + offset, positive direction)
    - The '+' suffix specifically indicates positive offset direction
    - No extra augmentation data bytes in the CIE (unlike 'z' prefix)
    - All CFA instructions after the augmentation string are standard DWARF

    We simply return empty augmentation data, letting pyelftools decode the
    standard DWARF instructions that follow.
    """
    from elftools.dwarf.callframe import CallFrameInfo

    if getattr(CallFrameInfo, '_armcc_patched', False):
        return  # Already patched

    _original = CallFrameInfo._parse_cie_augmentation

    def _patched(self, header, entry_structs):
        aug = header.get('augmentation', b'')
        if aug and aug.startswith(b'armcc'):
            return (b'', {})
        return _original(self, header, entry_structs)

    CallFrameInfo._parse_cie_augmentation = _patched
    CallFrameInfo._armcc_patched = True


class DWARFCFIUnwinder:
    """Precise stack unwinder using DWARF .debug_frame CFI tables.

    Works with all ARM toolchains:
    - armcc (AC5): Requires armcc+ augmentation monkey-patch
    - armclang (AC6): Standard DWARF, works out of box
    - GCC: Standard DWARF, works out of box
    """

    def __init__(self, elf_path: str):
        _patch_pyelftools_armcc()

        from elftools.elf.elffile import ELFFile
        from elftools.dwarf.callframe import CIE, FDE

        self._fde_list: list[tuple[int, int, object]] = []  # (start, end, fde)

        with open(elf_path, 'rb') as f:
            elf = ELFFile(f)
            if not elf.has_dwarf_info():
                raise ValueError("ELF has no DWARF info")

            dwarf = elf.get_dwarf_info()

            try:
                entries = list(dwarf.CFI_entries())
            except Exception as e:
                raise ValueError(f"Failed to parse .debug_frame: {e}") from e

            for entry in entries:
                if isinstance(entry, FDE):
                    start = entry.header.initial_location
                    size = entry.header.address_range
                    if start > 0 and size > 0:
                        # Pre-decode the table so the ELF file can be closed
                        try:
                            decoded = entry.get_decoded()
                            self._fde_list.append((start, start + size, decoded))
                        except Exception:
                            # Skip FDEs that fail to decode
                            pass

        if not self._fde_list:
            raise ValueError("No usable FDE entries in .debug_frame")

        # Sort by start address for binary search
        self._fde_list.sort(key=lambda x: x[0])
        self._starts = [fde[0] for fde in self._fde_list]

        logger.debug("DWARF CFI: %d FDEs loaded", len(self._fde_list))

    def find_fde(self, pc: int) -> Optional[tuple[int, int, object]]:
        """Find FDE covering the given PC address.

        Returns (start, end, decoded_table) or None.
        """
        idx = bisect_right(self._starts, pc) - 1
        if idx < 0:
            return None
        start, end, decoded = self._fde_list[idx]
        if start <= pc < end:
            return (start, end, decoded)
        return None

    def unwind_frame(self, registers: dict[int, int],
                     read_memory: ReadMemoryFunc) -> Optional[dict[int, int]]:
        """Unwind one stack frame using DWARF CFI rules.

        Args:
            registers: Current register values {reg_num: value}.
                       Key registers: 13=SP, 14=LR, 15=PC
            read_memory: Function to read a 32-bit word from target memory.

        Returns:
            New register dict for the caller frame, or None if unwinding fails.
        """
        pc = registers.get(15, 0)
        if pc == 0:
            return None

        fde_info = self.find_fde(pc)
        if fde_info is None:
            return None

        _, _, decoded = fde_info

        # Find the appropriate row: last row where row['pc'] <= target pc
        table = decoded.table
        if not table:
            return None

        row = table[0]
        for r in table:
            if r['pc'] <= pc:
                row = r
            else:
                break

        # Extract CFA rule
        cfa_rule = row.get('cfa')
        if cfa_rule is None or cfa_rule.reg is None:
            return None

        cfa_reg = cfa_rule.reg
        cfa_offset = cfa_rule.offset

        if cfa_reg not in registers:
            return None

        cfa = registers[cfa_reg] + cfa_offset
        if cfa == 0:
            return None

        # Build new register set by applying rules
        new_regs = dict(registers)
        new_regs[13] = cfa  # SP = CFA (canonical frame address is caller's SP)

        pc_recovered = False
        lr_recovered = False

        for key, rule in row.items():
            if key in ('pc', 'cfa'):
                continue

            reg_num = key
            if not isinstance(reg_num, int):
                continue

            if rule.type == 'OFFSET':
                # Register saved at CFA + offset
                mem_addr = cfa + rule.arg
                try:
                    new_regs[reg_num] = read_memory(mem_addr)
                    if reg_num == 15:
                        pc_recovered = True
                    elif reg_num == 14:
                        lr_recovered = True
                except Exception:
                    # Critical: if LR or PC read fails, we can't unwind
                    if reg_num in (14, 15):
                        return None
                    pass  # Non-critical registers: skip silently

            elif rule.type == 'VAL_OFFSET':
                # Register value IS CFA + offset
                new_regs[reg_num] = cfa + rule.arg

            elif rule.type == 'REGISTER':
                # Register value is in another register
                src_reg = rule.arg
                if src_reg in registers:
                    new_regs[reg_num] = registers[src_reg]

            elif rule.type == 'SAME_VALUE':
                # Register retains its current value
                pass

            elif rule.type == 'UNDEFINED':
                # Register has no recoverable value
                if reg_num in new_regs and reg_num not in (13, 15):
                    pass  # Keep whatever is there for display purposes

        # If PC was not explicitly recovered, use LR
        if not pc_recovered:
            if lr_recovered and 14 in new_regs:
                new_regs[15] = new_regs[14] & ~1  # Clear Thumb bit
            elif not lr_recovered:
                # LR rule was SAME_VALUE or absent — check if LR changed
                # If LR == old PC (within current function), we can't unwind further
                old_pc = registers.get(15, 0)
                lr_val = new_regs.get(14, 0)
                if lr_val == 0 or (lr_val & ~1) == old_pc:
                    return None
                new_regs[15] = lr_val & ~1

        return new_regs


# ─── EHABI (.ARM.exidx) Unwinder ─────────────────────────────────────────────


class EHABIUnwinder:
    """Precise stack unwinder using ARM EHABI (.ARM.exidx) unwind tables.

    Implements a VRS (Virtual Register Set) interpreter that executes
    EHABI bytecode opcodes to virtually unwind the stack frame.

    Works with armclang (AC6) and GCC (requires -funwind-tables).
    """

    # EXIDX special values
    EXIDX_CANTUNWIND = 0x00000001

    def __init__(self, elf_path: str):
        from elftools.elf.elffile import ELFFile

        self._entries: list[tuple[int, bytes | None]] = []  # (func_addr, bytecodes|None)

        with open(elf_path, 'rb') as f:
            elf = ELFFile(f)
            exidx_section = None
            for section in elf.iter_sections():
                if section.name == '.ARM.exidx' or \
                   section.header.sh_type == 'SHT_ARM_EXIDX':
                    exidx_section = section
                    break

            if exidx_section is None:
                raise ValueError("ELF has no .ARM.exidx section")

            data = exidx_section.data()
            section_addr = exidx_section.header.sh_addr
            num_entries = len(data) // 8

            # Load .ARM.extab if present (for personality routines)
            extab_section = None
            extab_data = None
            extab_addr = 0
            for section in elf.iter_sections():
                if section.name == '.ARM.extab':
                    extab_section = section
                    extab_data = section.data()
                    extab_addr = section.header.sh_addr
                    break

            for i in range(num_entries):
                word0, word1 = struct.unpack_from('<II', data, i * 8)

                # Decode prel31 function address
                func_addr = self._prel31_to_addr(word0, section_addr + i * 8)

                if word1 == self.EXIDX_CANTUNWIND:
                    # Function cannot be unwound
                    self._entries.append((func_addr, None))
                elif word1 & 0x80000000:
                    # Inline compact model (Su16): personality 0
                    # Byte 0 = 0x80 | personality(0), bytes 1-3 are opcodes
                    b1 = (word1 >> 16) & 0xFF
                    b2 = (word1 >> 8) & 0xFF
                    b3 = word1 & 0xFF
                    bytecodes = bytes([b1, b2, b3])
                    self._entries.append((func_addr, bytecodes))
                else:
                    # Pointer to .ARM.extab entry (prel31)
                    extab_entry_addr = self._prel31_to_addr(
                        word1, section_addr + i * 8 + 4)
                    bytecodes = self._parse_extab_entry(
                        extab_entry_addr, extab_data, extab_addr)
                    self._entries.append((func_addr, bytecodes))

        if not self._entries:
            raise ValueError("No entries in .ARM.exidx")

        self._entries.sort(key=lambda x: x[0])
        self._addrs = [e[0] for e in self._entries]

        logger.debug("EHABI: %d entries loaded", len(self._entries))

    @staticmethod
    def _prel31_to_addr(word: int, origin: int) -> int:
        """Convert a prel31 offset to absolute address."""
        offset = word & 0x7FFFFFFF
        if offset & 0x40000000:
            offset |= 0x80000000
            offset -= 0x100000000
        return (origin + offset) & 0xFFFFFFFF

    @staticmethod
    def _parse_extab_entry(entry_addr: int, extab_data: Optional[bytes],
                           extab_base: int) -> Optional[bytes]:
        """Parse an .ARM.extab entry to extract bytecodes."""
        if extab_data is None:
            return None

        offset = entry_addr - extab_base
        if offset < 0 or offset + 4 > len(extab_data):
            return None

        word0 = struct.unpack_from('<I', extab_data, offset)[0]

        if word0 & 0x80000000:
            # Compact model: personality in bits [27:24]
            personality = (word0 >> 24) & 0x0F
            if personality == 1:
                # Su16: 3 bytes of opcodes in word0
                b1 = (word0 >> 16) & 0xFF
                b2 = (word0 >> 8) & 0xFF
                b3 = word0 & 0xFF
                bytecodes = bytes([b1, b2, b3])
                return bytecodes
            elif personality == 2:
                # Lu16/Lu32: first byte is additional word count
                extra_words = (word0 >> 16) & 0xFF
                b2 = (word0 >> 8) & 0xFF
                b3 = word0 & 0xFF
                opcodes = [b2, b3]
                for w in range(extra_words):
                    wo = offset + 4 + w * 4
                    if wo + 4 > len(extab_data):
                        break
                    extra = struct.unpack_from('<I', extab_data, wo)[0]
                    opcodes.extend([
                        (extra >> 24) & 0xFF,
                        (extra >> 16) & 0xFF,
                        (extra >> 8) & 0xFF,
                        extra & 0xFF,
                    ])
                return bytes(opcodes)
            else:
                # Personality 0 compact in extab (rare)
                b1 = (word0 >> 16) & 0xFF
                b2 = (word0 >> 8) & 0xFF
                b3 = word0 & 0xFF
                return bytes([b1, b2, b3])
        else:
            # Generic personality routine — not compact, cannot decode
            return None

    def find_entry(self, pc: int) -> Optional[tuple[int, bytes | None]]:
        """Find EHABI entry for the given PC.

        Returns (func_addr, bytecodes) or None. bytecodes is None for CANTUNWIND.
        """
        idx = bisect_right(self._addrs, pc) - 1
        if idx < 0:
            return None

        func_addr, bytecodes = self._entries[idx]

        # Verify PC is within reasonable range of function start
        # (use next entry's address as upper bound)
        if idx + 1 < len(self._entries):
            next_addr = self._entries[idx + 1][0]
            if pc >= next_addr:
                return None

        return (func_addr, bytecodes)

    def unwind_frame(self, registers: dict[int, int],
                     read_memory: ReadMemoryFunc) -> Optional[dict[int, int]]:
        """Unwind one stack frame by executing EHABI bytecodes.

        Implements a VRS (Virtual Register Set) interpreter:
        1. Initialize VRS from current registers
        2. Set vsp = current SP
        3. Execute opcodes sequentially
        4. Pop operations read from memory at vsp, advance vsp
        5. If PC not explicitly set, copy LR to PC (implicit Finish)

        Args:
            registers: Current register values {reg_num: value}.
            read_memory: Function to read a 32-bit word from target memory.

        Returns:
            New register dict for the caller frame, or None if unwinding fails.
        """
        pc = registers.get(15, 0)
        if pc == 0:
            return None

        entry = self.find_entry(pc)
        if entry is None:
            return None

        func_addr, bytecodes = entry
        if bytecodes is None:
            # CANTUNWIND
            return None

        # Initialize VRS (Virtual Register Set)
        vrs = dict(registers)
        vsp = vrs.get(13, 0)
        if vsp == 0:
            return None

        pc_set = False

        # Execute bytecodes
        i = 0
        while i < len(bytecodes):
            op = bytecodes[i]

            if (op & 0xC0) == 0x00:
                # 00xxxxxx: vsp += (xxxxxx << 2) + 4
                vsp += ((op & 0x3F) << 2) + 4
                i += 1

            elif (op & 0xC0) == 0x40:
                # 01xxxxxx: vsp -= (xxxxxx << 2) + 4
                vsp -= ((op & 0x3F) << 2) + 4
                i += 1

            elif (op & 0xF0) == 0x80:
                # 1000iiii iiiiiiii: Pop registers by mask
                if i + 1 >= len(bytecodes):
                    break
                mask_hi = op & 0x0F
                mask_lo = bytecodes[i + 1]
                mask = (mask_hi << 8) | mask_lo
                i += 2

                if mask == 0:
                    # 10000000 00000000 = Refuse to unwind
                    return None

                # Bits [11:4] map to r4-r11, bits [3:0] map to r12-r15
                for bit in range(12):
                    if mask & (1 << bit):
                        if bit < 8:
                            reg = 4 + bit  # r4-r11
                        else:
                            reg = 12 + (bit - 8)  # r12-r15
                        try:
                            vrs[reg] = read_memory(vsp)
                        except Exception:
                            return None
                        vsp += 4
                        if reg == 15:
                            pc_set = True

            elif (op & 0xF0) == 0x90:
                # 1001nnnn: vsp = r[nnnn] (nnnn != 13, 15)
                reg = op & 0x0F
                if reg == 13 or reg == 15:
                    # Reserved
                    i += 1
                    continue
                vsp = vrs.get(reg, 0)
                i += 1

            elif (op & 0xF8) == 0xA0:
                # 10100nnn: Pop r4-r[4+nnn]
                count = (op & 0x07) + 1
                for r in range(4, 4 + count):
                    try:
                        vrs[r] = read_memory(vsp)
                    except Exception:
                        return None
                    vsp += 4
                i += 1

            elif (op & 0xF8) == 0xA8:
                # 10101nnn: Pop r4-r[4+nnn], r14
                count = (op & 0x07) + 1
                for r in range(4, 4 + count):
                    try:
                        vrs[r] = read_memory(vsp)
                    except Exception:
                        return None
                    vsp += 4
                try:
                    vrs[14] = read_memory(vsp)
                except Exception:
                    return None
                vsp += 4
                i += 1

            elif op == 0xB0:
                # 10110000: Finish
                break

            elif op == 0xB1:
                # 10110001 0000iiii: Pop integer registers under mask
                if i + 1 >= len(bytecodes):
                    break
                mask = bytecodes[i + 1]
                i += 2

                if mask == 0 or (mask & 0xF0):
                    # Spare / reserved
                    continue

                for bit in range(4):
                    if mask & (1 << bit):
                        try:
                            vrs[bit] = read_memory(vsp)  # r0-r3
                        except Exception:
                            return None
                        vsp += 4

            elif op == 0xB2:
                # 10110010 uleb128: vsp += 0x204 + (uleb128 << 2)
                i += 1
                uleb_val = 0
                shift = 0
                while i < len(bytecodes):
                    b = bytecodes[i]
                    uleb_val |= (b & 0x7F) << shift
                    i += 1
                    if not (b & 0x80):
                        break
                    shift += 7
                vsp += 0x204 + (uleb_val << 2)

            elif op == 0xB3:
                # 10110011 sssscccc: Pop VFP D[s]-D[s+c] (FSTMFDX style, +4 pad)
                if i + 1 >= len(bytecodes):
                    break
                operand = bytecodes[i + 1]
                s = (operand >> 4) & 0x0F
                c = operand & 0x0F
                vsp += (c + 1) * 8 + 4  # 8 bytes per D-reg + 4 pad
                i += 2

            elif (op & 0xF8) == 0xB8:
                # 10111nnn: Pop VFP D[8]-D[8+nnn] (FSTMFDX)
                n = op & 0x07
                vsp += (n + 1) * 8 + 4
                i += 1

            elif (op & 0xF8) == 0xC0:
                if op == 0xC6:
                    # 11000110 sssscccc: Pop WMMX wR[s]-wR[s+c]
                    if i + 1 >= len(bytecodes):
                        break
                    operand = bytecodes[i + 1]
                    c = operand & 0x0F
                    vsp += (c + 1) * 8
                    i += 2
                elif op == 0xC7:
                    # 11000111 0000iiii: Pop WMMX wCGR registers
                    if i + 1 >= len(bytecodes):
                        break
                    mask = bytecodes[i + 1]
                    if mask and not (mask & 0xF0):
                        for bit in range(4):
                            if mask & (1 << bit):
                                vsp += 4
                    i += 2
                elif op == 0xC8:
                    # 11001000 sssscccc: Pop VFP D[s]-D[s+c] (VPUSH style)
                    if i + 1 >= len(bytecodes):
                        break
                    operand = bytecodes[i + 1]
                    c = operand & 0x0F
                    vsp += (c + 1) * 8
                    i += 2
                elif op == 0xC9:
                    # 11001001 sssscccc: Pop VFP D[s]-D[s+c] (VPUSH, D16-D31)
                    if i + 1 >= len(bytecodes):
                        break
                    operand = bytecodes[i + 1]
                    c = operand & 0x0F
                    vsp += (c + 1) * 8
                    i += 2
                else:
                    # Skip unknown C0 opcodes
                    i += 1

            elif (op & 0xF8) == 0xD0:
                # 11010nnn: Pop VFP D[8]-D[8+nnn] (VPUSH style)
                n = op & 0x07
                vsp += (n + 1) * 8
                i += 1

            else:
                # Unknown opcode — skip
                i += 1

        # Apply results
        vrs[13] = vsp

        # Implicit Finish: if PC was not explicitly popped, copy LR → PC
        if not pc_set:
            vrs[15] = vrs.get(14, 0) & ~1  # Clear Thumb bit

        # Clear Thumb bit on recovered PC
        if 15 in vrs:
            vrs[15] = vrs[15] & ~1

        return vrs


# ─── Unified Precise Unwinder ────────────────────────────────────────────────


class PreciseUnwinder:
    """Facade that combines EHABI and DWARF CFI unwinders.

    Initialization priority:
    1. Try EHABI (.ARM.exidx) — preferred for AC6/GCC
    2. Try DWARF CFI (.debug_frame) — works for all including AC5
    3. If neither available, raises ValueError

    Frame unwinding tries EHABI first, falls back to DWARF CFI.
    """

    def __init__(self, elf_path: str):
        self._ehabi: Optional[EHABIUnwinder] = None
        self._dwarf: Optional[DWARFCFIUnwinder] = None
        self._elf_path = elf_path

        # Try EHABI first
        try:
            self._ehabi = EHABIUnwinder(elf_path)
            logger.info("EHABI unwinder loaded (%d entries)",
                        len(self._ehabi._entries))
        except (ValueError, Exception) as e:
            logger.debug("EHABI not available: %s", e)

        # Try DWARF CFI
        try:
            self._dwarf = DWARFCFIUnwinder(elf_path)
            logger.info("DWARF CFI unwinder loaded (%d FDEs)",
                        len(self._dwarf._fde_list))
        except (ValueError, Exception) as e:
            logger.debug("DWARF CFI not available: %s", e)

        if self._ehabi is None and self._dwarf is None:
            raise ValueError(
                "No unwind info found in ELF "
                "(need .ARM.exidx or .debug_frame)")

    @property
    def method(self) -> str:
        """Describe available unwinding methods."""
        methods = []
        if self._ehabi:
            methods.append("EHABI")
        if self._dwarf:
            methods.append("DWARF_CFI")
        return "+".join(methods)

    def unwind_frame(self, registers: dict[int, int],
                     read_memory: ReadMemoryFunc) -> tuple[Optional[dict[int, int]], str]:
        """Unwind one frame. Returns (new_registers, method_used) or (None, reason).

        Tries EHABI first (if available), then DWARF CFI.
        """
        # Try EHABI first (more reliable for AC6/GCC)
        if self._ehabi is not None:
            result = self._ehabi.unwind_frame(registers, read_memory)
            if result is not None:
                return (result, "ehabi")

        # Fall back to DWARF CFI
        if self._dwarf is not None:
            result = self._dwarf.unwind_frame(registers, read_memory)
            if result is not None:
                return (result, "dwarf_cfi")

        return (None, "no_unwind_info")

    def unwind(self, initial_registers: dict[int, int],
               read_memory: ReadMemoryFunc,
               max_frames: int = 20) -> list[dict]:
        """Perform full stack unwinding from initial register state.

        Args:
            initial_registers: Starting registers {reg_num: value}.
                               Must include at least: 13(SP), 14(LR), 15(PC)
            read_memory: Function to read a 32-bit word from memory.
            max_frames: Maximum number of frames to unwind.

        Returns:
            List of frame dicts, each containing:
            - pc: Program counter for this frame
            - sp: Stack pointer for this frame
            - method: Unwinding method used ("ehabi", "dwarf_cfi")
            - frame_num: Frame index (0 = current)
        """
        frames = []
        regs = dict(initial_registers)
        seen_pcs: set[int] = set()

        for frame_num in range(max_frames):
            pc = regs.get(15, 0)
            sp = regs.get(13, 0)

            if pc == 0:
                break

            # Detect infinite loop
            frame_key = (pc, sp)
            if frame_key in seen_pcs:
                break
            seen_pcs.add(frame_key)

            if frame_num == 0:
                frames.append({
                    "pc": pc,
                    "sp": sp,
                    "method": "current",
                    "frame_num": 0,
                })
            else:
                frames.append({
                    "pc": pc,
                    "sp": sp,
                    "method": method_used,  # noqa: F821 - set in previous iteration
                    "frame_num": frame_num,
                })

            # Try to unwind to caller
            new_regs, method_used = self.unwind_frame(regs, read_memory)
            if new_regs is None:
                break

            # Sanity checks
            new_pc = new_regs.get(15, 0)
            new_sp = new_regs.get(13, 0)

            # PC must be non-zero
            if new_pc == 0:
                break

            # SP must not decrease (stack grows down, unwinding goes up)
            if new_sp < sp and new_sp != 0:
                # Allow small SP decrease only for exception frames
                if sp - new_sp > 1024:
                    break

            regs = new_regs

        return frames
