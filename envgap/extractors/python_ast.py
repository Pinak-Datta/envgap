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

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if _inherits_base_settings(node):
            self.usages.extend(_settings_field_usages(node, self.path))
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


def _inherits_base_settings(node: ast.ClassDef) -> bool:
    return any(_base_name(base) == "BaseSettings" for base in node.bases)


def _base_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None


def _settings_field_usages(node: ast.ClassDef, path: Path) -> list[CodeUsage]:
    usages: list[CodeUsage] = []
    env_prefix = _settings_env_prefix(node)
    for statement in node.body:
        if not isinstance(statement, ast.AnnAssign):
            continue
        if not isinstance(statement.target, ast.Name):
            continue
        field_name = statement.target.id
        if field_name == "model_config" or field_name.startswith("_") or _is_class_var(statement.annotation):
            continue
        keys = _settings_field_aliases(statement.value) or [f"{env_prefix}{field_name.upper()}"]
        required = _settings_field_required(statement.value)
        for key in keys:
            usages.append(
                CodeUsage(
                    key=key,
                    path=path,
                    line=statement.lineno,
                    required=required,
                    source=f"{node.name}.{field_name} (Pydantic BaseSettings)",
                )
            )
    return usages


def _settings_env_prefix(node: ast.ClassDef) -> str:
    env_prefix = ""
    for statement in node.body:
        value = _model_config_value(statement)
        if value is None:
            continue
        env_prefix = _config_env_prefix(value) or ""
    return env_prefix


def _model_config_value(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "model_config" for target in statement.targets
    ):
        return statement.value
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name) and statement.target.id == "model_config":
        return statement.value
    return None


def _config_env_prefix(value: ast.AST) -> str | None:
    if isinstance(value, ast.Call) and _call_name(value.func) in {"SettingsConfigDict", "ConfigDict"}:
        return _string_keyword(value, "env_prefix") or ""
    if isinstance(value, ast.Dict):
        for key, item in zip(value.keys, value.values):
            if key is not None and _string_literal(key) == "env_prefix":
                return _string_literal(item) or ""
        return ""
    return None


def _settings_field_aliases(value: ast.AST | None) -> list[str]:
    if not isinstance(value, ast.Call) or _call_name(value.func) != "Field":
        return []
    validation_aliases = _alias_keyword_values(value, "validation_alias")
    if validation_aliases:
        return validation_aliases
    return _alias_keyword_values(value, "alias")


def _alias_keyword_values(node: ast.Call, name: str) -> list[str]:
    keyword = next((kw for kw in node.keywords if kw.arg == name), None)
    if keyword is None:
        return []
    literal = _string_literal(keyword.value)
    if literal is not None:
        return [literal]
    if isinstance(keyword.value, ast.Call) and _call_name(keyword.value.func) == "AliasChoices":
        return [value for arg in keyword.value.args if (value := _string_literal(arg)) is not None]
    return []


def _string_keyword(node: ast.Call, name: str) -> str | None:
    keyword = next((kw for kw in node.keywords if kw.arg == name), None)
    if keyword is None:
        return None
    return _string_literal(keyword.value)


def _settings_field_required(value: ast.AST | None) -> bool:
    if value is None:
        return True
    if _is_ellipsis(value):
        return True
    if isinstance(value, ast.Call) and _call_name(value.func) == "Field":
        return _field_call_required(value)
    return False


def _field_call_required(node: ast.Call) -> bool:
    default_keyword = next((kw for kw in node.keywords if kw.arg == "default"), None)
    if default_keyword:
        return _is_ellipsis(default_keyword.value)
    if any(kw.arg == "default_factory" for kw in node.keywords):
        return False
    if node.args:
        return _is_ellipsis(node.args[0])
    return True


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_ellipsis(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _is_class_var(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        return _base_name(node.value) == "ClassVar"
    return _base_name(node) == "ClassVar"
