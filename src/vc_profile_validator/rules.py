from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def resolve_path(doc: Any, path: str) -> list[Any]:
    """
    Resolve a minimal JSONPath-like selector.

    Supported:
    - $.a.b
    - $.a[0].b
    - $.a[*].b
    """
    if not path.startswith("$."):
        return []

    tokens = path[2:].split(".")
    current = [doc]

    for token in tokens:
        next_values: list[Any] = []
        if token.endswith("[*]"):
            key = token[:-3]
            for item in current:
                if isinstance(item, dict) and key in item and isinstance(item[key], list):
                    next_values.extend(item[key])
        elif "[" in token and token.endswith("]"):
            key, index_str = token[:-1].split("[")
            try:
                index = int(index_str)
            except ValueError:
                return []
            for item in current:
                if isinstance(item, dict) and key in item and isinstance(item[key], list):
                    arr = item[key]
                    if 0 <= index < len(arr):
                        next_values.append(arr[index])
        else:
            key = token
            for item in current:
                if isinstance(item, dict) and key in item:
                    next_values.append(item[key])
        current = next_values

        if not current:
            break

    return current


@dataclass(frozen=True)
class RuleResult:
    passed: bool
    resolved: list[Any]


def evaluate_rule(rule: dict[str, Any], doc: dict[str, Any]) -> RuleResult:
    rule_type = rule.get("type")
    path = rule.get("path", "")
    resolved = resolve_path(doc, path)

    if rule_type == "required":
        passed = any(value is not None for value in resolved)
        return RuleResult(passed=passed, resolved=resolved)

    if not resolved:
        return RuleResult(passed=False, resolved=resolved)

    if rule_type == "equals":
        expected = rule.get("value")
        passed = any(value == expected for value in resolved)
        return RuleResult(passed=passed, resolved=resolved)

    if rule_type == "in":
        values = rule.get("values", [])
        passed = any(value in values for value in resolved)
        return RuleResult(passed=passed, resolved=resolved)

    if rule_type == "regex":
        import re

        pattern = rule.get("pattern", "")
        try:
            regex = re.compile(pattern)
        except re.error:
            return RuleResult(passed=False, resolved=resolved)
        passed = any(isinstance(value, str) and regex.search(value) for value in resolved)
        return RuleResult(passed=passed, resolved=resolved)

    if rule_type == "type":
        expected = rule.get("expectedType")
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        expected_type = type_map.get(expected)
        passed = expected_type is not None and any(isinstance(value, expected_type) for value in resolved)
        return RuleResult(passed=passed, resolved=resolved)

    return RuleResult(passed=False, resolved=resolved)
