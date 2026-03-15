# Profile Loader Design

This document defines how profiles are loaded, validated, and version-checked in the current implementation.

## Responsibilities

- Load profiles from an explicit file path
- Validate profiles against the profile schema
- Validate version alignment between the profile file and versioned profile directory layout

## Profile Location

The loader accepts a direct path to a profile YAML file.

**Examples:**

| Path | Meaning |
| --- | --- |
| `profiles/w3c-vc-core-min/1.0.0/profile.yaml` | Repository-managed versioned profile |
| `custom-profiles/demo/profile.yaml` | Custom relative profile path |
| `/path/to/custom/profile.yaml` | Custom absolute profile path |

If the file is loaded from a versioned repository layout such as `profiles/<id>/<version>/profile.yaml`, the loader also validates that the folder version matches `profile.version`.

## Loader Rules

- A profile must satisfy the `profile-schema.json` contract
- Required fields include `id`, `name`, `version`, and `rules`
- Unknown fields are rejected by schema validation
- `version` must match the version folder when the profile is loaded from a versioned `profiles/<id>/<version>/profile.yaml` path

## Schema Resolution

The loader resolves the profile schema in the following order:

1. Configured schema path, if provided
2. Repository schema path discovered under `profile-schema/profile-schema.json`
3. Packaged schema bundled with the Python package

## Validation Flow

1. Read the YAML file from the provided path
2. Parse the file into a YAML object
3. Validate the parsed object against the profile schema
4. Validate the bundle version when the file path is under `profiles/<id>/<version>/`
5. Return the validated profile object

## Failure Scenarios

| Scenario | Outcome |
| --- | --- |
| Profile file does not exist | Raises a profile loader error |
| Profile file cannot be read or parsed | Raises a profile loader error |
| Parsed profile is not a YAML object | Raises a profile loader error |
| Profile schema validation fails | Raises a profile loader error with validation details |
| Bundle version does not match `profile.version` | Raises a profile loader error |

## Example Versioned Layout

```text
profiles/
  w3c-vc-core-min/
    1.0.0/
      profile.yaml
  oid4vp-jwt-basic/
    1.0.0/
      profile.yaml
```
