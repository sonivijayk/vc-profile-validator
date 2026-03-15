from __future__ import annotations

from dataclasses import dataclass
import importlib.resources as resources
from pathlib import Path
from typing import Any

import json

import yaml
from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ProfileLoaderConfig:
    schema_path: Path | None = None


class ProfileLoaderError(ValueError):
    """Raised when a profile cannot be loaded or validated."""


class ProfileLoader:
    def __init__(self, config: ProfileLoaderConfig | None = None) -> None:
        self._config = config or ProfileLoaderConfig()

    def load(self, profile_path: str | Path) -> dict[str, Any]:
        path = Path(profile_path)
        if not path.exists() or not path.is_file():
            raise ProfileLoaderError(f"Profile file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as exc:  # pragma: no cover - defensive
            raise ProfileLoaderError(f"Failed to read profile: {exc}") from exc

        if not isinstance(data, dict):
            raise ProfileLoaderError("Profile must be a YAML object")

        schema = self._load_schema()
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            details = "; ".join(self._format_error(err) for err in errors)
            raise ProfileLoaderError(f"Profile schema validation failed: {details}")

        self._validate_bundle_version(path, data)
        return data

    def _load_schema(self) -> dict[str, Any]:
        schema_path = self._config.schema_path or self._find_schema_path()
        if schema_path is not None and schema_path.exists():
            try:
                return json.loads(schema_path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive
                raise ProfileLoaderError(f"Failed to read schema: {exc}") from exc
        try:
            schema_text = (
                resources.files("vc_profile_validator.schemas")
                .joinpath("profile-schema.json")
                .read_text(encoding="utf-8")
            )
            return json.loads(schema_text)
        except Exception as exc:  # pragma: no cover - defensive
            raise ProfileLoaderError(f"Failed to read schema: {exc}") from exc

    def _find_schema_path(self) -> Path | None:
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            candidate = parent / "profile-schema" / "profile-schema.json"
            if candidate.exists():
                return candidate
            git_dir = parent / ".git"
            if git_dir.exists():
                root_candidate = parent / "profile-schema" / "profile-schema.json"
                if root_candidate.exists():
                    return root_candidate
        return None

    def _validate_bundle_version(self, path: Path, data: dict[str, Any]) -> None:
        parts = path.resolve().parts
        try:
            idx = parts.index("profiles")
        except ValueError:
            return

        if len(parts) < idx + 4:
            return

        bundle_version = parts[idx + 2]
        profile_version = data.get("version")
        if bundle_version != profile_version:
            raise ProfileLoaderError(
                "Profile version does not match bundle folder: "
                f"{profile_version} != {bundle_version}"
            )

    @staticmethod
    def _format_error(err: Any) -> str:
        path = ".".join(str(p) for p in err.path) if err.path else "<root>"
        return f"{path}: {err.message}"
