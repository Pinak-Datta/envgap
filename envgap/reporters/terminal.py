from __future__ import annotations

from collections import defaultdict
from collections import Counter
from pathlib import Path

from envgap.checker import CheckResult
from envgap.model import Finding, Severity

ICONS = {
    Severity.ERROR: "!",
    Severity.WARNING: "~",
    Severity.INFO: "i",
}

SEVERITY_ORDER = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}

DIAGNOSIS_LABELS = {
    "code_missing_from_example": "Code/documentation drift",
    "duplicate_key": "Duplicate key",
    "empty_value": "Empty value",
    "missing_env_file": "Missing source",
    "missing_example_file": "Missing source",
    "missing_key": "Missing value",
    "parse_warning": "Parse warning",
    "placeholder_value": "Placeholder value",
    "possible_typo": "Possible typo",
    "undocumented_key": "Undocumented key",
}


def render_terminal(result: CheckResult, strict: bool = False) -> str:
    lines: list[str] = []
    counts = Counter(finding.severity for finding in result.findings)

    lines.append("envgap check")
    lines.append("=" * 15)
    lines.append("")
    lines.append(f"Project: {result.root}")
    lines.append("Checked:")
    lines.append(f"  shell environment: {_shell_summary(result)}")
    lines.append(f"  .env: {_dotenv_summary(result.env_path, len(result.env_file.vars))}")
    lines.append(f"  .env.example: {_dotenv_summary(result.example_path, len(result.example_file.vars))}")
    lines.append(f"  Python code: {len(result.code_usages)} env usage(s)")
    lines.append("")

    if not result.findings:
        lines.append("OK  No environment config issues found.")
        lines.append(_exit_code_line(strict))
        return "\n".join(lines)

    lines.append(
        "Summary: "
        f"{counts[Severity.ERROR]} error(s), "
        f"{counts[Severity.WARNING]} warning(s), "
        f"{counts[Severity.INFO]} info"
    )
    lines.append("")
    lines.append("Diagnosis:")

    for group, findings in _group_findings(result.findings).items():
        lines.append(f"  {group}")
        for finding in sorted(findings, key=_finding_sort_key):
            lines.extend(_format_finding(finding, result))
        lines.append("")

    lines.append(_exit_code_line(strict))
    return "\n".join(lines).rstrip()


def _format_finding(finding: Finding, result: CheckResult) -> list[str]:
    icon = ICONS[finding.severity]
    location = _location(finding, result.root)
    label = DIAGNOSIS_LABELS.get(finding.code, finding.code.replace("_", " ").title())
    lines = [f"    {icon} {label}: {finding.title}{location}", f"      {finding.message}"]
    checked = [detail for detail in finding.details if _is_checked_detail(detail)]
    usages = [detail for detail in finding.details if not _is_checked_detail(detail)]
    if checked:
        lines.append("      Checked:")
        for detail in checked:
            lines.append(f"        {detail}")
    elif finding.key:
        lines.extend(_checked_lines(finding.key, result))
    for detail in usages:
        lines.append(f"      Used at: {_relative_detail(detail, result.root)}")
    if finding.suggestion:
        lines.append(f"      Suggested fix: {finding.suggestion}")
    return lines


def _group_findings(findings: list[Finding]) -> dict[str, list[Finding]]:
    groups: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        groups[finding.key or "Project setup"].append(finding)
    return {
        key: groups[key]
        for key in sorted(groups, key=lambda value: (value != "Project setup", value))
    }


def _finding_sort_key(finding: Finding) -> tuple[int, str, int]:
    return (SEVERITY_ORDER[finding.severity], finding.code, finding.line or 0)


def _checked_lines(key: str, result: CheckResult) -> list[str]:
    return [
        "      Checked:",
        f"        shell environment: {_shell_key_status(key, result)}",
        f"        .env: {_env_file_status(key, result.env_path, result.env_file.values)}",
        f"        .env.example: {_env_file_status(key, result.example_path, result.example_file.values)}",
        f"        Python code: {_code_status(key, result)}",
    ]


def _is_checked_detail(detail: str) -> bool:
    return detail.startswith(("shell environment:", ".env:", ".env.example:", "Python code:"))


def _dotenv_summary(path: Path, count: int) -> str:
    if not path.exists():
        return "not found"
    return f"found ({count} key(s))"


def _shell_summary(result: CheckResult) -> str:
    if not result.include_shell:
        return "ignored (--no-shell)"
    if not result.expected_keys:
        return f"available ({len(result.shell_env)} variable(s))"
    found = sum(1 for key in result.expected_keys if key in result.shell_env)
    return f"available ({found}/{len(result.expected_keys)} expected key(s) found)"


def _env_file_status(key: str, path: Path, values: dict) -> str:
    if not path.exists():
        return "file not found"
    return "found" if key in values else "not found"


def _shell_key_status(key: str, result: CheckResult) -> str:
    if not result.include_shell:
        return "ignored"
    return "found" if key in result.shell_env else "not found"


def _code_status(key: str, result: CheckResult) -> str:
    usages = [usage for usage in result.code_usages if usage.key == key]
    if not usages:
        return "not found"
    if any(usage.required for usage in usages):
        return "required"
    return "optional"


def _exit_code_line(strict: bool) -> str:
    if strict:
        return "Exit code: 1 when errors or warnings are present (--strict/--ci), otherwise 0."
    return "Exit code: 1 when errors are present, otherwise 0. Warnings do not fail unless --strict or --ci is used."


def _location(finding: Finding, root: Path) -> str:
    if not finding.path:
        return ""
    path = _relative(finding.path, root)
    if finding.line:
        return f" ({path}:{finding.line})"
    return f" ({path})"


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _relative_detail(detail: str, root: Path) -> str:
    root_text = str(root)
    return detail.replace(root_text + "/", "")
