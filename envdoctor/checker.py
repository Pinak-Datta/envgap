from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path

from envdoctor.extractors.dotenv import parse_dotenv
from envdoctor.extractors.python_ast import scan_python_env_usage
from envdoctor.model import CodeUsage, EnvFile, ExpectedVar, Finding, Severity

PLACEHOLDER_VALUES = {
    "",
    "<your-key-here>",
    "changeme",
    "change-me",
    "example",
    "insert-key-here",
    "replace-me",
    "todo",
    "your-api-key",
    "your-key",
    "your-key-here",
}

ABBREVIATIONS = {
    "db": "database",
    "cfg": "config",
    "conf": "config",
    "pwd": "password",
    "uri": "url",
}


@dataclass
class CheckResult:
    root: Path
    env_path: Path
    example_path: Path
    env_file: EnvFile
    example_file: EnvFile
    shell_env: dict[str, str]
    expected_keys: set[str]
    code_usages: list[CodeUsage]
    findings: list[Finding]

    @property
    def has_errors(self) -> bool:
        return any(finding.severity == Severity.ERROR for finding in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(finding.severity == Severity.WARNING for finding in self.findings)


def run_check(
    root: Path,
    env_file: str = ".env",
    example_file: str = ".env.example",
    environ: Mapping[str, str] | None = None,
) -> CheckResult:
    root = root.resolve()
    env_path = root / env_file
    example_path = root / example_file
    actual = parse_dotenv(env_path)
    example = parse_dotenv(example_path)
    shell_env = dict(os.environ if environ is None else environ)
    code_usages = scan_python_env_usage(root)
    expected = _expected_vars(example, code_usages)
    findings = _build_findings(actual, example, expected, code_usages, shell_env)

    return CheckResult(
        root=root,
        env_path=env_path,
        example_path=example_path,
        env_file=actual,
        example_file=example,
        shell_env=shell_env,
        expected_keys=set(expected),
        code_usages=code_usages,
        findings=findings,
    )


def _expected_vars(example: EnvFile, code_usages: list[CodeUsage]) -> dict[str, ExpectedVar]:
    expected: dict[str, ExpectedVar] = {}
    for var in example.vars:
        expected.setdefault(var.key, ExpectedVar(key=var.key, documented_in=var.path))
    for usage in code_usages:
        expected.setdefault(usage.key, ExpectedVar(key=usage.key)).code_usages.append(usage)
    return expected


def _build_findings(
    actual: EnvFile,
    example: EnvFile,
    expected: dict[str, ExpectedVar],
    code_usages: list[CodeUsage],
    shell_env: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    actual_values = actual.values
    example_values = example.values
    expected_keys = set(expected)
    actual_keys = set(actual_values)
    example_keys = set(example_values)

    if not example.path.exists():
        findings.append(
            Finding(
                code="missing_example_file",
                severity=Severity.WARNING,
                title=".env.example was not found",
                message="envdoctor could not find a documented source of expected variables.",
                path=example.path,
                suggestion="Add a .env.example file with every environment variable your app expects.",
            )
        )

    if not actual.path.exists():
        findings.append(
            Finding(
                code="missing_env_file",
                severity=Severity.WARNING,
                title=".env was not found",
                message="envdoctor could not compare local values because .env is missing.",
                path=actual.path,
                suggestion="Create .env from .env.example, or pass --env-file for a different file.",
            )
        )

    findings.extend(_duplicate_findings(actual))
    findings.extend(_duplicate_findings(example))

    for key in sorted(expected_keys - actual_keys):
        expected_var = expected[key]
        if not expected_var.required and not expected_var.documented_in:
            continue
        usage = _first_required_usage(expected_var.code_usages)
        findings.append(
            Finding(
                code="missing_key",
                severity=Severity.ERROR if expected_var.required or expected_var.documented_in else Severity.WARNING,
                title=f"{key} is missing from .env",
                message=_missing_message(key, expected_var, shell_env),
                key=key,
                path=usage.path if usage else expected_var.documented_in,
                line=usage.line if usage else None,
                suggestion=_missing_suggestion(key, shell_env),
                details=_checked_details(key, actual, example, shell_env) + _usage_details(expected_var.code_usages),
            )
        )

    for key in sorted(actual_keys - expected_keys):
        findings.append(
            Finding(
                code="undocumented_key",
                severity=Severity.WARNING,
                title=f"{key} is present but undocumented",
                message=f"{key} exists in .env but is not in .env.example and was not found in Python env usage.",
                key=key,
                path=actual_values[key].path,
                line=actual_values[key].line,
                suggestion=f"Add {key} to .env.example, or remove it from .env if it is unused.",
            )
        )

    for key, var in sorted(actual_values.items()):
        if var.value == "":
            findings.append(
                Finding(
                    code="empty_value",
                    severity=Severity.ERROR if key in expected_keys else Severity.WARNING,
                    title=f"{key} is empty",
                    message=f"{key} is defined in .env but has no value.",
                    key=key,
                    path=var.path,
                    line=var.line,
                    suggestion=f"Set a value for {key}, or remove it if the app should use a default.",
                )
            )
        elif _is_placeholder(var.value):
            findings.append(
                Finding(
                    code="placeholder_value",
                    severity=Severity.ERROR if key in expected_keys else Severity.WARNING,
                    title=f"{key} still looks like a placeholder",
                    message=f"{key} is set to {_mask_value(key, var.value)}, which does not look like a real value.",
                    key=key,
                    path=var.path,
                    line=var.line,
                    suggestion=f"Replace {key} with the real value for this environment.",
                )
            )

    for key in sorted(_required_code_keys(code_usages) - example_keys):
        usage = next(usage for usage in code_usages if usage.key == key and usage.required)
        findings.append(
            Finding(
                code="code_missing_from_example",
                severity=Severity.ERROR,
                title=f"{key} is used in code but missing from .env.example",
                message=f"{key} is required by {usage.source} but is not documented in .env.example.",
                key=key,
                path=usage.path,
                line=usage.line,
                suggestion=f"Add {key}=... to .env.example so local dev and CI know it is required.",
            )
        )

    findings.extend(_typo_findings(actual_keys, expected_keys, actual))
    findings.extend(_parse_warning_findings(actual))
    findings.extend(_parse_warning_findings(example))
    return sorted(findings, key=lambda f: (f.severity.value, f.code, f.key or "", str(f.path or ""), f.line or 0))


def _duplicate_findings(env_file: EnvFile) -> list[Finding]:
    findings: list[Finding] = []
    for key, vars_ in sorted(env_file.duplicates.items()):
        lines = ", ".join(str(var.line) for var in vars_)
        findings.append(
            Finding(
                code="duplicate_key",
                severity=Severity.ERROR,
                title=f"{key} is duplicated in {env_file.path.name}",
                message=f"{key} appears more than once in {env_file.path.name} on lines {lines}. The last value wins in many loaders.",
                key=key,
                path=env_file.path,
                line=vars_[0].line,
                suggestion=f"Keep one {key} entry in {env_file.path.name}.",
            )
        )
    return findings


def _typo_findings(actual_keys: set[str], expected_keys: set[str], actual: EnvFile) -> list[Finding]:
    findings: list[Finding] = []
    for actual_key in sorted(actual_keys - expected_keys):
        for expected_key in sorted(expected_keys - actual_keys):
            if _similar(actual_key, expected_key):
                var = actual.values[actual_key]
                findings.append(
                    Finding(
                        code="possible_typo",
                        severity=Severity.WARNING,
                        title=f"{actual_key} may be a typo for {expected_key}",
                        message=f".env contains {actual_key}, but the expected variable is {expected_key}.",
                        key=actual_key,
                        path=var.path,
                        line=var.line,
                        suggestion=f"Rename {actual_key} to {expected_key} if they represent the same setting.",
                    )
                )
    return findings


def _parse_warning_findings(env_file: EnvFile) -> list[Finding]:
    return [
        Finding(
            code="parse_warning",
            severity=Severity.WARNING,
            title="Could not parse dotenv line",
            message=warning,
            path=env_file.path,
        )
        for warning in env_file.parse_warnings
    ]


def _first_required_usage(usages: list[CodeUsage]) -> CodeUsage | None:
    return next((usage for usage in usages if usage.required), usages[0] if usages else None)


def _required_code_keys(usages: list[CodeUsage]) -> set[str]:
    return {usage.key for usage in usages if usage.required}


def _missing_message(key: str, expected_var: ExpectedVar, shell_env: dict[str, str]) -> str:
    required_usage = _first_required_usage(expected_var.code_usages)
    shell_note = ""
    if key in shell_env:
        shell_note = " It is present in your shell environment, so local commands may work while CI or Docker still fails."
    if required_usage:
        return f"{key} is required by {required_usage.source} in {required_usage.path.name}:{required_usage.line} but was not found in .env.{shell_note}"
    if expected_var.documented_in:
        return f"{key} is documented in {expected_var.documented_in.name} but was not found in .env.{shell_note}"
    return f"{key} is expected but was not found in .env.{shell_note}"


def _missing_suggestion(key: str, shell_env: dict[str, str]) -> str:
    if key in shell_env:
        return f"Add {key}=... to .env or document how CI/Docker should provide it."
    return f"Add {key}=... to .env."


def _checked_details(key: str, actual: EnvFile, example: EnvFile, shell_env: dict[str, str]) -> list[str]:
    return [
        f"shell environment: {'found' if key in shell_env else 'not found'}",
        f".env: {_env_file_status(key, actual)}",
        f".env.example: {_env_file_status(key, example)}",
    ]


def _env_file_status(key: str, env_file: EnvFile) -> str:
    if not env_file.path.exists():
        return "file not found"
    if key not in env_file.values:
        return "not found"
    value = env_file.values[key].value
    if value == "":
        return "found empty"
    if _is_placeholder(value):
        return "found placeholder"
    return "found"


def _usage_details(usages: list[CodeUsage]) -> list[str]:
    return [
        f"{usage.path}:{usage.line}: {usage.source} ({'required' if usage.required else 'optional'})"
        for usage in usages
    ]


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in PLACEHOLDER_VALUES:
        return True
    return "your-" in normalized or normalized.startswith("<") and normalized.endswith(">")


def _mask_value(key: str, value: str) -> str:
    if _secret_like(key) or len(value) > 12:
        return value[:2] + "***" + value[-2:] if len(value) > 4 else "***"
    return repr(value)


def _secret_like(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in ("secret", "token", "password", "passwd", "api_key", "apikey", "key"))


def _similar(left: str, right: str) -> bool:
    if left == right:
        return False
    if left.replace("_", "") == right.replace("_", ""):
        return True
    if _expand_tokens(left) == _expand_tokens(right):
        return True
    if _token_acronym_match(left, right) or _token_acronym_match(right, left):
        return True
    if left.endswith(right) or right.endswith(left):
        return True
    return _levenshtein(left, right) <= max(2, min(len(left), len(right)) // 4)


def _expand_tokens(value: str) -> list[str]:
    return [ABBREVIATIONS.get(part.lower(), part.lower()) for part in value.split("_")]


def _token_acronym_match(short: str, long: str) -> bool:
    short_parts = short.split("_")
    long_parts = long.split("_")
    if len(short_parts) != len(long_parts):
        return False
    return all(
        short_part == long_part or long_part.startswith(short_part)
        for short_part, long_part in zip(short_parts, long_parts)
    )


def _levenshtein(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (left_char != right_char)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]
