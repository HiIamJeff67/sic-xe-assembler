from __future__ import annotations

import argparse
from pathlib import Path

class ObjectCodeComparator:
    def compare(self, source_path: Path, target_path: Path) -> bool:
        source_lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
        target_lines = target_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if len(source_lines) != len(target_lines):
            print(
                "Comparison mismatch: "
                f"line count differs ({len(source_lines)} vs {len(target_lines)})."
            )
            return False

        if source_lines and source_lines[-1].endswith("\n"):
            source_lines[-1] = source_lines[-1].rstrip("\n")
        if target_lines and target_lines[-1].endswith("\n"):
            target_lines[-1] = target_lines[-1].rstrip("\n")

        for line_index, (source_line, target_line) in enumerate(zip(source_lines, target_lines), start=1):
            if len(source_line) != len(target_line):
                print(
                    "Comparison mismatch: "
                    f"line {line_index} has different lengths ({len(source_line)} vs {len(target_line)})."
                )
                return False

            for column_index, (source_character, target_character) in enumerate(
                zip(source_line, target_line),
                start=1,
            ):
                if source_character != target_character:
                    print(
                        "Comparison mismatch: "
                        f"line {line_index}, column {column_index} differs "
                        f"('{source_character}' != '{target_character}')."
                    )
                    return False

        return True


def parse_arguments() -> dict[str, Path]:
    parser = argparse.ArgumentParser(description="Compare two SIC/XE object files")
    parser.add_argument("source", help="generated object file path")
    parser.add_argument("target", help="expected object file path")
    parsed_args = parser.parse_args()

    source_path = Path(parsed_args.source)
    target_path = Path(parsed_args.target)

    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target path does not exist: {target_path}")

    return {"source": source_path, "target": target_path}


def main() -> None:
    try:
        arguments = parse_arguments()
        comparator = ObjectCodeComparator()
        is_identical = comparator.compare(arguments["source"], arguments["target"])
        if is_identical:
            print(
                "Comparison complete: object files are identical. "
                f"({arguments['source']} == {arguments['target']})"
            )
        else:
            print(
                "Comparison complete: object files differ. "
                f"({arguments['source']} != {arguments['target']})"
            )
            raise SystemExit(1)
    except Exception as error:
        print(f"Object-code comparison aborted: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
