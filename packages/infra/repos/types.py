
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, List

T = TypeVar("T")

@dataclass(slots=True)
class PageParams:
    page: int = 1
    size: int = 20

@dataclass(slots=True)
class Page(Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        if self.size <= 0:
            return 1 if self.total > 0 else 0
        return (self.total + self.size - 1) // self.size
