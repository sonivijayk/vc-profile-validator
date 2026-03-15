from pathlib import Path

import pytest

from vc_profile_validator.profile_loader import ProfileLoader, ProfileLoaderError


def _write_profile(path: Path, version: str = "1.0.0") -> None:
    content = f"""id: w3c-vc-core-min
name: W3C VC Core - Minimal
version: {version}
description: Minimal structure checks
rules:
  - id: vc-issuer-required
    description: VC must have an issuer
    severity: error
    target: vc
    type: required
    path: $.vc.issuer
"""
    path.write_text(content, encoding="utf-8")


def test_load_profile_success(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    _write_profile(profile_path)

    loader = ProfileLoader()
    data = loader.load(profile_path)

    assert data["id"] == "w3c-vc-core-min"
    assert data["version"] == "1.0.0"


def test_load_profile_schema_error(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text("name: Missing id\n", encoding="utf-8")

    loader = ProfileLoader()
    with pytest.raises(ProfileLoaderError, match="schema validation failed"):
        loader.load(profile_path)


def test_load_profile_version_mismatch(tmp_path: Path) -> None:
    profile_path = tmp_path / "profiles" / "w3c-vc-core-min" / "2.0.0" / "profile.yaml"
    profile_path.parent.mkdir(parents=True)
    _write_profile(profile_path, version="1.0.0")

    loader = ProfileLoader()
    with pytest.raises(ProfileLoaderError, match="does not match bundle folder"):
        loader.load(profile_path)


def test_load_profile_invalid_yaml(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(": bad yaml", encoding="utf-8")

    loader = ProfileLoader()
    with pytest.raises(ProfileLoaderError, match="Failed to read profile"):
        loader.load(profile_path)
