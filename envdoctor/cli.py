from __future__ import annotations

import argparse
from pathlib import Path

from envdoctor import __version__
from envdoctor.checker import run_check
from envdoctor.reporters.json import render_json
from envdoctor.reporters.terminal import render_terminal


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        result = run_check(Path(args.path), env_file=args.env_file, example_file=args.example_file)
        strict = args.strict or args.ci
        output = render_json(result) if args.format == "json" else render_terminal(result, strict=strict)
        print(output)
        if result.has_errors:
            return 1
        if strict and result.has_warnings:
            return 1
        return 0

    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdoctor",
        description="Explain why your Python environment config is broken.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    check = subparsers.add_parser("check", help="diagnose .env, .env.example, and Python env usage")
    check.add_argument("path", nargs="?", default=".", help="project directory to inspect")
    check.add_argument("--env-file", default=".env", help="dotenv file to compare, relative to path")
    check.add_argument("--example-file", default=".env.example", help="example dotenv file, relative to path")
    check.add_argument("--format", choices=["terminal", "json"], default="terminal", help="output format")
    check.add_argument("--json", action="store_const", const="json", dest="format", help="shortcut for --format json")
    check.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    check.add_argument("--ci", action="store_true", help="CI-friendly alias for --strict")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
