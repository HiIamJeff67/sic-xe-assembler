from __future__ import annotations

import argparse
from pathlib import Path

from errors.error import ArgumentError, FileSystemError
from definitions import AssemblerArguments

class AssemblerIoManager:
    def _validate_source_path(self, source_path: Path) -> None:
        if not source_path.exists():
            raise ArgumentError(f"Source file was not found: {source_path}")
        if not source_path.is_file():
            raise ArgumentError(f"Source path is not a regular file: {source_path}")
        if source_path.suffix.lower() != ".asm":
            raise ArgumentError(f"Source file extension must be .asm: {source_path}")

    def _resolve_output_path(self, source_path: Path, output_argument: str | None) -> Path:
        if output_argument is None:
            return source_path.with_suffix(".obj")

        output_path = Path(output_argument)
        if output_path.suffix.lower() != ".obj":
            raise ArgumentError(f"Output file extension must be .obj: {output_path}")
        return output_path

    def get_arguments(self) -> AssemblerArguments:
        parser = argparse.ArgumentParser(description="SIC/XE Assembler")
        parser.add_argument("source", help="Input assembly source file")
        parser.add_argument("-o", "--output", help="Destination object file")
        parser.add_argument("--sic", action="store_true", default=False, help="Compile in SIC mode")
        parsed_args = parser.parse_args()

        source_path = Path(parsed_args.source)
        self._validate_source_path(source_path)
        output_path = self._resolve_output_path(source_path, parsed_args.output)

        return AssemblerArguments(
            source_path=source_path,
            output_path=output_path,
            sic_mode=parsed_args.sic,
        )

    def write_output_records(self, records: list[str], output_path: Path) -> None:
        if not records:
            raise FileSystemError("No object records generated; skip writing output file.")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="") as output_file:
                for record in records:
                    output_file.write(record + "\n")
        except PermissionError as error:
            raise FileSystemError(f"Permission denied while writing output file: {output_path}") from error
        except OSError as error:
            raise FileSystemError(f"Unable to write output file {output_path}: {error}") from error
