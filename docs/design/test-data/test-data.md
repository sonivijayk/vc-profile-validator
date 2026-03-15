# Test Data Strategy

This document defines how local fixture data is organized and how OWF-derived fixtures are used in validation suites.

## Goals

- Use OWF-derived fixtures for interoperability-oriented validation
- Keep local fixture sets small and focused
- Track source provenance for extracted OWF fixtures

## Current Fixture Sources

The current implementation includes:

| Source Type | Location | Purpose |
| --- | --- | --- |
| Local example fixtures | `examples/fixtures/` | Simple JWT inputs for smoke testing |
| OWF-derived fixtures | `fixtures/owf/` | JSON fixtures extracted from OWF test harness material |
| Fixture provenance mapping | `fixtures/owf/mapping.json` | Source repository and source-path tracking for OWF-derived fixtures |

## OWF Source Repositories

The current mapped OWF-derived fixtures reference:

| Source Repository | Status |
| --- | --- |
| `owl-agent-test-harness` | In use |
| `owl-mobile-wallet-test-harness` | Not currently used |

## Fixture Mapping

OWF-derived fixtures are tracked in `fixtures/owf/mapping.json`.

Each mapping entry records:

| Field | Description |
| --- | --- |
| `sourceRepo` | Source repository name |
| `sourceCommit` | Source revision reference recorded for the extracted fixture; this may be a branch name or commit SHA |
| `sourcePath` | Original path in the source repository |
| `extracted` | Description of the extracted data subset |
| `localPath` | Local fixture path stored in this repository |
| `type` | Fixture target type: `vc` or `vp` |

## Local Fixture Layout

```text
examples/
  fixtures/
    *.jwt

fixtures/
  owf/
    <repo-name>/
      *.json
```

## Suite Integration

- OWF suites live under `suites/owf-*.yaml`
- Suites reference local fixture copies stored in this repository
- Current OWF suites use JSON fixture inputs
- Smoke suites use local JWT example inputs

## Batch Output Behavior

- Batch outputs record the local input path for each case
- Batch outputs include mapped OWF provenance when a case input matches an entry in `fixtures/owf/mapping.json`
- Per-case and summary reports are generated from the suite input set used at runtime

## Future Enhancement Scope

- `sourceCommit` currently records a source revision reference and may not be a pinned commit SHA
- OWF-derived fixtures are currently sourced from `owl-agent-test-harness` only; additional sources such as `owl-mobile-wallet-test-harness` are not yet represented
- Supporting additional fixture sources would require new extracted fixture files, new `mapping.json` entries, and new or expanded suite definitions
