from __future__ import annotations

import argparse
import sys

import pytest


def parse_arguments() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run SIC/XE assembler tests. Positional names map to test/original/<name>.asm and test/target/<name>.obj."
    )
    parser.add_argument(
        "cases",
        nargs="*",
        help="指定要測試的檔名（可含或不含副檔名）。例如: addexample 或 addexample.asm",
    )
    parser.add_argument(
        "--default-mode",
        default="sic",
        choices=["sic", "sicxe"],
        help="若 test/cases.json 沒指定 mode，則使用此預設。",
    )
    return parser.parse_known_args()


def main() -> None:
    parsed_args, pytest_extra_args = parse_arguments()

    pytest_args = [
        "-v",
        "test/test_object_programs.py",
        "--default-mode",
        parsed_args.default_mode,
    ]

    for case_name in parsed_args.cases:
        pytest_args.extend(["--case", case_name])

    pytest_args.extend(pytest_extra_args)

    raise SystemExit(pytest.main(pytest_args))


if __name__ == "__main__":
    main()
