from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    title: str
    message: str
    key: str | None = None
    path: Path | None = None
    line: int | None = None
    suggestion: str | None = None
    details: list[str] = field(default_factory=list)

