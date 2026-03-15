# Docker Packaging Design

This document defines how the validator is packaged and run via Docker.

## Image
- Image name: `vc-profile-validator`
- Default entrypoint: `vc-profile-validator`
- Exposes CLI commands (`validate`, `batch`)
- Uses a Python slim base image
- Sets `/work` as the runtime working directory

## Container Usage
```bash
docker build -t vc-profile-validator .

docker run --rm \
  -v $(pwd):/work \
  vc-profile-validator \
  validate --input /work/examples/fixtures/vc.jwt --profile /work/profiles/w3c-vc-core-min/1.0.0/profile.yaml
```

## Volume Conventions
- Mount a working directory to `/work`
- Input, profiles, suites, and outputs are referenced under `/work`

## Output Handling
- JSON output defaults to stdout
- File outputs are written to mounted volume paths

## Build Notes
- Build from the repository root using the included `Dockerfile`
- Install the package from `pyproject.toml`
- Set `WORKDIR /work` for mounted project paths
- Mount repository content into `/work` when running validation commands
