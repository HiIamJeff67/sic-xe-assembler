from __future__ import annotations

from errors.error import AssemblerError
from passers import Passer1, Passer2
from lib.iomanager import AssemblerIoManager
from lib.sourceparser import SourceParser
from definitions import AssemblerArguments

class Assembler:
    def __init__(self, io_manager: AssemblerIoManager | None = None, source_parser: SourceParser | None = None) -> None:
        self.io_manager = io_manager or AssemblerIoManager()
        self.source_parser = source_parser or SourceParser()

    def assemble(self, arguments: AssemblerArguments) -> list[str]:
        parsed_lines = self.source_parser.parse_source(arguments.source_path)
        pass1_result = Passer1(parsed_lines).run()
        object_records = Passer2(arguments.sic_mode, parsed_lines, pass1_result).run()
        self.io_manager.write_output_records(object_records, arguments.output_path)
        return object_records


def main() -> None:
    assembler = Assembler()
    try:
        arguments = assembler.io_manager.get_arguments()
        assembler.assemble(arguments)
        print(f"Assembly complete. Object program saved at: {arguments.output_path}")
    except AssemblerError as error:
        print(f"Assembly failed. Diagnostic: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
