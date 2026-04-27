from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CaseSpec:
    name: str
    asm_path: Path
    obj_path: Path
    sic_mode: bool