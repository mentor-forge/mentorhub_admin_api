# F022 – Migrate API dependency source and locking to a Release wheel

**Status**: Shipped

**Type**: Feature

**Depends On**: F021

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — migrate api dependency source and locking to a release wheel.

**Issue**: [I-AA01](https://github.com/mentor-forge/mentorhub_admin_api/issues/12)

## Path anchoring

All output paths are relative to this repository root. Sibling references are read-only context permitted by the repo planning guide.

## Context

- `README.md`
- `tasks/_PLANNING.md`
- `tasks/_ORCHESTRATE.md`
- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/sre_standards.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/flask_utils/token.py`
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py`
- `Pipfile`
- `Pipfile.lock`
- `scripts/pipenv-install.sh`
- `scripts/pipenv-lock.sh`
- `test/e2e/e2e_auth.py`

Source issue is authoritative for this migration. The agreed migration supersedes old CodeArtifact-auth prerequisites only in the paths explicitly migrated by these tasks; do not rewrite unrelated framework rules.

## Goals

- Change the sole third-party index to public PyPI and api-utils to an exact public GitHub Release wheel URL with its verified version/hash. Never fall back to the unrelated PyPI api-utils, Git main or floating latest.
- Replace scripts/pipenv-install.sh and pipenv-lock.sh AWS token/helper usage with AWS-free public resolution while preserving pipenv run install and lock entrypoints. Regenerate Pipfile.lock and verify pipenv sync/requirements preserve the direct wheel origin and hashes.
- Audit Token display_name/profile/customer/mentor claim requirements and helper signatures; align test/e2e/e2e_auth.py only if necessary for the chosen release. Do not silently absorb unrelated upstream API changes or alter service data schemas.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- External prerequisite: I-UA01 published wheel available. Run pipenv run install, lock then locked sync in a clean temp environment with no AWS CLI/profile; verify installed api_utils origin/version/Config/token exports, pipenv run test, lint and build. Perform mandatory pipenv run container && pipenv run api && pipenv run e2e after the container task is complete; do not misreport the intermediate old Dockerfile as migrated.

## Outputs

- `Pipfile`
- `Pipfile.lock`
- `scripts/pipenv-install.sh`
- `scripts/pipenv-lock.sh`
- `test/e2e/e2e_auth.py`
- `docs/aws-exit.md`

Only these implementation files may change. The orchestrator may also update/rename this task record under the established lifecycle.

## Execution boundary

This is a reviewable plan, not an execution record. Execute only this task's listed outputs when orchestration is separately authorized. Do not touch excluded MongoDB/Runbook utility repos, publish packages/tags, mutate issue/project state, or delete/provision AWS resources as a side effect. Future workflow publication happens only through the reviewed maintainer release path.

Where a task requires an unpublished release, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Cloud-agnostic local configuration and integration boundary: https://github.com/mentor-forge/mentorhub/issues/80. No production identity/hosting decision blocks this package/build work. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Cloud-agnostic deployment boundary

The deliverable is a cloud-agnostic **local** deployment plus the agreed GitHub dependency/build migration. Existing identity/hosting implementations are largely placeholders: audit actual executable dependencies before proposing changes. Selecting, implementing or migrating to a production IdP/hosting provider is not a prerequisite for library releases, journey package/build/CI changes or local acceptance.

Keep application-facing backing-service contracts and environment settings provider neutral. Concentrate necessary integration changes in Admin API and DeveloperEdition/docker-compose.yaml where inspection proves coupling; preserve the existing shared JWT/redirect contracts and local persona/mocked-service behavior. Do not create per-journey provider adapters, new identity schemas or a general multi-cloud framework speculatively.

Cloud-specific provisioning, backing-service configuration, identity-provider wiring, roles/secrets and deployment overlays belong to the relevant infrastructure repo: mentorhub_cloudformation owns AWS, including future CodeArtifact provisioning. Future separate repos may implement Google, Microsoft/Azure, IBM or Red Hat platforms against the same contracts; do not create or implement them in this effort. Core compose must not require AWS accounts, credentials or endpoints. A locally optional emulator is not a live AWS dependency; retain it only if useful without making it a required cloud-specific integration.

AWS inventory, secure backup/restore evidence and separately approved decommissioning remain I-S01 responsibilities. Production provider selection or a live production cutover is future infrastructure/integration work, not an acceptance gate for the cloud-agnostic local stack.

## Execution Notes

Replaced the CodeArtifact index with public PyPI and pinned API Utils 1.0.5 to its public GitHub wheel. Pipenv does not emit a separate hash for a direct wheel URL, so its URL includes the SHA-256 digest verified against the published checksum. The regenerated lockfile and hashed requirements export preserve that URL and digest.

Removed the two AWS shell wrappers. `pipenv run install` now runs `pipenv sync --dev`, and `pipenv lock` regenerates the lockfile. Updated the E2E token fixture to send the current `display_name` JWT claim.

Verified the wheel download checksum, lock and requirements export, clean Python 3.12 install and repeated sync, installed wheel origin, checksum and version, Config/MongoIO and token exports, and token role/profile/customer/mentor claim mapping. With AWS profile and credential environment variables unset, 81 non-E2E tests, Black lint, and Python compilation passed. Container, runtime, and E2E verification follows the Docker migration.
