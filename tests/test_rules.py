from vc_profile_validator.rules import evaluate_rule, resolve_path


def test_resolve_simple_path() -> None:
    doc = {"vc": {"issuer": "did:example:123"}}
    assert resolve_path(doc, "$.vc.issuer") == ["did:example:123"]


def test_resolve_array_index() -> None:
    doc = {"vc": {"type": ["VerifiableCredential", "Test"]}}
    assert resolve_path(doc, "$.vc.type[1]") == ["Test"]


def test_resolve_wildcard() -> None:
    doc = {"vc": {"type": ["VerifiableCredential", "Test"]}}
    assert resolve_path(doc, "$.vc.type[*]") == ["VerifiableCredential", "Test"]


def test_required_rule_pass() -> None:
    rule = {"type": "required", "path": "$.vc.issuer"}
    result = evaluate_rule(rule, {"vc": {"issuer": "did:example:123"}})
    assert result.passed


def test_equals_rule_fail_on_missing() -> None:
    rule = {"type": "equals", "path": "$.vc.issuer", "value": "did:example:123"}
    result = evaluate_rule(rule, {"vc": {}})
    assert not result.passed


def test_in_rule_any_match() -> None:
    rule = {"type": "in", "path": "$.vc.type[*]", "values": ["VerifiableCredential"]}
    result = evaluate_rule(rule, {"vc": {"type": ["Other", "VerifiableCredential"]}})
    assert result.passed


def test_regex_rule_non_string_fail() -> None:
    rule = {"type": "regex", "path": "$.vc.issuer", "pattern": "^did:"}
    result = evaluate_rule(rule, {"vc": {"issuer": 123}})
    assert not result.passed


def test_type_rule_pass() -> None:
    rule = {"type": "type", "path": "$.vc.issuer", "expectedType": "string"}
    result = evaluate_rule(rule, {"vc": {"issuer": "did:example:123"}})
    assert result.passed
