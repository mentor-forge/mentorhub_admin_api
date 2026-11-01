# F025 – Implement the approved non-AWS identity ingress transition

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

- Gate implementation on the central identity decision: authentication/signing, provider event envelope, claims, registration/invites, identity mapping, legacy cognito_sub and rollback must be recorded. Do not infer schemas from sibling files; require live authoritative API/configurator contracts if changing persisted shapes.
- Replace active Cognito-specific ingress/provisioning dependency with the approved non-AWS contract in existing webhook/dev-register/service boundaries. Retain historical Cognito identifiers/audit entries for compatibility and do not rewrite data or invent new MongoDB enum values.
- Preserve idempotent primary/invitee provisioning, tenant scoping, privileged ingress checks, Stripe/SMS behavior and provider-neutral JWT validation. Development-only registration must stay disabled in production; local parity is not a production IdP.
- If the decision needs schema changes in excluded utility repos or new adapter/output files, stop and request a scoped follow-on plan before proceeding; do not expand this task silently.

### Craftsmanship Expectations

Keep package, auth and deployment ownership in the existing shared modules. Preserve APIs and runtime contracts unless the recorded migration decision explicitly requires a change; remove obsolete AWS auth knowledge rather than duplicate it. Keep every dependency reference reproducible.

## Testing Expectations

These checks are for future execution; none were run while creating this plan.

- External prerequisite: approved I-WE01 identity contract, non-AWS provider/test environment and any needed live schema verification. Test primary/invitee idempotency, source event mapping, invalid signature/auth, role/tenant denial, historic identifiers and production dev-route exclusion. Run pipenv run test/lint/build and mandatory container → api → e2e gate; no production data migration.

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

Where a task requires an unpublished release, an undecided production contract, unavailable live schema or operator evidence, stop execution at that prerequisite and report it; do not guess values or substitute the unrelated PyPI api-utils package. Pending status describes the plan's review state, not proof that external execution gates are satisfied.

## External prerequisites

API utils release and verified wheel URL/hash: https://github.com/mentor-forge/mentorhub_api_utils/issues/36. Production identity/hosting decisions and cutover readiness: https://github.com/mentor-forge/mentorhub/issues/80. These are execution gates, not local task dependencies. No excluded utility-repo changes are authorized.

## Execution Notes

Reserved for the execution agent. No implementation, tests, service changes or publication have been performed.
