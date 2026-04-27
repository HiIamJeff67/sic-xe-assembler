from __future__ import annotations

import pytest

from test.caseloader import resolve_cases

def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("sicxe-test-options")
    group.addoption(
        "--case",
        action="append",
        default=[],
        metavar="NAME",
        help="test specific case(repeatable)。例如: --case addexample --case textbookexample",
    )
    group.addoption(
        "--default-mode",
        action="store",
        default="sic",
        choices=["sic", "sicxe"],
        help="if test/cases.json does not specifiy the case mode, the default value will be used",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "case_spec" not in metafunc.fixturenames:
        return

    selected_case_names: list[str] = metafunc.config.getoption("case")
    default_mode: str = metafunc.config.getoption("default_mode")
    resolved_cases, problems = resolve_cases(selected_case_names, default_mode)

    if problems:
        formatted = "\n".join(f"- {problem}" for problem in problems)
        raise pytest.UsageError(f"Failed to check test case: \n{formatted}")

    if not resolved_cases:
        raise pytest.UsageError("Please make sure to place the original test inputs(.asm) in test/original and place the expected test results(.obj) in test/target。")

    metafunc.parametrize("case_spec", resolved_cases, ids=[case.name for case in resolved_cases])
