# F019 – README, e2e, and packaging pass

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F018_dev_parity_register`  
**Description:** Align README and server startup logs with the Admin API surface, add black-box e2e coverage for operator REST and ingress, and run the full unit plus containerized e2e gate for this wave.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `README.md` — still describes a platform shell
- `src/server.py` — route log lines
- `docs/openapi.yaml`
- `test/test_server.py`
- `test/e2e/e2e_auth.py` — must include `profile_id` and `roles: ["admin"]` for api-utils 1.0.0
- `../mentorhub/Workshops/admin_journey_issues.md` — out of scope: Customer enrichment, Stripe Checkout/Portal, Cognito AdminCreateUser, Discovery list/dismiss

This is a documentation and verification task. Add tests only for gaps against F011’s **SPA** endpoint map plus the F017/F018 listeners. Do not invent new SPA endpoints. Do not add webhook or `/dev` paths to OpenAPI.

**Confirmation greps** (zero hits required except inside `tasks/`):

```bash
rg 'execute_infinite_scroll_query|after_id|has_more|next_cursor' --glob '*.py' --glob 'docs/openapi.yaml'
rg 'access_token|id_token' src/routes
```

Credential-minting HTTP routes must remain absent. Routes may mention tokens only as Bearer input.

## Goals

- `README.md` current-state and project-structure list Setting, Event, ExternalEvent list, plus a short **ingress** note that `/webhooks/*` and optional `/dev/register/*` are process listeners **not** in OpenAPI, and that Profile/Customer are provisioned by those listeners (no `/api/profile` or `/api/customer`). Pin remains `api-utils==1.0.0`.
- `README.md` curl examples cover at least:
  - `GET /api/config`
  - `GET /api/setting` (Bearer `$TOKEN`)
  - `GET /api/external-event` (optional `source`)
  - `POST /webhooks/stripe` documented as SRE/provider ingress (no Bearer; note `STRIPE_WEBHOOK_VERIFY`) — not as an SPA operation
- Token minting for tests uses `test/e2e/e2e_auth.py` / `pipenv run e2e` JWT settings — not an API route.
- `src/server.py` startup logs list every registered prefix (config, docs, metrics, event, external-event, setting, webhooks, and dev register when enabled).
- `test/test_server.py` URL assertions match the registered surface; still forbids credential-minting and journey-domain leftovers; `/api/profile`, `/api/customer`, `/api/webhooks`, ExternalEvent POST, and ExternalEvent by-id are absent.
- E2E coverage (containerized API, admin JWT from `e2e_auth.py`) for:
  - Setting list / get (empty array is acceptable)
  - Event list GET
  - ExternalEvent list GET (array; optional `source`)
  - Stripe webhook POST to `/webhooks/stripe` records without verify when `STRIPE_WEBHOOK_VERIFY` is false (or 400 on empty body if recording requires JSON — document the chosen assertion)
  - `/dev/register/primary` 404 when `REGISTRATION_DEV_MODE` is off
- `Pipfile` still pins `api-utils==1.0.0`.
- `docs/openapi.yaml` still has no `/webhooks`, `/dev/register`, `/api/profile`, or `/api/customer` paths.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — contains `/api/setting` and `/api/external-event`; does **not** contain `/webhooks` or `/api/dev`
- Record command results in **Execution Notes**.

## Outputs

- `README.md` — current Admin API surface and curl examples
- `src/server.py` — route registration log lines only if they still omit new prefixes
- `test/test_server.py` — only if assertions still drift
- `test/e2e/e2e_auth.py` — only if claims are still insufficient
- `test/e2e/test_operator_rest.py` — operator GET/POST coverage
- `test/e2e/test_webhooks.py` — ingress coverage

The agent must not update files outside this list.

## Execution Notes

1. **Documentation & Architecture Alignment:**
   - Updated `README.md` with current state, full project layout, operator BFF surface, ingress listener surface, and comprehensive curl examples for all routes.
   - Verified `src/server.py` registers and logs all active route blueprints.
2. **E2E Test Coverage:**
   - Created `test/e2e/test_operator_rest.py` with black-box integration tests for `/api/config`, `/api/setting` CRUD, `/api/event` list and create, `/api/external-event` list and source filter, and 401 unauthorized checks.
   - Created `test/e2e/test_webhooks.py` with black-box integration tests for Stripe webhook ingress idempotency, Cognito Post Confirmation account provisioning, SMS webhook listener, Developer Edition self-serve registration (`/dev/register/primary` and `/dev/register/invite`), and 404 assertions on forbidden paths.
3. **Verification Gate Results:**
   - `pipenv run test`: 81 unit tests passed.
   - `pipenv run lint`: Black format check clean.
   - `pipenv run build`: Compilation succeeded.
   - `pipenv run container`: Docker container built successfully.
   - `pipenv run api`: Microservice containers restarted and healthy.
   - `pipenv run e2e`: 10 E2E integration tests passed.
   - Zero forbidden pattern greps (`execute_infinite_scroll_query`, `next_cursor`, `access_token`, `id_token` in routes).
   - OpenAPI spec verified at `http://localhost:8389/docs/openapi.yaml` (contains `/api/setting`, `/api/event`, `/api/external-event`; strictly excludes webhook, dev, profile, customer endpoints).
