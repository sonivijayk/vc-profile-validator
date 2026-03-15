from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import base64
import hashlib
import json

import yaml

from .engine import ValidationEngine
from .report import render_html_report


def _find_fixture_mapping_path() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "fixtures" / "owf" / "mapping.json"
        if candidate.exists():
            return candidate
        if (parent / ".git").exists():
            break
    return None


def _load_fixture_mapping() -> dict[Path, dict[str, Any]]:
    mapping_path = _find_fixture_mapping_path()
    if mapping_path is None:
        return {}

    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {}

    mapping_root = mapping_path.parents[2]
    mapped: dict[Path, dict[str, Any]] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        local_path = entry.get("localPath")
        if not isinstance(local_path, str):
            continue
        mapped[(mapping_root / local_path).resolve()] = entry
    return mapped


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    name: str
    description: str
    tags: list[str]
    expect: str
    actual: str
    passed: bool
    report: dict[str, Any]
    input_path: str


def _timestamp_folder() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _format_run_timestamp(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return parsed.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return value


def _read_jwt_payload(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8").strip()
    parts = content.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    decoded = base64.urlsafe_b64decode(payload_b64 + padding)
    return json.loads(decoded.decode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_payload(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object")
    return data


def load_suite(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValueError(f"Suite file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Suite must be a YAML object")

    required = ["id", "name", "version", "profile", "cases"]
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"Suite missing fields: {', '.join(missing)}")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Suite cases must be a non-empty list")

    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("Suite case must be an object")
        for field in ["id", "name", "input", "expect"]:
            if field not in case:
                raise ValueError(f"Suite case missing field: {field}")
    return data


def run_suite(suite_path: Path, output_dir: Path) -> tuple[dict[str, Any], int]:
    suite = load_suite(suite_path)
    profile_path = suite["profile"]
    fixture_mapping = _load_fixture_mapping()

    output_dir.mkdir(parents=True, exist_ok=True)
    run_timestamp = _timestamp_folder()
    run_dir = output_dir / run_timestamp
    cases_dir = run_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    engine = ValidationEngine()
    results: list[CaseResult] = []

    for case in suite["cases"]:
        case_id = case["id"]
        name = case["name"]
        expect = case["expect"]
        description = case.get("description", "")
        tags = case.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]
        input_path = Path(case["input"])
        if not input_path.exists():
            raise ValueError(f"Case input not found: {input_path}")

        input_format = case.get("format")
        if input_format is None:
            input_format = "json" if input_path.suffix.lower() == ".json" else "jwt"
        if input_format not in {"jwt", "json"}:
            raise ValueError(f"Unsupported input format: {input_format}")

        payload = _read_json_payload(input_path) if input_format == "json" else _read_jwt_payload(input_path)
        report = engine.validate(
            profile_path=profile_path,
            payload=payload,
            target=case.get("target"),
            input_source=str(input_path),
            input_sha256=_sha256_file(input_path),
        ).report

        actual = report["summary"]["result"]
        passed = actual == expect
        results.append(
            CaseResult(
                case_id=case_id,
                name=name,
                description=description,
                tags=tags,
                expect=expect,
                actual=actual,
                passed=passed,
                report=report,
                input_path=str(input_path),
            )
        )

        case_json = json.dumps(report, indent=2)
        (cases_dir / f"{case_id}.json").write_text(case_json, encoding="utf-8")
        (cases_dir / f"{case_id}.html").write_text(render_html_report(report), encoding="utf-8")

    summary = _build_summary(suite, results, run_timestamp, fixture_mapping)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (run_dir / "summary.html").write_text(_render_summary_html(summary, results), encoding="utf-8")

    exit_code = 0 if summary["summary"]["failed"] == 0 else 1
    return summary, exit_code


def _build_summary(
    suite: dict[str, Any],
    results: list[CaseResult],
    run_timestamp: str,
    fixture_mapping: dict[Path, dict[str, Any]],
) -> dict[str, Any]:
    readable = _format_run_timestamp(run_timestamp)
    totals = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
    }

    cases = []
    for r in results:
        case_summary = {
            "id": r.case_id,
            "name": r.name,
            "description": r.description,
            "tags": r.tags,
            "expect": r.expect,
            "actual": r.actual,
            "passed": r.passed,
            "input": r.input_path,
            "report": {
                "json": f"cases/{r.case_id}.json",
                "html": f"cases/{r.case_id}.html",
            },
        }
        provenance = fixture_mapping.get(Path(r.input_path).resolve())
        if provenance is not None:
            case_summary["source"] = {
                "repo": provenance.get("sourceRepo"),
                "path": provenance.get("sourcePath"),
                "commit": provenance.get("sourceCommit"),
                "extracted": provenance.get("extracted"),
            }
        cases.append(case_summary)

    return {
        "suite": {
            "id": suite["id"],
            "name": suite["name"],
            "version": suite["version"],
            "profile": suite["profile"],
        },
        "summary": totals,
        "cases": cases,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "runId": run_timestamp,
        "runTime": readable,
    }


def _render_summary_html(summary: dict[str, Any], results: list[CaseResult]) -> str:
    suite = summary["suite"]
    totals = summary["summary"]
    run_id = summary.get("runId", "")
    run_time = summary.get("runTime", summary.get("timestamp", ""))

    tree_items = []
    case_sections = []
    for r in results:
        status_class = "pass" if r.passed else "fail"
        tree_items.append(
            "<li>"
            f"<span class=\"dot {status_class}\"></span>"
            f"<a href=\"#case-{r.case_id}\">{r.case_id}</a>"
            "</li>"
        )

        case_sections.append(
            f"<details id=\"case-{r.case_id}\" open>"
            f"<summary class=\"case-summary {status_class}\">"
            f"<span class=\"badge {status_class}\">{status_class.upper()}</span>"
            f"<span class=\"case-title\">{r.case_id}: {r.name}</span>"
            "</summary>"
            "<div class=\"case-body\">"
            f"<div class=\"case-meta\">"
            f"<div><strong>Expect:</strong> {r.expect}</div>"
            f"<div><strong>Actual:</strong> {r.actual}</div>"
            f"<div><strong>Input:</strong> {r.input_path}</div>"
            f"<div><strong>Description:</strong> {r.description}</div>"
            f"<div><strong>Tags:</strong> {', '.join(r.tags) if r.tags else ''}</div>"
            "</div>"
            f"{_render_findings_table(r.report)}"
            "</div>"
            "</details>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>VC Profile Validator Batch Report</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: "IBM Plex Sans", "Source Sans 3", "Noto Sans", "Helvetica Neue", Arial, sans-serif; margin: 0; color: #1f2328; background: #f7f7f5; }}
    .layout {{ display: flex; min-height: 100vh; }}
    .sidebar {{ width: 280px; background: #fbfbf9; border-right: 1px solid #e2e6ea; padding: 16px; flex-shrink: 0; overflow: auto; overflow-x: hidden; word-break: break-word; }}
    .content {{ flex: 1; padding: 24px; }}
    h1 {{ margin-top: 0; font-size: 24px; }}
    h2 {{ margin: 0 0 10px; font-size: 18px; }}
    ul {{ list-style: none; padding-left: 0; margin: 8px 0 0; }}
    li {{ margin: 8px 0; display: flex; align-items: center; gap: 8px; }}
    a {{ color: #2b2f36; text-decoration: none; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    .dot.pass {{ background: #1b5e20; }}
    .dot.fail {{ background: #b42318; }}
    .summary {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0; width: 100%; }}
    .card {{ border: 1px solid #e2e6ea; padding: 12px; border-radius: 8px; background: #ffffff; }}
    .badge {{ font-size: 12px; padding: 2px 8px; border-radius: 999px; display: inline-block; margin-right: 8px; font-weight: 600; }}
    .badge.pass {{ background: #e6f4ea; color: #1b5e20; }}
    .badge.fail {{ background: #fdecea; color: #b42318; }}
    .case-summary {{ cursor: pointer; padding: 10px 12px; border-radius: 8px; background: #ffffff; border: 1px solid #e2e6ea; display: flex; align-items: center; gap: 8px; }}
    .case-summary.pass {{ border-left: 4px solid #1b5e20; }}
    .case-summary.fail {{ border-left: 4px solid #b42318; }}
    .case-title {{ font-weight: 600; }}
    .case-body {{ background: #ffffff; border: 1px solid #e2e6ea; border-top: none; border-radius: 0 0 8px 8px; padding: 12px 16px 16px; }}
    .case-meta {{ margin: 0 0 12px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; }}
    details {{ margin: 12px 0; }}
    details[open] > summary {{ border-bottom-left-radius: 0; border-bottom-right-radius: 0; }}
    summary {{ list-style: none; }}
    summary::-webkit-details-marker {{ display: none; }}
    code {{ font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; background: #ffffff; border: 1px solid #e2e6ea; border-radius: 8px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #eef1f4; text-align: left; padding: 10px 12px; vertical-align: top; }}
    th {{ background: #f3f4f6; color: #3a4047; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }}
  </style>
</head>
<body>
  <div class="layout">
    <div class="sidebar">
      <h2>Scenarios</h2>
      <div><strong>Suite:</strong> {suite['name']}</div>
      <div><strong>Profile:</strong> {suite['profile']}</div>
      <div><strong>Run:</strong> {run_id}</div>
      <div><strong>Executed:</strong> {run_time}</div>
      <div class="summary">
        <div class="card"><div>Total</div><div>{totals['total']}</div></div>
        <div class="card"><div>Passed</div><div>{totals['passed']}</div></div>
        <div class="card"><div>Failed</div><div>{totals['failed']}</div></div>
      </div>
      <ul>
        {''.join(tree_items)}
      </ul>
    </div>
    <div class="content">
      <h1>Suite Report</h1>
      <div><strong>Suite:</strong> {suite['name']} ({suite['id']}@{suite['version']})</div>
      <div><strong>Profile:</strong> {suite['profile']}</div>
      {''.join(case_sections)}
    </div>
  </div>
</body>
</html>
"""


def _render_findings_table(report: dict[str, Any]) -> str:
    findings = report.get("findings", [])
    if not findings:
        return "<div>No findings.</div>"

    rows = []
    for finding in findings:
        evidence = finding.get("evidence")
        evidence_text = json.dumps(evidence, ensure_ascii=True) if evidence is not None else ""
        rows.append(
            "<tr>"
            f"<td>{finding.get('severity', '')}</td>"
            f"<td>{finding.get('ruleId', '')}</td>"
            f"<td>{finding.get('path', '')}</td>"
            f"<td>{finding.get('message', '')}</td>"
            f"<td><code>{evidence_text}</code></td>"
            "</tr>"
        )

    return (
        "<table>"
        "<thead><tr><th>Severity</th><th>Rule ID</th><th>Path</th><th>Message</th><th>Evidence</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )
