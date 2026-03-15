# Design Home Page

This page is the entry point for the VC Profile Validator design set. It summarizes the project scope, points to the detailed design documents, and records the current implementation status of each area.

## Purpose

VC Profile Validator is a profile-driven validation tool for Verifiable Credentials (VCs) and Verifiable Presentations (VPs). The current implementation supports:
- Validation of JWT-based VC/VP inputs from files or inline strings
- Validation of JSON VC/VP inputs from inline input or stdin
- Profile-based rule evaluation using versioned YAML profiles
- JSON and HTML report generation
- Single validation and batch suite execution

For the full architecture, validation flow, data artifacts, and exit-code behavior, see [technical-overview.md](technical-overview.md).

## Scope

In scope:
- Validation of VC/VP payloads against profile-defined rules
- Deterministic rule evaluation and machine-readable reports
- CLI-based execution for local use and automation
- Suite-based batch validation using local and OWF-derived fixtures

Out of scope:
- Credential issuance
- Wallet or SDK implementation
- Production compliance certification
- Live DID network operations

## Detailed Design

| # | Area | Document |
| --- | --- | --- |
| 1 | Technical Overview | [technical-overview.md](technical-overview.md) |
| 2 | Profile Schema | [profile-schema.json](profile-schema/profile-schema.json) |
| 3 | Rule Model | [rule-model.md](rule-model/rule-model.md) |
| 4 | Validation Engine | [validation-engine.md](validation-engine/validation-engine.md) |
| 5 | CLI | [cli.md](cli/cli.md) |
| 6 | Report Format | [report-format.md](report-format/report-format.md) |
| 7 | Suite Format | [suite-format.md](suite-format/suite-format.md) |
| 8 | Profile Loader | [profile-loader.md](profile-loader/profile-loader.md) |
| 9 | Docker Packaging | [docker.md](docker/docker.md) |
| 10 | Test Data Strategy | [test-data.md](test-data/test-data.md) |
