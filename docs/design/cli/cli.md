# CLI Design

This document defines the `vc-profile-validator` CLI commands, flags, and expected behavior.

## Commands

### 1. `validate`

Validates a single VC or VP against a profile.

**Usage**

```bash
vc-profile-validator validate \
  --input examples/fixtures/vc.jwt \
  --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml \
  --output-dir reports
```

**Flags**

| Flag | Required | Description |
| --- | --- | --- |
| `--input` | No | VC or VP JWT file path |
| `--input-jwt` | No | VC or VP JWT string |
| `--input-json` | No | VC or VP JSON string |
| `--stdin` | No | Read VC or VP JSON from stdin |
| `--profile` | Yes | Profile YAML file path |
| `--output` | No | Output file path |
| `--output-dir` | No | Directory for timestamped JSON and HTML reports |
| `--format` | No | Output format: `json` or `html` |
| `--target` | No | Target override: `vc` or `vp` |

Exactly one input flag must be provided from `--input`, `--input-jwt`, `--input-json`, or `--stdin`.

**Behavior**

- Produces JSON output by default.
- Produces HTML output when `--format html` is used with `--output`.
- Produces both JSON and HTML report files when `--output-dir` is provided.
- If input is provided via `--input-jwt`, `--input-json`, or `--stdin` and `--output-dir` is not provided, reports are written to `reports/YYYYMMDDHHMMSS/` by default and JSON is printed to stdout.
- If `--target` is omitted, target resolution falls back to the profile `targets` field when the profile declares exactly one target.
- Errors are written to stdout.
- Exit code is `0` for pass, `1` for validation failure, and `2` for execution error.

### 2. `batch`

Runs a suite of validation cases.

**Usage**

```bash
vc-profile-validator batch \
  --suite suites/owf-smoke.yaml \
  --output-dir reports
```

**Flags**

| Flag | Required | Description |
| --- | --- | --- |
| `--suite` | Yes | Suite YAML file path |
| `--output-dir` | Yes | Output directory for timestamped batch reports |

**Behavior**

- Produces per-case JSON and HTML reports under `OUTPUT_DIR/YYYYMMDDHHMMSS/cases/`.
- Produces `summary.json` and `summary.html` in the run output folder.
- Errors are written to stdout.
- Exit codes:
  - `0` when all cases match expectations
  - `1` when any case does not match expectation
  - `2` for execution error

## Examples

| Scenario | Command |
| --- | --- |
| Validate from a JWT file | `vc-profile-validator validate --input examples/fixtures/vc.jwt --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml` |
| Validate from an inline JWT string | `vc-profile-validator validate --input-jwt "<jwt>" --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml` |
| Validate from an inline JSON string | `vc-profile-validator validate --input-json '{"issuer":"did:example:123","type":["VerifiableCredential"]}' --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml` |
| Validate JSON from stdin | `echo '{"issuer":"did:example:123","type":["VerifiableCredential"]}' \| vc-profile-validator validate --stdin --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml` |
| Run a batch suite | `vc-profile-validator batch --suite suites/owf-smoke.yaml --output-dir out` |
