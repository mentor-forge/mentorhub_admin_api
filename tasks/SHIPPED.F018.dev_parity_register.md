# F018 – Dev-parity register and join endpoints

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F017_webhook_transport`  
**Description:** F-W10 login.html register/join tabs call Admin ingress so the local path matches production Post Confirmation. Reuse IdentityProvisioningService. Do not mint JWTs. Do not expose Customer enrichment or Stripe Checkout.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — domain APIs must **not** register HTTP routes that mint credentials
- `tasks/_PLANNING.md`
- `README.md`
- `../mentorhub/Research/local_dev_mocks.md` — register/join body shapes (`email`, `name`, `organization_name` / `customer_id`); login.html mints JWT **after** the API returns ids. Path prefix in this repo is `/dev/register` (outside `/api`), not `/api/dev/register`.
- `../mentorhub/Workshops/admin_journey_issues.md` — additional members are invited by the org; AdminCreateUser stays on Customer API; Admin only provisions a Profile under `customer_id`
- `docs/openapi.yaml` — F011 SPA contract; **do not** add login.html register paths
- `src/services/identity_provisioning_service.py`
- `src/server.py`
- `test/test_server.py` — existing forbidden credential-issuer path must remain 404
- `test/e2e/e2e_auth.py`

**Gate:** both routes are registered only when `REGISTRATION_DEV_MODE` is a truthy env value (`true` / `1`). When disabled, the paths should 404 (do not leak a 403 that implies the route exists in production). Read the flag from `os.environ`; do not extend `api_utils.Config`.

**Shared layer:** these routes call the same `IdentityProvisioningService` methods as the Cognito webhook handler. Do not fork create logic.

**Responses:** return the provisioned documents (Profile, and Customer on primary) so login.html can mint a JWT. Never return `access_token` / `id_token` / a signed JWT.

Invite does **not** send email and does **not** call Cognito AdminCreateUser.

## Goals

- `src/routes/dev_register_routes.py` — `POST /primary` and `POST /invite` under prefix `/dev/register` (not under `/api`; login.html is not the Admin SPA). HTTP-only; pass JSON to `IdentityProvisioningService`. Do **not** add these paths to `docs/openapi.yaml`.
- When `REGISTRATION_DEV_MODE` is off, do not register the blueprint (preferred) or return 404 from the handlers.
- `src/server.py` registers the blueprint only in dev mode and logs that fact.
- `test/test_server.py` still asserts the credential-issuer path is absent. Optionally assert `/dev/register/primary` is absent when the flag is off (document how the test sets env).
- Route tests: primary returns Profile + Customer without a token field; invite does not create a Customer; disabled mode 404; duplicate primary is idempotent via the service.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/routes/test_dev_register_routes.py`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - Confirm `/dev/register/primary` is 404 in the default container env unless compose sets `REGISTRATION_DEV_MODE` (record the observed behavior in Execution Notes)
  - `curl -s http://localhost:8389/docs/openapi.yaml` — must **not** contain `/dev/register` or `/api/dev`

## Outputs

- `src/routes/dev_register_routes.py`
- `src/server.py` — conditional register
- `test/test_server.py` — only if URL assertions need updating
- `test/routes/test_dev_register_routes.py`

The agent must not update files outside this list.

## Execution Notes

1. **Dev Parity Registration Routes:**
   - Created `src/routes/dev_register_routes.py` with `POST /primary` (alias `/organization`) and `POST /invite` (alias `/join`) mounted at `/dev/register`.
   - Dispatches to `IdentityProvisioningService.provision_primary` and `IdentityProvisioningService.provision_invitee`.
   - Gate controlled via `REGISTRATION_DEV_MODE` environment variable returning 404 when disabled.
   - Response bodies return provisioned `Profile` and `Customer` documents; no JWTs or credentials are minted by the API.
2. **Testing:**
   - Created `test/routes/test_dev_register_routes.py`.
   - Updated `test/test_server.py` asserting `/dev/register/*` routes exist and `/api/dev` does not.
   - `pipenv run test`: All 81 tests passed.
   - `pipenv run lint`: Black formatted and lint clean.
   - `pipenv run build`: Clean compilation.
3. **Packaging Verification:**
   - `pipenv run container`: Docker image built.
   - `pipenv run api`: Containers restarted.
   - Verified live `POST /dev/register/primary` returns 201 with Customer and Profile, `POST /dev/register/invite` returns 201 under existing Customer, and `/docs/openapi.yaml` excludes dev register endpoints.
