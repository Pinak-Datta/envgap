from pathlib import Path

from envdoctor.extractors.python_ast import scan_python_env_usage


def test_scan_python_env_usage_classifies_required_and_optional(tmp_path: Path) -> None:
    app = tmp_path / "app.py"
    app.write_text(
        "\n".join(
            [
                "import os",
                'DATABASE_URL = os.environ["DATABASE_URL"]',
                'REDIS_URL = os.getenv("REDIS_URL")',
                'DEBUG = os.getenv("DEBUG", "false")',
                'CACHE_URL = os.environ.get("CACHE_URL", "memory://")',
            ]
        ),
        encoding="utf-8",
    )

    usages = scan_python_env_usage(tmp_path)
    by_key = {usage.key: usage for usage in usages}

    assert by_key["DATABASE_URL"].required is True
    assert by_key["REDIS_URL"].required is True
    assert by_key["DEBUG"].required is False
    assert by_key["CACHE_URL"].required is False
    assert by_key["DATABASE_URL"].line == 2

