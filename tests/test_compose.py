from pathlib import Path

from envgap.checker import run_check
from envgap.extractors.compose import scan_compose_env_usage


def test_compose_environment_mapping_reports_missing_example_keys(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\nREDIS_URL=redis://localhost:6379/0\n", encoding="utf-8")
    (tmp_path / "compose.yml").write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    environment:",
                "      DATABASE_URL: ${DATABASE_URL}",
                "      REDIS_URL: redis://redis:6379/0",
                "      DEBUG: 'true'",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(tmp_path, environ={})

    assert {usage.key for usage in result.compose_usages} == {"DATABASE_URL", "DEBUG", "REDIS_URL"}
    assert any(
        finding.code == "compose_missing_from_example"
        and finding.key == "REDIS_URL"
        and finding.path == tmp_path / "compose.yml"
        and finding.line == 5
        for finding in result.findings
    )
    assert any(
        finding.code == "compose_missing_from_example"
        and finding.key == "DEBUG"
        and finding.path == tmp_path / "compose.yml"
        and finding.line == 6
        for finding in result.findings
    )
    assert not any(finding.code == "compose_missing_from_example" and finding.key == "DATABASE_URL" for finding in result.findings)


def test_compose_environment_list_and_env_file_are_scanned(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost/app\n", encoding="utf-8")
    (tmp_path / ".env.docker").write_text(
        "\n".join(
            [
                "WORKER_QUEUE=default",
                "export CACHE_URL=redis://redis:6379/0",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "docker-compose.yaml").write_text(
        "\n".join(
            [
                "services:",
                "  worker:",
                "    env_file:",
                "      - .env.docker",
                "    environment:",
                "      - DATABASE_URL=${DATABASE_URL}",
                "      - FEATURE_FLAG",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(tmp_path, environ={})
    missing_from_example = {
        finding.key for finding in result.findings if finding.code == "compose_missing_from_example"
    }

    assert {usage.key for usage in result.compose_usages} == {
        "CACHE_URL",
        "DATABASE_URL",
        "FEATURE_FLAG",
        "WORKER_QUEUE",
    }
    assert {"CACHE_URL", "FEATURE_FLAG", "WORKER_QUEUE"} <= missing_from_example
    assert "DATABASE_URL" not in missing_from_example


def test_compose_ignores_env_files_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.env"
    outside.write_text("SECRET_TOKEN=secret\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "compose.yml").write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    env_file:",
                "      - ../outside.env",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(tmp_path, environ={})

    assert result.compose_usages == []
    assert not any(finding.key == "SECRET_TOKEN" for finding in result.findings)


def test_compose_inline_environment_and_env_file_entries(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "web.env").write_text("WEB_CONCURRENCY=2\n", encoding="utf-8")
    (tmp_path / "compose.yaml").write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    env_file: [web.env]",
                "    environment: [DATABASE_URL=${DATABASE_URL}, DEBUG=true]",
                "  api:",
                "    environment: {API_KEY: ${API_KEY}}",
            ]
        ),
        encoding="utf-8",
    )

    usages = scan_compose_env_usage(tmp_path)

    assert {usage.key for usage in usages} == {"API_KEY", "DATABASE_URL", "DEBUG", "WEB_CONCURRENCY"}
