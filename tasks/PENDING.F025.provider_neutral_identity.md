# F025 – Isolate Admin backing-service integration from cloud configuration

**Status**: Pending

**Type**: Feature

**Depends On**: F024

**Description**: Remove AWS dependencies and migrate builds/packages off CodeArtifact — implement the approved non-aws identity ingress transition.

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
- `src/services/identity_provisioning_service.py`
- `src/services/webhook_handlers.py`
- `src/services/ingress_service.py`
- `src/services/provisioning_service.py`
- `src/routes/webhook_routes.py`
- `src/routes/dev_register_routes.py`
- `src/server.py`
- `test/services/test_identity_provisioning_service.py`
- `test/services/test_webhook_handlers.py`
- `test/services/test_provisioning_service.py`
- `test/routes/test_webhook_routes.py`
- `test/e2e/test_webhooks.py`
- `test/test_server.py`

Source issue is authoritative for this migration. The agreed migration supersedes old CodeArtifact-auth prerequisites only in the paths explicitly migrated by these tasks; do not rewrite unrelated framework rules.

## Goals

- Audit the existing provisioning, webhook and dev-register paths to separate business operations from Cognito event-envelope/configuration assumptions. Most backing-service integration is placeholder code: change only demonstrated local AWS coupling, and record evidence when no implementation change is needed.
- Keep provider-neutral primary/invitee provisioning, JWT validation, tenant/RBAC checks, idempotency and local registration parity in Admin. Allow backing services to be supplied through existing environment/configuration contracts; AWS endpoint/pool/client and deployment-specific mapping belong in CloudFormation configuration/overlays.
- Preserve historical cognito_sub identifiers and event-source values for compatibility. Do not rename data fields/enums, introduce a new provider, rewrite persisted identities, or add speculative schema/API changes.
- Keep optional provider-shaped webhook compatibility behind the existing integration boundary if it does not require AWS locally. Preserve Stripe/SMS behavior and ensure dev-only registration cannot become a production identity provider.
- No production identity/hosting decision is a prerequisite. If inspection finds an actual missing backing-service contract, document a narrowly scoped follow-on for review rather than build a generic adapter framework.

## Testing Expectations

- During future execution, use existing local/mock backing services to verify primary/invitee idempotency, permissions and tenant denial, webhook input mapping, historical identifiers and dev-mode boundaries without AWS credentials or service calls.
- Run pipenv run test/lint/build and the existing container → api → e2e packaging gate. Do not require a new IdP, live production migration or schema change to complete local integration isolation.
- Record which source files actually needed edits; do not churn placeholder implementations merely to remove a historical provider name.

## Outputs

- `src/services/identity_provisioning_service.py`
- `src/services/webhook_handlers.py`
- `src/services/ingress_service.py`
- `src/services/provisioning_service.py`
- `src/routes/webhook_routes.py`
- `src/routes/dev_register_routes.py`
- `src/server.py`
- `test/services/test_identity_provisioning_service.py`
- `test/services/test_webhook_handlers.py`
- `test/services/test_provisioning_service.py`
- `test/routes/test_webhook_routes.py`
- `test/e2e/test_webhooks.py`
- `test/test_server.py`
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

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
