from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envdoctor.checker import CheckResult
from envdoctor.model import Finding, Severity


def render_json(result: CheckResult) -> str:
    payload = {
        "root": str(result.root),
        "files": {
            "env": _file_info(result.env_path),
            "example": _file_info(result.example_path),
        },
        "shell": {
            "available": True,
            "expected_keys_found": sorted(key for key in result.expected_keys if key in result.shell_env),
            "expected_keys_missing": sorted(key for key in result.expected_keys if key not in result.shell_env),
        },
        "summary": {
            "findings": len(result.findings),
            "errors": sum(1 for finding in result.findings if finding.severity == Severity.ERROR),
            "warnings": sum(1 for finding in result.findings if finding.severity == Severity.WARNING),
            "expected_keys": len(result.expected_keys),
            "code_usages": len(result.code_usages),
        },
        "findings": [_finding_to_dict(finding, result.root) for finding in result.findings],
        "code_usages": [
            {
                "key": usage.key,
                "path": _relative(usage.path, result.root),
                "line": usage.line,
                "required": usage.required,
                "source": usage.source,
            }
            for usage in result.code_usages
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _finding_to_dict(finding: Finding, root: Path) -> dict[str, Any]:
    return {
        "code": finding.code,
        "severity": finding.severity.value,
        "title": finding.title,
        "message": finding.message,
        "key": finding.key,
        "path": _relative(finding.path, root) if finding.path else None,
        "line": finding.line,
        "suggestion": finding.suggestion,
        "details": finding.details,
    }


def _file_info(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.exists()}


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
