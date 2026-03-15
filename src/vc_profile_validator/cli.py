from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .batch import run_suite
from .engine import ValidationEngine, ValidationEngineError
from .report import render_html_report


def _read_jwt_payload(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8").strip()
    return _decode_jwt_payload(content)


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    decoded = base64.urlsafe_b64decode(payload_b64 + padding)
    return json.loads(decoded.decode("utf-8"))


def _read_json_payload(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_output(output_path: str | None, content: str) -> None:
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content)


def _timestamp_folder() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def validate_command(args: argparse.Namespace) -> int:
    input_mode = "file"
    input_source = None
    input_sha = None

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Input file not found: {input_path}")
            return 2
        try:
            payload = _read_jwt_payload(input_path)
        except Exception as exc:
            print(f"Failed to parse JWT: {exc}")
            return 2
        input_source = str(input_path)
        input_sha = _sha256_file(input_path)
    elif args.input_jwt:
        input_mode = "jwt"
        try:
            payload = _decode_jwt_payload(args.input_jwt)
        except Exception as exc:
            print(f"Failed to parse JWT: {exc}")
            return 2
        input_source = "inline-jwt"
        input_sha = _sha256_text(args.input_jwt)
    elif args.input_json:
        input_mode = "json"
        try:
            payload = _read_json_payload(args.input_json)
        except Exception as exc:
            print(f"Failed to parse JSON: {exc}")
            return 2
        input_source = "inline-json"
        input_sha = _sha256_text(args.input_json)
    elif args.stdin:
        input_mode = "stdin"
        raw = sys.stdin.read()
        try:
            payload = _read_json_payload(raw)
        except Exception as exc:
            print(f"Failed to parse JSON from stdin: {exc}")
            return 2
        input_source = "stdin"
        input_sha = _sha256_text(raw)
    else:
        print("Input must be provided via --input, --input-jwt, --input-json, or --stdin")
        return 2

    engine = ValidationEngine()
    try:
        result = engine.validate(
            profile_path=args.profile,
            payload=payload,
            target=args.target,
            input_source=input_source,
            input_sha256=input_sha,
        )
    except ValidationEngineError as exc:
        print(f"Validation error: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Execution error: {exc}")
        return 2

    report_json = json.dumps(result.report, indent=2)
    report_html = render_html_report(result.report)

    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir is None and input_mode in {"json", "jwt", "stdin"}:
        output_dir = Path("reports")

    if output_dir is not None:
        run_dir = output_dir / _timestamp_folder()
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "report.json").write_text(report_json, encoding="utf-8")
        (run_dir / "report.html").write_text(report_html, encoding="utf-8")

    if args.output:
        output = report_html if args.format == "html" else report_json
        _write_output(args.output, output)
    else:
        if input_mode in {"json", "jwt", "stdin"}:
            print(report_json)
        elif output_dir is None:
            output = report_html if args.format == "html" else report_json
            _write_output(args.output, output)
    return 0 if result.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vc-profile-validator")
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="Validate a single VC/VP")
    input_group = validate.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", help="VC/VP JWT file path")
    input_group.add_argument("--input-jwt", help="VC/VP JWT string")
    input_group.add_argument("--input-json", help="VC/VP JSON string")
    input_group.add_argument("--stdin", action="store_true", help="Read VC/VP JSON from stdin")
    validate.add_argument("--profile", required=True, help="Profile YAML file path")
    validate.add_argument("--output", help="Output file path")
    validate.add_argument("--output-dir", help="Directory for JSON and HTML reports")
    validate.add_argument("--format", choices=["json", "html"], default="json")
    validate.add_argument("--target", choices=["vc", "vp"], help="Override target")
    validate.set_defaults(func=validate_command)

    batch = subparsers.add_parser("batch", help="Run a validation suite")
    batch.add_argument("--suite", required=True, help="Suite YAML file path")
    batch.add_argument("--output-dir", required=True, help="Output directory for reports")
    batch.set_defaults(func=batch_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    return args.func(args)


def batch_command(args: argparse.Namespace) -> int:
    try:
        _, exit_code = run_suite(Path(args.suite), Path(args.output_dir))
        return exit_code
    except Exception as exc:
        print(f"Execution error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
