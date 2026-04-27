from __future__ import annotations

import json
from pathlib import Path
from definitions import CaseSpec

VALID_MODES = {"sic", "sicxe"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DIR = PROJECT_ROOT / "test" / "original"
TARGET_DIR = PROJECT_ROOT / "test" / "target"
CASE_CONFIG_PATH = PROJECT_ROOT / "test" / "cases.json"


def normalize_case_name(raw_name: str) -> str:
    file_name = Path(raw_name).name
    lowered = file_name.lower()
    if lowered.endswith(".asm") or lowered.endswith(".obj"):
        return Path(file_name).stem
    return file_name


def _collect_case_names(directory: Path, suffix: str) -> set[str]:
    if not directory.exists():
        return set()

    names: set[str] = set()
    for file_path in directory.glob(f"*{suffix}"):
        names.add(file_path.stem)
    return names


def _deduplicate_case_names(raw_names: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw_name in raw_names:
        name = normalize_case_name(raw_name)
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def _load_mode_overrides() -> tuple[dict[str, str], list[str]]:
    if not CASE_CONFIG_PATH.exists():
        return {}, []

    try:
        content = json.loads(CASE_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {}, [f"test/cases.json failed to parse JSON: {error}"]

    if not isinstance(content, dict):
        return {}, ["test/cases.json top format must be object"]

    raw_modes = content.get("modes", {})
    if not isinstance(raw_modes, dict):
        return {}, ["the modes field of test/cases.json must be object"]

    problems: list[str] = []
    mode_overrides: dict[str, str] = {}
    for raw_name, raw_mode in raw_modes.items():
        if not isinstance(raw_name, str):
            problems.append("The modes key of test/cases.json must be a string")
            continue
        if not isinstance(raw_mode, str):
            problems.append(f"The mode of case '{raw_name}' must be a string")
            continue

        normalized_mode = raw_mode.strip().lower()
        if normalized_mode not in VALID_MODES:
            problems.append(
                f"The mode of case '{raw_name}' must be either 'sic' or 'sicxe', got '{raw_mode}'"
            )
            continue

        mode_overrides[normalize_case_name(raw_name)] = normalized_mode

    return mode_overrides, problems


def resolve_cases(selected_case_names: list[str], default_mode: str) -> tuple[list[CaseSpec], list[str]]:
    normalized_default_mode = default_mode.strip().lower()
    if normalized_default_mode not in VALID_MODES:
        return [], [f"Invalid default mode: {default_mode}, it must be either 'sic' or 'sicxe'"]

    mode_overrides, config_problems = _load_mode_overrides()

    if selected_case_names:
        case_names = _deduplicate_case_names(selected_case_names)
    else:
        case_names = sorted(
            _collect_case_names(ORIGINAL_DIR, ".asm") | _collect_case_names(TARGET_DIR, ".obj")
        )

    resolved_cases: list[CaseSpec] = []
    missing_problems = list(config_problems)

    for case_name in case_names:
        asm_path = ORIGINAL_DIR / f"{case_name}.asm"
        obj_path = TARGET_DIR / f"{case_name}.obj"

        if not asm_path.exists():
            missing_problems.append(f"case '{case_name}' require test input file of: test/original/{case_name}.asm")
        if not obj_path.exists():
            missing_problems.append(f"case '{case_name}' require expected ouput file of: test/target/{case_name}.obj")
        if not asm_path.exists() or not obj_path.exists():
            continue

        mode_text = mode_overrides.get(case_name, normalized_default_mode)
        resolved_cases.append(
            CaseSpec(
                name=case_name,
                asm_path=asm_path,
                obj_path=obj_path,
                sic_mode=(mode_text == "sic"),
            )
        )

    return resolved_cases, missing_problems
