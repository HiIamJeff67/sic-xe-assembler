from __future__ import annotations

import subprocess
import sys

from test.caseloader import PROJECT_ROOT, CaseSpec

def test_generated_object_program_matches_target(case_spec: CaseSpec, tmp_path) -> None:
    output_path = tmp_path / f"{case_spec.name}.obj"

    command = [
        sys.executable,
        "assembler.py",
        str(case_spec.asm_path),
        "-o",
        str(output_path),
    ]
    if case_spec.sic_mode:
        command.append("--sic")

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"assembler failed for case '{case_spec.name}'.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    assert output_path.exists(), f"No output files exported: {output_path}"

    actual_lines = output_path.read_text(encoding="utf-8").splitlines()
    expected_lines = case_spec.obj_path.read_text(encoding="utf-8").splitlines()

    assert actual_lines == expected_lines
