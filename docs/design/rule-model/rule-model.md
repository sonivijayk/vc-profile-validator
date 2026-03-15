# Rule Model Design

This document defines the rule primitives and evaluation semantics for VC Profile Validator.

## Objectives

- Provide deterministic, explainable validation results.
- Use a small set of rule primitives for structure-level checks.
- Maintain a clear mapping from rule definition to validation finding.

## Rule Base

Common fields for all rules:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `string` | Yes | Stable rule identifier |
| `description` | `string` | Yes | Human-readable rule intent |
| `severity` | `error` \| `warning` \| `info` | Yes | Finding level |
| `target` | `vc` \| `vp` | Yes | Document type the rule applies to |
| `path` | `string` | No | JSONPath-like selector into the target document |
| `message` | `string` | No | Failure message override |
| `remediation` | `string` | No | Suggested fix |

## Path Conventions

- JSONPath-like, starting at `$`.
- Supported path forms:
  - Object navigation: `$.vc.issuer`
  - Array index: `$.vc.credentialSubject[0]`
  - Wildcard selection: `$.vc.credentialSubject[*].id`
- If a path cannot be resolved, it is treated as missing for rule evaluation.

## Rule Types

| Rule Type | Purpose | Required Fields | Evaluation |
| --- | --- | --- | --- |
| `required` | Ensures that a path exists and is not null | `path` | Pass if the path resolves to at least one non-null value. Fail if the path is missing or all resolved values are null |
| `equals` | Ensures that a resolved value matches exactly | `path`, `value` | Pass if any resolved value equals `value`. Fail if no resolved values exist or no value matches. Matching is case-sensitive by default |
| `in` | Ensures that a resolved value is one of a defined set | `path`, `values` | Pass if any resolved value is contained in `values`. Fail if no resolved values exist or no value matches. Matching is case-sensitive by default |
| `regex` | Ensures that a resolved string value matches a regular expression | `path`, `pattern` | Pass if any resolved string value matches the regex. Fail if no resolved values exist, values are non-string, or no value matches |
| `type` | Ensures that a resolved value matches the expected JSON type | `path`, `expectedType` | Pass if any resolved value matches the expected type. Fail if no resolved values exist or no value matches |

For `type`, supported `expectedType` values are `string`, `number`, `integer`, `boolean`, `object`, and `array`.

## Findings Model

Each failed rule produces a finding with the following attributes:

| Field | Description |
| --- | --- |
| `ruleId` | The rule id |
| `severity` | `error`, `warning`, or `info` |
| `target` | `vc` or `vp` |
| `path` | The rule path |
| `message` | Default description or rule override |
| `remediation` | Optional guidance text |
| `evidence` | Resolved values, when available |

## Determinism Rules

- Resolve paths in a stable order.
- Produce findings in the same order as rules appear in the profile.
- Do not short-circuit across rules.
- Allow mixed resolved values when evaluating a rule.

## Example Rule Snippet

```yaml
rules:
  - id: vc-issuer-required
    description: VC must have an issuer
    severity: error
    target: vc
    type: required
    path: $.vc.issuer

  - id: vc-type-contains-vc
    description: VC type must include VerifiableCredential
    severity: error
    target: vc
    type: in
    path: $.vc.type[*]
    values: ["VerifiableCredential"]
```
