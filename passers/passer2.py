from __future__ import annotations

from math import ceil

from constants import (
    BASE_RELATIVE_MAX,
    BASE_RELATIVE_MIN,
    DIRECTIVES,
    FORMAT3_IMMEDIATE_MAX,
    FORMAT3_IMMEDIATE_MIN,
    FORMAT4_IMMEDIATE_MAX,
    FORMAT4_IMMEDIATE_MIN,
    OPCODES,
    PC_RELATIVE_MAX,
    PC_RELATIVE_MIN,
    REGISTERS,
    SHIFT_MAX,
    SHIFT_MIN,
    SIC_DIRECT_MAX,
    SIC_DIRECT_MIN,
    SVC_MAX,
    SVC_MIN,
    TEXT_RECORD_HEX_LIMIT,
    WORD_MAX,
    WORD_MIN,
)
from errors.error import (
    AddressingModeError,
    Pass2Error,
    RangeValidationError,
    RegisterOperandError,
    SicModeError,
    SymbolResolutionError,
)
from passers.passer import Passer
from definitions import ParsedLine, Pass1Result

class Passer2(Passer[list[str]]):
    FORMAT2_SHIFT = {"SHIFTL", "SHIFTR"}

    def __init__(self, sic_mode: bool, lines: list[ParsedLine], pass1_result: Pass1Result) -> None:
        self.sic_mode = sic_mode
        self.lines = lines
        self.pass1_result = pass1_result

        self.base_address: int | None = None
        self.execution_address = pass1_result.start_address

        self.modification_records: list[str] = []
        self.text_records: list[tuple[int, str]] = []
        self.text_start: int | None = None
        self.text_data = ""

    def _normalize_signed_decimal(self, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            return ""

        if stripped_value[0] in {"+", "-"}:
            sign = stripped_value[0]
            digits = "".join(stripped_value[1:].split())
            return sign + digits

        return "".join(stripped_value.split())

    def _is_decimal(self, value: str) -> bool:
        normalized_value = self._normalize_signed_decimal(value)
        if not normalized_value:
            return False
        if normalized_value[0] in {"+", "-"}:
            return normalized_value[1:].isdigit()
        return normalized_value.isdigit()

    def _parse_decimal(self, value: str, line_number: int, field_name: str) -> int:
        normalized_value = self._normalize_signed_decimal(value)
        if not self._is_decimal(normalized_value):
            raise SymbolResolutionError(
                f"{field_name} expects a decimal value at line {line_number}: {value}"
            )
        return int(normalized_value, 10)

    def _resolve_symbol_or_decimal(
        self,
        operand: str,
        line_number: int,
        allow_decimal: bool = True,
    ) -> int:
        candidate = operand.strip()
        if not candidate:
            raise SymbolResolutionError(f"Operand is missing at line {line_number}.")

        if allow_decimal and self._is_decimal(candidate):
            return self._parse_decimal(candidate, line_number, "Operand")

        symbol_value = self.pass1_result.symbol_table.get(candidate)
        if symbol_value is not None:
            return symbol_value

        raise SymbolResolutionError(f"Symbol is undefined at line {line_number}: {candidate}")

    def _encode_byte_operand(self, operand: str, line_number: int) -> str:
        if operand.startswith("X'"):
            hex_value = operand[2:-1]
            if len(hex_value) % 2 != 0:
                raise RangeValidationError(
                    f"Hex literal length must be even at line {line_number}: {operand}"
                )
            return hex_value

        if operand.startswith("C'"):
            return "".join(f"{ord(character):02X}" for character in operand[2:-1])

        raise Pass2Error(f"BYTE operand format is invalid at line {line_number}: {operand}")

    def _encode_word_operand(self, operand: str, line_number: int) -> str:
        value = self._parse_decimal(operand, line_number, "WORD operand")
        if not (WORD_MIN <= value <= WORD_MAX):
            raise RangeValidationError(f"WORD value out of range at line {line_number}: {value}")
        return f"{(value & 0xFFFFFF):06X}"

    def _parse_indexed_operand(self, operand: str, line_number: int) -> tuple[str, bool]:
        if "," not in operand:
            cleaned_operand = operand.strip()
            if not cleaned_operand:
                raise SymbolResolutionError(f"Operand is missing at line {line_number}.")
            return cleaned_operand, False

        parts = [part.strip() for part in operand.split(",") if part.strip()]
        if len(parts) != 2 or parts[1].upper() != "X":
            raise AddressingModeError(
                f"Indexed operand must follow '<target>,X' format at line {line_number}: {operand}"
            )
        return parts[0], True

    def _encode_format2_instruction(
        self,
        opcode_name: str,
        opcode_value: int,
        operand: str,
        line_number: int,
    ) -> str:
        operands = [token.strip().upper() for token in operand.split(",") if token.strip()]

        if not operands:
            raise RegisterOperandError(f"{opcode_name} requires operand(s) at line {line_number}.")
        if len(operands) > 2:
            raise RegisterOperandError(
                f"{opcode_name} accepts at most two operands at line {line_number}: {operand}"
            )

        if opcode_name == "SVC":
            if len(operands) != 1:
                raise RegisterOperandError(f"SVC expects one operand at line {line_number}: {operand}")
            service_code = self._parse_decimal(operands[0], line_number, "SVC operand")
            if not (SVC_MIN <= service_code <= SVC_MAX):
                raise RangeValidationError(
                    f"SVC value must be between {SVC_MIN} and {SVC_MAX} at line {line_number}: {service_code}"
                )
            return f"{opcode_value:02X}{service_code:X}0"

        register_one = REGISTERS.get(operands[0])
        if register_one is None:
            raise RegisterOperandError(f"Unknown register at line {line_number}: {operands[0]}")

        register_two = 0
        if len(operands) == 2:
            if opcode_name in self.FORMAT2_SHIFT:
                shift_count = self._parse_decimal(operands[1], line_number, f"{opcode_name} shift")
                if not (SHIFT_MIN <= shift_count <= SHIFT_MAX):
                    raise RangeValidationError(
                        f"Shift count out of range [{SHIFT_MIN},{SHIFT_MAX}] at line {line_number}: {shift_count}"
                    )
                register_two = shift_count
            else:
                register_two = REGISTERS.get(operands[1], -1)
                if register_two < 0:
                    raise RegisterOperandError(f"Unknown register at line {line_number}: {operands[1]}")

        return f"{opcode_value:02X}{register_one:X}{register_two:X}"

    def _encode_format34_instruction(
        self,
        opcode: int,
        supports_sic: bool,
        is_extended: bool,
        line: ParsedLine,
        next_loc: int,
    ) -> str:
        operand_text = line.operand
        n, i, x, b, p, e = 1, 1, 0, 0, 0, 1 if is_extended else 0

        if operand_text.startswith("#"):
            if self.sic_mode:
                raise SicModeError(
                    f"SIC mode does not allow immediate addressing at line {line.number}: {operand_text}"
                )
            n, i = 0, 1
            operand_text = operand_text[1:].strip()
            if not operand_text:
                raise SymbolResolutionError(f"Immediate operand is missing at line {line.number}.")

        elif operand_text.startswith("@"):
            if self.sic_mode:
                raise SicModeError(
                    f"SIC mode does not allow indirect addressing at line {line.number}: {operand_text}"
                )
            n, i = 1, 0
            operand_text = operand_text[1:].strip()
            if not operand_text:
                raise SymbolResolutionError(f"Indirect operand is missing at line {line.number}.")

        target_operand, has_index_register = self._parse_indexed_operand(operand_text, line.number)
        if has_index_register:
            x = 1

        immediate_numeric = n == 0 and i == 1 and self._is_decimal(target_operand)
        if immediate_numeric and has_index_register:
            raise AddressingModeError(
                f"Immediate addressing cannot be combined with index register at line {line.number}: {line.operand}"
            )

        if immediate_numeric:
            target_address = self._parse_decimal(target_operand, line.number, "Immediate value")
        else:
            target_address = self._resolve_symbol_or_decimal(target_operand, line.number, allow_decimal=True)

        opcode = (opcode & 0xFC) | (n << 1) | i

        if is_extended:
            if immediate_numeric and not (FORMAT4_IMMEDIATE_MIN <= target_address <= FORMAT4_IMMEDIATE_MAX):
                raise RangeValidationError(
                    f"Format-4 immediate value out of range at line {line.number}: {target_address}"
                )

            displacement = target_address & 0xFFFFF
            if not immediate_numeric:
                if line.loc is None:
                    raise Pass2Error(
                        f"LOCCTR was not assigned before modification record generation at line {line.number}."
                    )
                self.modification_records.append(f"M{(line.loc + 1):06X}05")

            flags = (x << 3) | (b << 2) | (p << 1) | e
            total_value = (opcode << 24) | (flags << 20) | displacement
            return f"{total_value:08X}"

        if immediate_numeric:
            if not (FORMAT3_IMMEDIATE_MIN <= target_address <= FORMAT3_IMMEDIATE_MAX):
                raise RangeValidationError(
                    f"Format-3 immediate value out of range at line {line.number}: {target_address}. Use '+' extension."
                )
            displacement = target_address & 0xFFF
            flags = (x << 3) | (b << 2) | (p << 1) | e
            total_value = (opcode << 16) | (flags << 12) | displacement
            return f"{total_value:06X}"

        pc_relative = target_address - next_loc
        base_relative = target_address - self.base_address if self.base_address is not None else None

        if (not self.sic_mode) and (PC_RELATIVE_MIN <= pc_relative <= PC_RELATIVE_MAX):
            p = 1
            displacement = pc_relative & 0xFFF

        elif (
            (not self.sic_mode)
            and (base_relative is not None)
            and (BASE_RELATIVE_MIN <= base_relative <= BASE_RELATIVE_MAX)
        ):
            b = 1
            displacement = base_relative

        else:
            if self.sic_mode or (supports_sic and not is_extended and n == 1 and i == 1):
                opcode &= 0xFC
                if SIC_DIRECT_MIN <= target_address <= SIC_DIRECT_MAX:
                    total_value = (opcode << 16) | (target_address & 0x7FFF)
                    if has_index_register:
                        total_value |= 1 << 15
                    return f"{total_value:06X}"
                if self.sic_mode:
                    raise AddressingModeError(
                        f"SIC direct addressing cannot reach target at line {line.number}: {target_operand}"
                    )

            if self.base_address is None:
                raise AddressingModeError(
                    f"PC-relative addressing failed at line {line.number}; set BASE or switch to format-4."
                )

            raise AddressingModeError(f"BASE-relative addressing failed at line {line.number}.")

        flags = (x << 3) | (b << 2) | (p << 1) | e
        total_value = (opcode << 16) | (flags << 12) | displacement
        return f"{total_value:06X}"

    def _flush_text_record(self) -> None:
        if self.text_start is not None and self.text_data:
            self.text_records.append((self.text_start, self.text_data))
        self.text_start = None
        self.text_data = ""

    def _append_object_code(self, line: ParsedLine, object_code: str) -> None:
        if line.loc is None:
            raise Pass2Error(f"LOCCTR is missing in Pass2 at line {line.number}.")

        if self.text_start is None:
            self.text_start = line.loc

        if len(self.text_data) + len(object_code) > TEXT_RECORD_HEX_LIMIT:
            self._flush_text_record()
            self.text_start = line.loc

        self.text_data += object_code

    def run(self) -> list[str]:
        for line in self.lines:
            object_code = ""
            opcode_text = line.opcode

            if opcode_text == "START":
                continue

            if opcode_text == "END":
                if line.operand:
                    self.execution_address = self._resolve_symbol_or_decimal(
                        line.operand,
                        line.number,
                        allow_decimal=False,
                    )
                break

            is_extended = opcode_text.startswith("+")
            base_opcode = opcode_text[1:] if is_extended else opcode_text

            opcode_info = OPCODES.get(base_opcode)
            if opcode_info is not None:
                opcode_value, fmt, supports_sic = opcode_info

                if is_extended and fmt != 3:
                    raise Pass2Error(
                        f"'+' extension is only valid on format-3 instructions at line {line.number}: {opcode_text}"
                    )

                if fmt == 1:
                    if self.sic_mode:
                        raise SicModeError(f"SIC mode does not support opcode at line {line.number}: {line.opcode}")
                    object_code = f"{opcode_value:02X}"

                elif fmt == 2:
                    if self.sic_mode:
                        raise SicModeError(f"SIC mode does not support opcode at line {line.number}: {line.opcode}")
                    object_code = self._encode_format2_instruction(
                        base_opcode,
                        opcode_value,
                        line.operand,
                        line.number,
                    )

                elif fmt == 3:
                    if self.sic_mode and not supports_sic:
                        raise SicModeError(f"SIC mode does not support opcode at line {line.number}: {line.opcode}")

                    if base_opcode == "RSUB":
                        if line.operand:
                            raise Pass2Error(f"RSUB must not include an operand at line {line.number}.")

                        if self.sic_mode:
                            opcode_value &= 0xFC
                            object_code = f"{opcode_value:02X}0000"
                        else:
                            opcode_value = (opcode_value & 0xFC) | 0x03
                            object_code = f"{opcode_value:02X}{'100000' if is_extended else '0000'}"
                    else:
                        if not line.operand:
                            raise SymbolResolutionError(f"Operand is missing at line {line.number}.")
                        if line.loc is None:
                            raise Pass2Error(f"LOCCTR is missing in Pass2 at line {line.number}.")

                        next_loc = line.loc + (4 if is_extended else 3)
                        object_code = self._encode_format34_instruction(
                            opcode=opcode_value,
                            supports_sic=supports_sic,
                            is_extended=is_extended,
                            line=line,
                            next_loc=next_loc,
                        )

            elif base_opcode in DIRECTIVES:
                if base_opcode == "WORD":
                    if not line.operand:
                        raise Pass2Error(f"WORD requires an operand at line {line.number}.")
                    object_code = self._encode_word_operand(line.operand, line.number)

                elif base_opcode == "BYTE":
                    if not line.operand:
                        raise Pass2Error(f"BYTE requires an operand at line {line.number}.")
                    object_code = self._encode_byte_operand(line.operand, line.number)

                elif base_opcode in {"RESB", "RESW"}:
                    self._flush_text_record()
                    continue

                elif base_opcode == "BASE":
                    if self.sic_mode:
                        raise SicModeError(f"SIC mode does not support BASE at line {line.number}.")
                    self.base_address = self._resolve_symbol_or_decimal(
                        line.operand,
                        line.number,
                        allow_decimal=True,
                    )
                    continue

                else:
                    raise Pass2Error(f"Directive is not handled in Pass2 at line {line.number}: {line.opcode}")

            else:
                raise Pass2Error(f"Unknown statement at line {line.number}: {line.opcode}")

            if object_code:
                self._append_object_code(line, object_code)

        self._flush_text_record()

        program_name = (self.pass1_result.program_name or "")[:6].ljust(6)
        records = [
            f"H{program_name}{self.pass1_result.start_address:06X}{self.pass1_result.program_length:06X}"
        ]

        for address, data in self.text_records:
            byte_length = ceil(len(data) / 2)
            records.append(f"T{address:06X}{byte_length:02X}{data}")

        records.extend(self.modification_records)
        records.append(f"E{self.execution_address:06X}")
        return records
