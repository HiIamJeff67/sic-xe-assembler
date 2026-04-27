from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

RunResult = TypeVar("RunResult")

class Passer(ABC, Generic[RunResult]):
    @abstractmethod
    def run(self) -> RunResult:
        raise NotImplementedError
