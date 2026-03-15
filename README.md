# VC Profile Validator

Profile-driven validator for JWT and JSON VCs/VPs with explainable JSON and HTML reports, CLI support, and CI-friendly command-line usage, aligned with OWF fixtures.

## Author
Vijay Kumar Soni (vijaysoni@sonivijay.com)

## Ownership
This project is independently developed and maintained in a personal capacity. It is not affiliated with or endorsed by any employer, standards body, or proprietary platform.

## Design Documentation
The design home page is available at [`docs/design/design-home-page.md`](docs/design/design-home-page.md).

## Installation
```
pip install -e .
```

## Docker
```bash
docker build -t vc-profile-validator .
docker run --rm \
  -v $(pwd):/work \
  vc-profile-validator \
  validate --input /work/examples/fixtures/vc.jwt --profile /work/profiles/w3c-vc-core-min/1.0.0/profile.yaml
```

## Usage
Validate from a JWT file:
```
vc-profile-validator validate \
  --input examples/fixtures/vc.jwt \
  --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml \
  --output-dir reports
```

Validate from an inline JWT string:
```
vc-profile-validator validate \
  --input-jwt "<jwt>" \
  --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml
```

Validate from an inline JSON string:
```
vc-profile-validator validate \
  --input-json '{"issuer":"did:example:123","type":["VerifiableCredential"],"@context":["https://www.w3.org/2018/credentials/v1"],"credentialSubject":{"id":"did:example:abc"}}' \
  --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml
```

Validate from JSON stdin (writes reports to `reports/YYYYMMDDHHMMSS/` and prints JSON to stdout):
```
echo '{"issuer":"did:example:123","type":["VerifiableCredential"],"@context":["https://www.w3.org/2018/credentials/v1"],"credentialSubject":{"id":"did:example:abc"}}' | \
  vc-profile-validator validate --stdin --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml
```

Batch suite run:
```
vc-profile-validator batch --suite suites/owf-owl-agent-vc.yaml --output-dir reports
```

## Reports
- Single validate with `--output-dir` writes `report.json` and `report.html` to `reports/YYYYMMDDHHMMSS/`.
- Single validate with `--input-jwt`, `--input-json`, or `--stdin` writes reports to `reports/YYYYMMDDHHMMSS/` by default and prints JSON to stdout.
- Batch runs write per-case reports under `reports/YYYYMMDDHHMMSS/cases/` and `summary.json`/`summary.html` at the run root.

## Exit Codes
- `0`: Validation passed.
- `1`: Validation completed and produced failing results.
- `2`: Execution error, invalid input, or invalid configuration.

## CI Usage Examples
GitHub Actions example:
```
- name: Validate VC
  run: |
    vc-profile-validator validate \
      --input examples/fixtures/vc.jwt \
      --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml \
      --output-dir reports
```

Jenkins shell step example:
```
vc-profile-validator validate \
  --input examples/fixtures/vc.jwt \
  --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml \
  --output-dir reports
```

For pipelines that stream credentials, use stdin:
```
generate_vc | vc-profile-validator validate --stdin --profile profiles/w3c-vc-core-min/1.0.0/profile.yaml
```
