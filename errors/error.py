from __future__ import annotations

from typing import Optional

class AssemblerError(Exception):
    """Base error for SIC/XE assembler failures."""


class ArgumentError(AssemblerError):
    """Raised for invalid command line arguments."""


class FileSystemError(AssemblerError):
    """Raised for file system read/write failures."""


class ParsingError(AssemblerError):
    """Raised when source code parsing fails."""

    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        source_line: Optional[str] = None,
    ) -> None:
        details: list[str] = [message]
        if line_number is not None:
            details.append(f"line {line_number}")
        if source_line is not None:
            details.append(f"source: {source_line.rstrip()}")
        super().__init__(" | ".join(details))


class Pass1Error(AssemblerError):
    """Raised for Pass 1 (LOCCTR / symbol table) errors."""


class Pass2Error(AssemblerError):
    """Raised for Pass 2 (object code generation) errors."""


class SicModeError(Pass2Error):
    """Raised when SIC mode encounters SIC/XE-only syntax."""


class SymbolResolutionError(Pass2Error):
    """Raised when symbols or operand references cannot be resolved."""


class RangeValidationError(AssemblerError):
    """Raised when values exceed allowed ranges."""


class DuplicateSymbolError(Pass1Error):
    """Raised for duplicated labels in symbol table."""


class DirectiveOrderError(Pass1Error):
    """Raised when START / END directive order is invalid."""


class RegisterOperandError(Pass2Error):
    """Raised for malformed register operands in format 2."""


class AddressingModeError(Pass2Error):
    """Raised for illegal or unreachable addressing mode combinations."""
