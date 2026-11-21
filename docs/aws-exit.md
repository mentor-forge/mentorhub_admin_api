# Admin API AWS exit audit

## Package delivery

Admin currently pins API Utils 1.0.4 via CodeArtifact. The public API Utils 1.0.5 wheel downloaded without credentials and matched the published checksum.

- Wheel: [api_utils-1.0.5-py3-none-any.whl](https://github.com/mentor-forge/mentorhub_api_utils/releases/download/v1.0.5/api_utils-1.0.5-py3-none-any.whl)
- SHA-256: `79de3829e2baa294497e08925908645bcea53cdf497d02b6bed71322a503d952`

Pin that exact wheel and its hash in the dependency lock. Resolve third-party dependencies through public PyPI. The similarly named PyPI package is unrelated. For future package rollbacks, restore a verified GitHub-hosted wheel pin and matching lockfile together. The rollback floor is 1.0.5.

| Surface | Current coupling | Migration |
| --- | --- | --- |
| `Pipfile`, `Pipfile.lock`, `scripts/pipenv-install.sh`, `scripts/pipenv-lock.sh` | CodeArtifact index, AWS CLI endpoint and token lookup, temporary requirements export | F022 locks the published wheel and public dependencies, preserving the install entry point with standard Pipenv commands. |
| `Dockerfile`, `scripts/docker-build.sh` | Authenticated package index passed as a build argument | F023 builds from the checked-in lock with the public wheel and retains the local container build entry point. |
| `.github/workflows/docker-push.yml` | AWS role assumption, CodeArtifact token, and build index argument | F024 removes AWS authentication and adds read-only PR validation while retaining GHCR publication on main. |
| `README.md`, `tasks/_PLANNING.md` | Active install instructions reference the old registry | F026 updates usage and records repo-local acceptance. |

The blocked F020 task is a historical CodeArtifact upgrade to 1.0.1. The current pin has already moved to 1.0.4. The checkout already includes the webhook system token's display label and writes `display_name` for provisioned Profiles where supplied. Retest the previous ingress failures as part of F025/F026 before drawing conclusions about live validation. Leave F020's historical record intact.

## Identity and runtime

The inbound Cognito route in `src/routes/webhook_routes.py` authenticates callbacks using the configured shared secret and passes the payload to `handle_cognito` in `src/services/webhook_handlers.py`. PostConfirmation dispatches primary or invitee provisioning. Other Cognito events can be recorded through `IngressService`. These paths interpret incoming events and do not make outbound AWS SDK calls.

`src/services/identity_provisioning_service.py` consumes normalized identity inputs and preserves an external subject in the existing `cognito_sub` field when provided. The development registration routes call the same provisioning entry points and use the historical Cognito source label. The label is stored compatibility data. `ProvisioningService` and `IngressService` likewise use application contracts and shared MongoIO access. Preserve compatibility, authorization, and idempotency. Keep infrastructure-specific configuration in CloudFormation. A production identity provider decision is outside this migration.

API Utils 1.0.5 maps JWT `sub` to `user_id`, requires `profile_id`, carries roles and optional `customer_id` and `mentor_id`, and exposes `display_name` from that JWT claim with an `unknown` fallback. Admin already supplies a display label on the synthetic webhook token. F022 should check the installed wheel against Admin's shared token, list/GET and MongoIO call sites and align persona fixtures where needed. Preserve service authorization, MongoIO-only data access, persisted document fields, and the OpenAPI contract.

## Installing the pinned wheel

Run `pipenv run install` to sync production and development dependencies from the committed lockfile. Run `pipenv lock` when intentionally updating a dependency, then review the resulting lock changes. PyPI serves third-party packages. Admin API installs API Utils 1.0.5 directly from its public GitHub Release wheel. The wheel URL in the Pipfile, lockfile, and requirements export includes the verified published SHA-256 digest. Neither installation nor lock generation needs registry credentials.

The local E2E token fixture supplies the signed `display_name` and existing admin role and profile claims. Admin’s application token, shared list/GET helpers, and MongoIO contracts are unchanged.

## Building the Admin API image

Run `pipenv run container` to build the usual local GHCR-tagged image. Set `ADMIN_API_IMAGE` to a separate local tag during validation so the standard tag stays available to Developer Edition. The build exports the production requirements from the committed lock, including package hashes and the direct wheel URL. It installs them from public sources with hash checking enabled. Gunicorn remains the image's separate runtime install. The build requires neither AWS nor GitHub credentials.

## Continuous integration and publishing

Pull requests targeting main run read-only validation with checkout credentials disabled. The workflow verifies the lockfile, installs its dependencies, runs lint and tests, compiles the application, and builds the container without registry login.

The separate main-branch workflow builds and publishes the same AMD64 and ARM64 image to GHCR. Its permissions are limited to repository contents read and package write. The GitHub token authenticates the GHCR login step. The Docker build receives no registry credentials or private package index.

## Local identity boundary

Admin handles incoming identity events and persists the resulting Profiles and Customers through MongoIO. Cognito PostConfirmation maps the incoming subject and organization or customer fields to the shared primary or invitee provisioning operations. Other callback events use the ingress audit path. The historical `cognito_sub` field and event source stay compatible with existing data. Stripe and SMS retain their existing verification and dispatch behavior.

Developer Edition registration calls the same provisioning operations and returns the persisted records without minting JWTs. Outside trusted Developer Edition deployments, explicitly set `REGISTRATION_DEV_MODE=false` on Admin API to disable the development routes. Admin currently defaults this flag to enabled, and the umbrella Compose configuration relies on that default. Making the default disabled requires an explicit opt-in on the Admin service in Developer Edition Compose. Coordinate that follow-up with the umbrella repo. Production provider wiring and callback verification configuration belong to the infrastructure deployment.
