from __future__ import annotations

import re
from pathlib import Path

from envdoctor.model import EnvFile, EnvVar

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_dotenv(path: Path) -> EnvFile:
    env_file = EnvFile(path=path)
    seen: dict[str, list[EnvVar]] = {}

    if not path.exists():
        return env_file

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parsed = _parse_line(raw_line)
        if parsed is None:
            continue

        key, value = parsed
        if not KEY_RE.match(key):
            env_file.parse_warnings.append(f"{path}:{line_number}: skipped invalid key {key!r}")
            continue

        var = EnvVar(key=key, value=value, path=path, line=line_number, raw=raw_line)
        env_file.vars.append(var)
        seen.setdefault(key, []).append(var)

    env_file.duplicates = {key: vars_ for key, vars_ in seen.items() if len(vars_) > 1}
    return env_file


def _parse_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].lstrip()

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = _strip_inline_comment(value.strip())
    return key, _unquote(value)


def _strip_inline_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
            continue
        if char == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value

