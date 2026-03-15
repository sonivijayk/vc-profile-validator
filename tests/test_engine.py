from vc_profile_validator.engine import ValidationEngine, ValidationEngineError


def _profile(tmp_path, target="vc"):
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
        id: w3c-vc-core-min
        name: W3C VC Core - Minimal
        version: 1.0.0
        targets: [vc]
        rules:
          - id: vc-issuer-required
            description: VC must have an issuer
            severity: error
            target: vc
            type: required
            path: $.vc.issuer
        """,
        encoding="utf-8",
    )
    return profile_path


def test_engine_pass(tmp_path):
    engine = ValidationEngine()
    profile_path = _profile(tmp_path)
    payload = {"issuer": "did:example:123"}

    result = engine.validate(str(profile_path), payload)

    assert result.passed
    assert result.report["summary"]["errors"] == 0


def test_engine_fail(tmp_path):
    engine = ValidationEngine()
    profile_path = _profile(tmp_path)
    payload = {}

    result = engine.validate(str(profile_path), payload)

    assert not result.passed
    assert result.report["summary"]["errors"] == 1


def test_engine_requires_target(tmp_path):
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
        id: w3c-vc-core-min
        name: W3C VC Core - Minimal
        version: 1.0.0
        rules:
          - id: vc-issuer-required
            description: VC must have an issuer
            severity: error
            target: vc
            type: required
            path: $.vc.issuer
        """,
        encoding="utf-8",
    )

    engine = ValidationEngine()
    with __import__("pytest").raises(ValidationEngineError, match="Target must be specified"):
        engine.validate(str(profile_path), {"issuer": "did:example:123"})
