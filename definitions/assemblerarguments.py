from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class AssemblerArguments:
    source_path: Path
    output_path: Path
    sic_mode: bool
