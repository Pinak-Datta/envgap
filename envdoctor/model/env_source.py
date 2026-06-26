from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EnvVar:
    key: str
    value: str
    path: Path
    line: int
    raw: str


@dataclass
class EnvFile:
    path: Path
    vars: list[EnvVar] = field(default_factory=list)
    duplicates: dict[str, list[EnvVar]] = field(default_factory=dict)
    parse_warnings: list[str] = field(default_factory=list)

    @property
    def values(self) -> dict[str, EnvVar]:
        return {var.key: var for var in self.vars}

    def contains(self, key: str) -> bool:
        return key in self.values

