# Batch Suite Format Design

This document defines the YAML format for batch validation suites.

## Suite Structure

A suite file contains suite metadata and a list of validation cases.

```yaml
id: owf-smoke
name: OWF Smoke Suite
version: 1.0.0
profile: profiles/w3c-vc-core-min/1.0.0/profile.yaml
cases:
  - id: vc-valid-01
    name: Valid VC
    description: VC includes issuer and type fields required by the profile
    tags: [smoke, positive]
    input: examples/fixtures/vc.jwt
    expect: pass
  - id: vc-missing-issuer
    name: Missing issuer
    description: VC omits issuer and should fail required field checks
    tags: [smoke, negative]
    input: examples/fixtures/vc-missing-issuer.jwt
    expect: fail
```

## Suite Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Suite identifier |
| `name` | Yes | Suite name |
| `version` | Yes | Suite version |
| `profile` | Yes | Profile file path used for all cases in the suite |
| `cases` | Yes | List of validation cases |

## Case Fields

| Field | Required | Description |
| --- | --- | --- |
| `id` | Yes | Case identifier |
| `name` | Yes | Human-readable case name |
| `description` | No | Optional case description |
| `tags` | No | Optional list of tags |
| `input` | Yes | Path to a VC or VP JWT or JSON file |
| `format` | No | Input format: `jwt` or `json`; defaults to `json` when the file ends with `.json`, otherwise `jwt` |
| `expect` | Yes | Expected validation result: `pass` or `fail` |
| `target` | No | Optional per-case target override: `vc` or `vp` |

## Execution Behavior

- Each case is validated using the suite profile
- Per-case JSON and HTML reports are written to `--output-dir/YYYYMMDDHHMMSS/cases/<case-id>.(json|html)`
- Batch summary files are written to `--output-dir/YYYYMMDDHHMMSS/summary.(json|html)`
- The batch command returns exit code `0` when all cases match expectations
- The batch command returns exit code `1` when one or more cases do not match expectation
- The batch command returns exit code `2` for execution errors

## Validation Behavior

- `expect` is compared against `report.summary.result`
- If `format` is omitted, the runner infers the input format from the file extension
- If `target` is omitted, target resolution falls back to the profile used by the suite

## Failure Scenarios

| Scenario | Outcome |
| --- | --- |
| Suite file is missing or invalid | Execution error |
| Suite metadata is missing required fields | Execution error |
| `cases` is missing or empty | Execution error |
| A case is not an object | Execution error |
| A case is missing a required field | Execution error |
| A case input file is missing | Execution error |
| A case input format is unsupported | Execution error |
