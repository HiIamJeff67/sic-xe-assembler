from __future__ import annotations

import re
from pathlib import Path

from constants import DIRECTIVES, HEX_DIGITS, OPCODES
from errors.error import FileSystemError, ParsingError
from definitions import ParsedLine

class SourceParser:
    def strip_inline_comment(self, raw_line: str) -> str:
        is_inside_literal = False
        for index, character in enumerate(raw_line):
            if character == "'":
                is_inside_literal = not is_inside_literal
            elif character == "." and not is_inside_literal:
                return raw_line[:index]
        return raw_line

    def split_statement_parts(self, statement: str) -> list[str]:
        parts: list[str] = []
        cursor = 0
        length = len(statement)

        while cursor < length and statement[cursor].isspace():
            cursor += 1
        if cursor >= length:
            return parts

        start = cursor
        while cursor < length and not statement[cursor].isspace():
            cursor += 1
        parts.append(statement[start:cursor])

        while cursor < length and statement[cursor].isspace():
            cursor += 1
        if cursor >= length:
            return parts

        start = cursor
        while cursor < length and not statement[cursor].isspace():
            cursor += 1
        parts.append(statement[start:cursor])

        while cursor < length and statement[cursor].isspace():
            cursor += 1
        if cursor < length:
            parts.append(statement[cursor:].strip())

        return parts

    def normalize_opcode(self, opcode: str) -> str:
        token = opcode.strip()
        if token.startswith("+"):
            return "+" + token[1:].upper()
        return token.upper()

    def normalize_literal(self, operand: str, line_number: int, source_line: str) -> str | None:
        if "'" not in operand:
            return None

        if operand.count("'") != 2:
            raise ParsingError(
                "Literal must be wrapped by exactly two single quotes",
                line_number=line_number,
                source_line=source_line,
            )

        literal_match = re.fullmatch(r"([cCxX])\s*'(.*)'", operand)
        if literal_match is None:
            raise ParsingError(
                f"Literal format is invalid: {operand}",
                line_number=line_number,
                source_line=source_line,
            )

        literal_type = literal_match.group(1).upper()
        literal_body = literal_match.group(2)

        if literal_type == "C":
            return f"C'{literal_body}'"

        hex_body = "".join(literal_body.split()).upper()
        if not hex_body:
            raise ParsingError(
                "Hex literal cannot be empty",
                line_number=line_number,
                source_line=source_line,
            )
        if any(character not in HEX_DIGITS for character in hex_body):
            raise ParsingError(
                f"Hex literal contains illegal digits: {operand}",
                line_number=line_number,
                source_line=source_line,
            )
        return f"X'{hex_body}'"

    def normalize_operand(self, operand: str, line_number: int, source_line: str) -> str:
        normalized_operand = operand.strip()
        if not normalized_operand:
            return ""

        literal_value = self.normalize_literal(normalized_operand, line_number, source_line)
        if literal_value is not None:
            return literal_value

        if normalized_operand[0] in {"#", "@"}:
            mode_prefix = normalized_operand[0]
            payload = "".join(normalized_operand[1:].split())
            if not payload:
                raise ParsingError(
                    f"Operand is missing after '{mode_prefix}'",
                    line_number=line_number,
                    source_line=source_line,
                )
            return f"{mode_prefix}{payload}"

        if "," in normalized_operand:
            operand_parts = [part.strip() for part in normalized_operand.split(",") if part.strip()]
            if not operand_parts:
                raise ParsingError(
                    "Operand is empty",
                    line_number=line_number,
                    source_line=source_line,
                )
            return ",".join(operand_parts)

        return normalized_operand

    def parse_line(self, line_number: int, raw_line: str) -> ParsedLine | None:
        statement = self.strip_inline_comment(raw_line).rstrip("\n")
        if not statement.strip():
            return None

        parts = self.split_statement_parts(statement)

        if len(parts) == 1:
            opcode = self.normalize_opcode(parts[0])
            if opcode.lstrip("+") not in OPCODES:
                raise ParsingError(
                    f"Unknown command: {parts[0]}",
                    line_number=line_number,
                    source_line=raw_line,
                )
            return ParsedLine(number=line_number, label="", opcode=opcode, operand="")

        if len(parts) == 2:
            first_opcode = self.normalize_opcode(parts[0])
            second_opcode = self.normalize_opcode(parts[1])

            if first_opcode in DIRECTIVES or first_opcode.lstrip("+") in OPCODES:
                return ParsedLine(
                    number=line_number,
                    label="",
                    opcode=first_opcode,
                    operand=self.normalize_operand(parts[1], line_number, raw_line),
                )

            if second_opcode in OPCODES:
                return ParsedLine(number=line_number, label=parts[0], opcode=second_opcode, operand="")

            raise ParsingError(
                f"Unable to parse statement: {statement.strip()}",
                line_number=line_number,
                source_line=raw_line,
            )

        if len(parts) == 3:
            first_opcode = self.normalize_opcode(parts[0])
            second_opcode = self.normalize_opcode(parts[1])

            if first_opcode in DIRECTIVES or first_opcode.lstrip("+") in OPCODES:
                merged_operand = f"{parts[1]} {parts[2]}"
                return ParsedLine(
                    number=line_number,
                    label="",
                    opcode=first_opcode,
                    operand=self.normalize_operand(merged_operand, line_number, raw_line),
                )

            if second_opcode in DIRECTIVES or second_opcode.lstrip("+") in OPCODES:
                return ParsedLine(
                    number=line_number,
                    label=parts[0],
                    opcode=second_opcode,
                    operand=self.normalize_operand(parts[2], line_number, raw_line),
                )

            raise ParsingError(
                f"Unknown command segment: {parts[1]}",
                line_number=line_number,
                source_line=raw_line,
            )

        raise ParsingError(
            "Statement format is not supported",
            line_number=line_number,
            source_line=raw_line,
        )

    def parse_source(self, source_path: Path) -> list[ParsedLine]:
        try:
            raw_lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except OSError as error:
            raise FileSystemError(f"Could not open source file {source_path}: {error}") from error

        parsed_lines: list[ParsedLine] = []
        for line_number, raw_line in enumerate(raw_lines, start=1):
            parsed_line = self.parse_line(line_number, raw_line)
            if parsed_line is not None:
                parsed_lines.append(parsed_line)

        if not parsed_lines:
            raise ParsingError("Source file does not contain any valid assembly statements")

        return parsed_lines
