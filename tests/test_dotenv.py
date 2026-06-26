from pathlib import Path

from envgap.extractors.dotenv import parse_dotenv


def test_parse_dotenv_values_and_duplicates(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "\n".join(
            [
                "# comment",
                "export DATABASE_URL=postgres://localhost/app",
                "API_KEY='abc#123'",
                'QUOTED="hello # world"',
                "COMMENTED=value # this is ignored",
                "EMPTY=",
                "DATABASE_URL=postgres://localhost/other # duplicate",
            ]
        ),
        encoding="utf-8",
    )

    env_file = parse_dotenv(path)

    assert env_file.values["DATABASE_URL"].value == "postgres://localhost/other"
    assert env_file.values["API_KEY"].value == "abc#123"
    assert env_file.values["QUOTED"].value == "hello # world"
    assert env_file.values["COMMENTED"].value == "value"
    assert env_file.values["EMPTY"].value == ""
    assert list(env_file.duplicates) == ["DATABASE_URL"]
