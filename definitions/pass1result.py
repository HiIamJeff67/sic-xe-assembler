from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Pass1Result:
    start_address: int
    program_length: int
    program_name: Optional[str]
    symbol_table: dict[str, int]
