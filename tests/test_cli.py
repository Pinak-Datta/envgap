from pathlib import Path

import pytest

from envgap import __version__
from envgap.cli import main


def test_cli_returns_zero_for_clean_project(tmp_path: Path, capsys) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\n", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "No environment config issues found" in output


def test_cli_json_returns_error_for_missing_key(tmp_path: Path, capsys) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert '"code": "missing_key"' in output
    assert '"errors": 1' in output


def test_cli_strict_fails_on_warnings(tmp_path: Path, capsys) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\nEXTRA_FLAG=true\n", encoding="utf-8")

    normal_exit = main(["check", str(tmp_path)])
    normal_output = capsys.readouterr().out
    strict_exit = main(["check", str(tmp_path), "--strict"])
    strict_output = capsys.readouterr().out

    assert normal_exit == 0
    assert strict_exit == 1
    assert "Warnings do not fail unless --strict or --ci is used" in normal_output
    assert "errors or warnings are present" in strict_output


def test_terminal_report_groups_diagnosis_by_key(tmp_path: Path, capsys) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DB_URL=postgres://localhost/app\n", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "shell environment:" in output
    assert "Diagnosis:" in output
    assert "DATABASE_URL" in output
    assert "Possible typo:" in output
    assert "Checked:" in output
    assert "Suggested fix:" in output


def test_cli_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    output = capsys.readouterr().out

    assert exc.value.code == 0
    assert f"envgap {__version__}" in output


def test_cli_help_mentions_check_and_no_shell(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["check", "--help"])

    output = capsys.readouterr().out

    assert exc.value.code == 0
    assert "Compare shell env, .env, .env.example, and Python code" in output
    assert "--no-shell" in output
    assert "--strict" in output


def test_cli_no_shell_ignores_shell_environment(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "postgres://shell/app")

    exit_code = main(["check", str(tmp_path), "--no-shell"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "shell environment: ignored (--no-shell)" in output
    assert "present in your shell environment" not in output
