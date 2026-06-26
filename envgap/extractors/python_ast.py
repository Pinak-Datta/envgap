from __future__ import annotations

import ast
from pathlib import Path

from envgap.model import CodeUsage

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def find_python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    )


def scan_python_env_usage(root: Path) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    for path in find_python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _EnvVisitor(path)
        visitor.visit(tree)
        usages.extend(visitor.usages)
    return sorted(usages, key=lambda usage: (str(usage.path), usage.line, usage.key))


class _EnvVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.usages: list[CodeUsage] = []

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _is_os_environ(node.value):
            key = _string_literal(node.slice)
            if key:
                self.usages.append(
                    CodeUsage(
                        key=key,
                        path=self.path,
                        line=node.lineno,
                        required=True,
                        source=f'os.environ["{key}"]',
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        key = None
        source = None
        if _is_os_getenv(node.func):
            key = _first_string_arg(node)
            source = f'os.getenv("{key}")' if key else "os.getenv"
        elif _is_os_environ_get(node.func):
            key = _first_string_arg(node)
            source = f'os.environ.get("{key}")' if key else "os.environ.get"

        if key and source:
            required = len(node.args) == 1 and not any(kw.arg == "default" for kw in node.keywords)
            self.usages.append(
                CodeUsage(
                    key=key,
                    path=self.path,
                    line=node.lineno,
                    required=required,
                    source=source,
                )
            )
        self.generic_visit(node)


def _is_os_environ(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "environ"
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
    )


def _is_os_getenv(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "getenv"
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
    )


def _is_os_environ_get(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "get" and _is_os_environ(node.value)


def _first_string_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    return _string_literal(node.args[0])


def _string_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None
