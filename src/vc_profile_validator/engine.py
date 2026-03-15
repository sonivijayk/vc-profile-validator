from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .profile_loader import ProfileLoader
from .report import ValidatorInfo, build_report
from .rules import RuleResult, evaluate_rule


@dataclass(frozen=True)
class ValidationResult:
    report: dict[str, Any]
    passed: bool


class ValidationEngineError(RuntimeError):
    """Raised when validation cannot be executed."""


class ValidationEngine:
    def __init__(self, validator_name: str = "vc-profile-validator", validator_version: str = "0.1.0") -> None:
        self._validator = ValidatorInfo(name=validator_name, version=validator_version)
        self._loader = ProfileLoader()

    def validate(
        self,
        profile_path: str,
        payload: dict[str, Any],
        target: str | None = None,
        input_source: str | None = None,
        input_sha256: str | None = None,
    ) -> ValidationResult:
        profile = self._loader.load(profile_path)
        resolved_target = self._resolve_target(target, profile)
        doc = self._normalize(payload, resolved_target)
        findings = self._evaluate(profile, doc)
        rules_total = len(profile.get("rules", []))
        report = build_report(
            profile,
            resolved_target,
            findings,
            self._validator,
            input_source=input_source,
            input_sha256=input_sha256,
            rules_total=rules_total,
        )
        return ValidationResult(report=report, passed=report["summary"]["result"] == "pass")

    @staticmethod
    def _resolve_target(target: str | None, profile: dict[str, Any]) -> str:
        if target in {"vc", "vp"}:
            return target
        targets = profile.get("targets") or []
        if len(targets) == 1:
            return targets[0]
        raise ValidationEngineError("Target must be specified (vc or vp)")

    @staticmethod
    def _normalize(payload: dict[str, Any], target: str) -> dict[str, Any]:
        if target == "vc":
            return {"vc": payload}
        if target == "vp":
            return {"vp": payload}
        raise ValidationEngineError(f"Unsupported target: {target}")

    def _evaluate(self, profile: dict[str, Any], doc: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for rule in profile.get("rules", []):
            result = evaluate_rule(rule, doc)
            if result.passed:
                continue
            findings.append(self._build_finding(rule, result))
        return findings

    @staticmethod
    def _build_finding(rule: dict[str, Any], result: RuleResult) -> dict[str, Any]:
        finding: dict[str, Any] = {
            "ruleId": rule.get("id"),
            "severity": rule.get("severity"),
            "target": rule.get("target"),
        }
        if "path" in rule:
            finding["path"] = rule["path"]
        if "message" in rule:
            finding["message"] = rule["message"]
        elif "description" in rule:
            finding["message"] = rule["description"]
        if "remediation" in rule:
            finding["remediation"] = rule["remediation"]
        if result.resolved:
            finding["evidence"] = result.resolved
        return finding
