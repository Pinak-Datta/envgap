from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CodeUsage:
    key: str
    path: Path
    line: int
    required: bool
    source: str


@dataclass
class ExpectedVar:
    key: str
    documented_in: Path | None = None
    code_usages: list[CodeUsage] = field(default_factory=list)

    @property
    def required(self) -> bool:
        return any(usage.required for usage in self.code_usages)

