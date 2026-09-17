from __future__ import annotations

import re
from pathlib import Path

from envgap.extractors.dotenv import KEY_RE
from envgap.model import CodeUsage

COMPOSE_FILENAMES = ("compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml")


def find_compose_files(root: Path) -> list[Path]:
    return [path for name in COMPOSE_FILENAMES if (path := root / name).exists()]


def scan_compose_env_usage(root: Path) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    for path in find_compose_files(root):
        usages.extend(_scan_compose_file(root, path))
    return sorted(_dedupe_usages(usages), key=lambda usage: (str(usage.path), usage.line, usage.key, usage.source))


def _scan_compose_file(root: Path, path: Path) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    blocks: list[tuple[str, int]] = []
    env_files_seen: set[Path] = set()

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return usages

    for line_number, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue

        indent = _indent(line)
        stripped = line.strip()
        while blocks and indent <= blocks[-1][1]:
            blocks.pop()

        current = blocks[-1][0] if blocks else None
        if current == "environment":
            usages.extend(_environment_usages(stripped, path, line_number))
        elif current == "env_file":
            for env_file in _env_file_entries(stripped):
                env_path = _safe_env_file_path(root, path, env_file)
                if env_path is None or env_path in env_files_seen:
                    continue
                env_files_seen.add(env_path)
                usages.extend(_scan_env_file_keys(env_path, env_file))

        key, value = _mapping_pair(stripped)
        if key == "environment":
            if value:
                usages.extend(_inline_environment_usages(value, path, line_number))
            else:
                blocks.append(("environment", indent))
        elif key == "env_file":
            if value:
                for env_file in _inline_env_file_entries(value):
                    env_path = _safe_env_file_path(root, path, env_file)
                    if env_path is None or env_path in env_files_seen:
                        continue
                    env_files_seen.add(env_path)
                    usages.extend(_scan_env_file_keys(env_path, env_file))
            else:
                blocks.append(("env_file", indent))

    return usages


def _environment_usages(stripped: str, path: Path, line: int) -> list[CodeUsage]:
    key = _environment_key(stripped)
    if key is None:
        return []
    return [
        CodeUsage(
            key=key,
            path=path,
            line=line,
            required=True,
            source="Docker Compose environment",
        )
    ]


def _inline_environment_usages(value: str, path: Path, line: int) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    for item in _split_inline_values(value):
        key = _environment_key(item)
        if key:
            usages.append(
                CodeUsage(
                    key=key,
                    path=path,
                    line=line,
                    required=True,
                    source="Docker Compose environment",
                )
            )
    return usages


def _environment_key(value: str) -> str | None:
    item = _strip_list_marker(value)
    if not item:
        return None
    if item.startswith("path:"):
        return None
    if "=" in item:
        key = item.split("=", 1)[0].strip()
    elif ":" in item:
        key = item.split(":", 1)[0].strip()
    else:
        key = item.strip()
    key = _unquote(key)
    return key if KEY_RE.match(key) else None


def _env_file_entries(stripped: str) -> list[str]:
    item = _strip_list_marker(stripped)
    if not item:
        return []
    key, value = _mapping_pair(item)
    if key == "path" and value:
        return [_unquote(value)]
    if key is not None:
        return []
    return [_unquote(item)]


def _inline_env_file_entries(value: str) -> list[str]:
    if value.startswith("[") and value.endswith("]"):
        return [_unquote(item) for item in _split_inline_values(value)]
    return [_unquote(value)]


def _scan_env_file_keys(path: Path, display_path: str) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    if not path.exists() or not path.is_file():
        return usages

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return usages

    for line_number, raw_line in enumerate(lines, start=1):
        parsed = _dotenv_key(raw_line)
        if parsed is None:
            continue
        usages.append(
            CodeUsage(
                key=parsed,
                path=path,
                line=line_number,
                required=True,
                source=f"Docker Compose env_file ({display_path})",
            )
        )
    return usages


def _dotenv_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].lstrip()
    key = stripped.split("=", 1)[0].strip()
    return key if KEY_RE.match(key) else None


def _safe_env_file_path(root: Path, compose_path: Path, value: str) -> Path | None:
    if "$" in value or value.startswith(("~", "/")):
        return None
    candidate = (compose_path.parent / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not _looks_like_env_file(candidate.name):
        return None
    return candidate


def _looks_like_env_file(name: str) -> bool:
    lowered = name.lower()
    return lowered == ".env" or lowered.startswith(".env.") or lowered.endswith(".env")


def _mapping_pair(value: str) -> tuple[str | None, str]:
    if ":" not in value:
        return None, ""
    key, rest = value.split(":", 1)
    key = _unquote(key.strip())
    if not key:
        return None, ""
    return key, rest.strip()


def _strip_list_marker(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("- "):
        stripped = stripped[2:].strip()
    return _unquote(stripped)


def _split_inline_values(value: str) -> list[str]:
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        stripped = stripped[1:-1]
    elif stripped.startswith("{") and stripped.endswith("}"):
        stripped = stripped[1:-1]
    return [item.strip() for item in stripped.split(",") if item.strip()]


def _strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
            continue
        if char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _unquote(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _dedupe_usages(usages: list[CodeUsage]) -> list[CodeUsage]:
    seen: set[tuple[str, Path, int, str]] = set()
    unique: list[CodeUsage] = []
    for usage in usages:
        key = (usage.key, usage.path, usage.line, usage.source)
        if key in seen:
            continue
        seen.add(key)
        unique.append(usage)
    return unique
