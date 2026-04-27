from __future__ import annotations

from math import ceil

from constants import DIRECTIVES, HEX_DIGITS, MAX_RESERVE_VALUE, MEMORY_LIMIT, OPCODES
from errors.error import DirectiveOrderError, DuplicateSymbolError, Pass1Error, RangeValidationError
from passers.passer import Passer
from definitions import ParsedLine, Pass1Result

class Passer1(Passer[Pass1Result]):
    def __init__(self, lines: list[ParsedLine]) -> None:
        self.lines = lines
        self.LOCCTR = 0
        self.start_address = 0
        self.program_name: str | None = None
        self.symbol_table: dict[str, int] = {}

    def _parse_start_address(self, operand: str, line_number: int) -> int:
        compact_operand = "".join(operand.split()).upper()
        if compact_operand.startswith("0X"):
            compact_operand = compact_operand[2:]

        if not compact_operand:
            raise DirectiveOrderError(f"START requires an address at line {line_number}.")
        if any(character not in HEX_DIGITS for character in compact_operand):
            raise DirectiveOrderError(
                f"START address must be hexadecimal at line {line_number}: {operand}"
            )

        start_address = int(compact_operand, 16)
        if not (0 <= start_address <= MEMORY_LIMIT - 1):
            raise RangeValidationError(
                f"START address exceeds memory range at line {line_number}: {start_address:06X}"
            )
        return start_address

    def _parse_reserve_value(self, operand: str, line_number: int) -> int:
        normalized_operand = operand.strip()
        if normalized_operand.startswith("-"):
            raise RangeValidationError(
                f"Reserve directive cannot use negative value at line {line_number}: {operand}"
            )

        if normalized_operand.startswith("+"):
            normalized_operand = normalized_operand[1:]

        normalized_operand = "".join(normalized_operand.split())
        if not normalized_operand.isdigit():
            raise Pass1Error(f"Reserve value must be decimal at line {line_number}: {operand}")

        reserve_value = int(normalized_operand, 10)
        if reserve_value > MAX_RESERVE_VALUE:
            raise RangeValidationError(
                f"Reserve value exceeds 15-bit limit at line {line_number}: {reserve_value}"
            )
        return reserve_value

    def _calculate_byte_length(self, operand: str, line_number: int) -> int:
        if operand.startswith("X'"):
            return ceil(len(operand[2:-1]) / 2)
        if operand.startswith("C'"):
            return len(operand[2:-1])
        raise Pass1Error(f"Invalid BYTE operand at line {line_number}: {operand}")

    def _consume_directive(self, line: ParsedLine) -> None:
        if line.opcode == "WORD":
            self.LOCCTR += 3
        elif line.opcode == "BYTE":
            self.LOCCTR += self._calculate_byte_length(line.operand, line.number)
        elif line.opcode == "RESW":
            self.LOCCTR += 3 * self._parse_reserve_value(line.operand, line.number)
        elif line.opcode == "RESB":
            self.LOCCTR += self._parse_reserve_value(line.operand, line.number)

    def _register_label(self, line: ParsedLine) -> None:
        if not line.label:
            return
        if line.label in self.symbol_table:
            raise DuplicateSymbolError(f"Label redefined at line {line.number}: {line.label}")
        self.symbol_table[line.label] = self.LOCCTR

    def _consume_opcode(self, line: ParsedLine) -> None:
        opcode_token = line.opcode
        is_extended = opcode_token.startswith("+")
        if is_extended:
            opcode_token = opcode_token[1:]

        opcode_info = OPCODES.get(opcode_token)
        if opcode_info is None:
            raise Pass1Error(f"Unknown opcode/directive at line {line.number}: {line.opcode}")

        _, fmt, _ = opcode_info
        if is_extended and fmt != 3:
            raise Pass1Error(
                f"Only format-3 instructions may use '+' at line {line.number}: {line.opcode}"
            )

        self.LOCCTR += 4 if is_extended else fmt

    def _validate_program_size(self, line_number: int) -> None:
        used_memory = self.LOCCTR - self.start_address
        if used_memory > MEMORY_LIMIT:
            raise RangeValidationError(
                f"Program size overflow at line {line_number}: {used_memory} bytes exceeds 1MB"
            )

    def run(self) -> Pass1Result:
        if not self.lines:
            raise Pass1Error("No parsed statements available for Pass1.")
        if self.lines[0].opcode != "START":
            raise DirectiveOrderError("First statement must be START.")

        has_start = False
        has_end = False

        for line in self.lines:
            if line.opcode == "START":
                if has_start:
                    raise DirectiveOrderError(f"Duplicate START directive at line {line.number}.")

                self.start_address = self._parse_start_address(line.operand, line.number)
                self.LOCCTR = self.start_address
                line.loc = self.LOCCTR
                has_start = True
                if line.label:
                    self.program_name = line.label
                continue

            line.loc = self.LOCCTR
            self._register_label(line)

            if line.opcode == "END":
                has_end = True
                break

            if line.opcode in DIRECTIVES:
                self._consume_directive(line)
            else:
                self._consume_opcode(line)

            self._validate_program_size(line.number)

        if not has_end:
            raise DirectiveOrderError("END directive is missing.")

        return Pass1Result(
            start_address=self.start_address,
            program_length=self.LOCCTR - self.start_address,
            program_name=self.program_name,
            symbol_table=self.symbol_table,
        )
