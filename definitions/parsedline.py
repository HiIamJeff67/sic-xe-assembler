from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedLine:
    number: int
    label: str
    opcode: str
    operand: str
    loc: Optional[int] = None
