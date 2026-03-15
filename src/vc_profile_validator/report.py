from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ValidatorInfo:
    name: str
    version: str


def build_report(
    profile: dict[str, Any],
    target: str,
    findings: list[dict[str, Any]],
    validator: ValidatorInfo,
    input_source: str | None = None,
    input_sha256: str | None = None,
    rules_total: int | None = None,
) -> dict[str, Any]:
    summary = {
        "errors": sum(1 for f in findings if f["severity"] == "error"),
        "warnings": sum(1 for f in findings if f["severity"] == "warning"),
        "infos": sum(1 for f in findings if f["severity"] == "info"),
    }
    summary["result"] = "fail" if summary["errors"] > 0 else "pass"
    summary["findingsTotal"] = len(findings)
    if rules_total is not None:
        summary["rulesTotal"] = rules_total

    report: dict[str, Any] = {
        "profile": {
            "id": profile["id"],
            "name": profile["name"],
            "version": profile["version"],
        },
        "summary": summary,
        "findings": findings,
        "metadata": {
            "target": target,
            "timestamp": _utc_now(),
            "validator": {
                "name": validator.name,
                "version": validator.version,
            },
        },
    }

    if input_source or input_sha256:
        input_meta: dict[str, Any] = {}
        if input_source:
            input_meta["source"] = input_source
        if input_sha256:
            input_meta["sha256"] = input_sha256
        report["metadata"]["input"] = input_meta

    return report


def render_html_report(report: dict[str, Any]) -> str:
    profile = report["profile"]
    summary = report["summary"]
    metadata = report["metadata"]
    findings = report["findings"]

    result_label = "PASS" if summary["result"] == "pass" else "FAIL"
    result_class = "pass" if summary["result"] == "pass" else "fail"

    input_meta = metadata.get("input", {})
    input_source = input_meta.get("source", "")
    input_sha256 = input_meta.get("sha256", "")

    rows = []
    for finding in findings:
        severity = finding.get("severity", "")
        evidence = finding.get("evidence")
        evidence_text = json.dumps(evidence, ensure_ascii=True) if evidence is not None else ""
        rows.append(
            "<tr>"
            f"<td><span class=\"tag {severity}\">{severity}</span></td>"
            f"<td>{finding.get('ruleId', '')}</td>"
            f"<td>{finding.get('path', '')}</td>"
            f"<td>{finding.get('message', '')}</td>"
            f"<td>{finding.get('remediation', '')}</td>"
            f"<td><code>{evidence_text}</code></td>"
            "</tr>"
        )

    findings_html = "".join(rows) if rows else "<tr><td colspan=\"5\">No findings.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>VC Profile Validator Report</title>
  <style>
    body {{ font-family: "IBM Plex Sans", "Source Sans 3", "Noto Sans", "Helvetica Neue", Arial, sans-serif; margin: 0; color: #1f2328; background: #f7f7f5; }}
    .page {{ max-width: 1100px; margin: 28px auto; padding: 0 24px 32px; }}
    h1 {{ margin: 0 0 6px; font-size: 26px; letter-spacing: 0.2px; }}
    h2 {{ margin: 22px 0 8px; font-size: 18px; }}
    .meta {{ color: #5a6169; margin-bottom: 10px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 8px 0 16px; }}
    .summary-title {{ text-align: right; font-weight: 600; margin: 0 0 6px; color: #4a5158; }}
    .card {{ border: 1px solid #e2e6ea; padding: 12px; border-radius: 8px; background: #ffffff; }}
    .fail {{ color: #b42318; font-weight: 600; }}
    .pass {{ color: #1b5e20; font-weight: 600; }}
    .panel {{ background: #ffffff; border: 1px solid #e2e6ea; border-radius: 10px; padding: 14px 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; background: #ffffff; border: 1px solid #e2e6ea; border-radius: 10px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #eef1f4; text-align: left; padding: 10px 12px; vertical-align: top; }}
    th {{ background: #f3f4f6; color: #3a4047; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .tag {{ padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
    .error {{ background: #fdecea; color: #b42318; }}
    .warning {{ background: #fff4cc; color: #7a5b00; }}
    .info {{ background: #eaf2ff; color: #1b4d8c; }}
    .section {{ margin: 18px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    code {{ font-size: 12px; }}
  </style>
</head>
<body>
  <div class="page">
    <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 24px;">
      <div>
        <h1>VC Profile Validator Report</h1>
        <div class="meta">Profile: {profile['name']} ({profile['id']}@{profile['version']})</div>
        <div><strong>Target:</strong> {metadata['target']}</div>
        <div><strong>Timestamp:</strong> {metadata['timestamp']}</div>
        <div><strong>Validator:</strong> {metadata['validator']['name']} {metadata['validator']['version']}</div>
        <div><strong>Input:</strong> {input_source}</div>
        <div><strong>SHA256:</strong> {input_sha256}</div>
      </div>
    <div>
      <div class="summary-title">Test Results Summary</div>
      <div class="summary">
        <div class="card"><div>Errors</div><div>{summary['errors']}</div></div>
        <div class="card"><div>Warnings</div><div>{summary['warnings']}</div></div>
        <div class="card"><div>Infos</div><div>{summary['infos']}</div></div>
        <div class="card"><div>Result</div><div class="{result_class}">{result_label}</div></div>
      </div>
    </div>
  </div>

  <div class="section panel">
    <h2>Profile Details</h2>
    <div class="grid">
      <div><strong>Profile ID:</strong> {profile['id']}</div>
      <div><strong>Profile Name:</strong> {profile['name']}</div>
      <div><strong>Profile Version:</strong> {profile['version']}</div>
      <div><strong>Rules Evaluated:</strong> {summary.get('rulesTotal', '')}</div>
      <div><strong>Findings:</strong> {summary.get('findingsTotal', '')}</div>
    </div>
  </div>

  <div class="section panel">
    <h2>Input Metadata</h2>
    <div class="grid">
      <div><strong>Source:</strong> {input_source}</div>
      <div><strong>SHA256:</strong> {input_sha256}</div>
    </div>
  </div>

  <h2>Findings</h2>
  <table>
    <thead>
      <tr>
        <th>Severity</th>
        <th>Rule ID</th>
        <th>Path</th>
        <th>Message</th>
        <th>Remediation</th>
        <th>Evidence</th>
      </tr>
    </thead>
    <tbody>
      {findings_html}
    </tbody>
  </table>
  </div>
</body>
</html>
"""
