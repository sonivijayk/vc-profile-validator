from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
import sys


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parents[1]
    src_path = str(repo / "src")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}:{existing}"
    return subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)


def test_cli_validate_creates_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "reports"

    cmd = [
        sys.executable,
        "-m",
        "vc_profile_validator.cli",
        "validate",
        "--input",
        str(repo / "examples" / "fixtures" / "vc.jwt"),
        "--profile",
        str(repo / "profiles" / "w3c-vc-core-min" / "1.0.0" / "profile.yaml"),
        "--output-dir",
        str(output_dir),
    ]
    result = _run(cmd, repo)
    assert result.returncode == 0

    run_dirs = [p for p in output_dir.iterdir() if p.is_dir()]
    assert run_dirs
    run_dir = run_dirs[0]
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.html").exists()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["summary"]["result"] == "pass"


def test_cli_batch_creates_summary(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "reports"

    cmd = [
        sys.executable,
        "-m",
        "vc_profile_validator.cli",
        "batch",
        "--suite",
        str(repo / "suites" / "owf-smoke.yaml"),
        "--output-dir",
        str(output_dir),
    ]
    result = _run(cmd, repo)
    assert result.returncode in (0, 1)

    run_dirs = [p for p in output_dir.iterdir() if p.is_dir()]
    assert run_dirs
    run_dir = run_dirs[0]
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "summary.html").exists()

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["summary"]["total"] >= 2


def test_cli_batch_summary_includes_fixture_provenance(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "reports"

    cmd = [
        sys.executable,
        "-m",
        "vc_profile_validator.cli",
        "batch",
        "--suite",
        str(repo / "suites" / "owf-owl-agent-vc.yaml"),
        "--output-dir",
        str(output_dir),
    ]
    result = _run(cmd, repo)
    assert result.returncode in (0, 1)

    run_dirs = [p for p in output_dir.iterdir() if p.is_dir()]
    assert run_dirs
    summary = json.loads((run_dirs[0] / "summary.json").read_text(encoding="utf-8"))
    first_case = summary["cases"][0]
    assert first_case["source"]["repo"] == "owl-agent-test-harness"
    assert "sourceCommit" not in first_case["source"]
    assert first_case["source"]["commit"] == "main"


def test_cli_validate_inline_json_creates_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    input_json = "{\"issuer\":\"did:example:123\",\"type\":[\"VerifiableCredential\"],\"@context\":[\"https://www.w3.org/2018/credentials/v1\"],\"credentialSubject\":{\"id\":\"did:example:abc\"}}"

    cmd = [
        sys.executable,
        "-m",
        "vc_profile_validator.cli",
        "validate",
        "--input-json",
        input_json,
        "--profile",
        str(repo / "profiles" / "w3c-vc-core-min" / "1.0.0" / "profile.yaml"),
    ]
    result = _run(cmd, tmp_path)
    assert result.returncode in (0, 1)

    reports_dir = tmp_path / "reports"
    assert reports_dir.exists()
    run_dirs = [p for p in reports_dir.iterdir() if p.is_dir()]
    assert run_dirs
    assert (run_dirs[0] / "report.json").exists()
    assert (run_dirs[0] / "report.html").exists()


def test_cli_validate_stdin_creates_reports(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    input_json = "{\"issuer\":\"did:example:123\",\"type\":[\"VerifiableCredential\"],\"@context\":[\"https://www.w3.org/2018/credentials/v1\"],\"credentialSubject\":{\"id\":\"did:example:abc\"}}"

    cmd = [
        sys.executable,
        "-m",
        "vc_profile_validator.cli",
        "validate",
        "--stdin",
        "--profile",
        str(repo / "profiles" / "w3c-vc-core-min" / "1.0.0" / "profile.yaml"),
    ]
    repo = Path(__file__).resolve().parents[1]
    src_path = str(repo / "src")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else f"{src_path}:{existing}"
    result = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        env=env,
        input=input_json,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1)

    reports_dir = tmp_path / "reports"
    assert reports_dir.exists()
    run_dirs = [p for p in reports_dir.iterdir() if p.is_dir()]
    assert run_dirs
    assert (run_dirs[0] / "report.json").exists()
    assert (run_dirs[0] / "report.html").exists()
