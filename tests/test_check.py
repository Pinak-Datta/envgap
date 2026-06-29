from pathlib import Path

from envgap.checker import run_check


def test_run_check_reports_core_findings(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "\n".join(
            [
                "DATABASE_URL=",
                "API_KEY=your-key-here",
                "REDIS_URL=",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "DB_URL=postgres://localhost/app",
                "API_KEY=changeme",
                "EXTRA_FLAG=true",
                "EXTRA_FLAG=false",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "settings.py").write_text(
        "\n".join(
            [
                "import os",
                'DATABASE_URL = os.environ["DATABASE_URL"]',
                'REDIS_URL = os.getenv("REDIS_URL")',
                'DEBUG = os.getenv("DEBUG", "false")',
                'SECRET_KEY = os.environ["SECRET_KEY"]',
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(tmp_path, environ={})
    codes = {finding.code for finding in result.findings}
    titles = {finding.title for finding in result.findings}

    assert result.has_errors is True
    assert "missing_key" in codes
    assert "placeholder_value" in codes
    assert "duplicate_key" in codes
    assert "undocumented_key" in codes
    assert "code_missing_from_example" in codes
    assert "possible_typo" in codes
    assert "DB_URL may be a typo for DATABASE_URL" in titles
    assert not any(finding.key == "DEBUG" and finding.code == "missing_key" for finding in result.findings)


def test_run_check_reports_when_missing_key_exists_in_shell(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")

    result = run_check(tmp_path, environ={"DATABASE_URL": "postgres://shell/app"})
    finding = next(finding for finding in result.findings if finding.code == "missing_key")

    assert "present in your shell environment" in finding.message
    assert "shell environment: found" in finding.details
    assert "CI/Docker" in finding.suggestion


def test_run_check_can_ignore_shell_environment(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")

    result = run_check(tmp_path, environ={"DATABASE_URL": "postgres://shell/app"}, include_shell=False)
    finding = next(finding for finding in result.findings if finding.code == "missing_key")

    assert result.shell_env == {}
    assert "shell environment: ignored" in finding.details
    assert "present in your shell environment" not in finding.message


def test_optional_code_usage_does_not_fail_when_absent(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDEBUG = os.getenv("DEBUG", "false")\n', encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert result.has_errors is False
    assert not any(finding.key == "DEBUG" for finding in result.findings)


def test_pydantic_settings_required_fields_are_expected(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "settings.py").write_text(
        "\n".join(
            [
                "from pydantic_settings import BaseSettings",
                "",
                "class Settings(BaseSettings):",
                "    database_url: str",
                "    debug: bool = False",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(tmp_path, environ={})

    assert any(finding.code == "missing_key" and finding.key == "DATABASE_URL" for finding in result.findings)
    assert not any(
        finding.code == "code_missing_from_example" and finding.key == "DATABASE_URL"
        for finding in result.findings
    )
    assert not any(finding.key == "DEBUG" and finding.code == "missing_key" for finding in result.findings)


def test_missing_env_file_is_reported(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert any(finding.code == "missing_env_file" for finding in result.findings)
    assert any(finding.code == "missing_key" and finding.key == "DATABASE_URL" for finding in result.findings)


def test_missing_example_file_is_reported(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\n", encoding="utf-8")
    (tmp_path / "app.py").write_text('import os\nDATABASE_URL = os.environ["DATABASE_URL"]\n', encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert any(finding.code == "missing_example_file" for finding in result.findings)
    assert any(finding.code == "code_missing_from_example" and finding.key == "DATABASE_URL" for finding in result.findings)


def test_duplicate_keys_in_example_are_reported(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\nDATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\n", encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert any(
        finding.code == "duplicate_key"
        and finding.key == "DATABASE_URL"
        and finding.path == tmp_path / ".env.example"
        for finding in result.findings
    )

def test_cfg_abbreviation_is_detected_as_config(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("APP_CONFIG=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("APP_CFG=value\n", encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert any(
        finding.code == "possible_typo"
        and finding.title == "APP_CFG may be a typo for APP_CONFIG"
        for finding in result.findings
    )


def test_pwd_abbreviation_is_detected_as_password(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("USER_PASSWORD=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("USER_PWD=secret\n", encoding="utf-8")

    result = run_check(tmp_path, environ={})

    assert any(
        finding.code == "possible_typo"
        and finding.title == "USER_PWD may be a typo for USER_PASSWORD"
        for finding in result.findings
    )
