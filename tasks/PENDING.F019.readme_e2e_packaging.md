# F019 – README, e2e, and packaging pass

**Status:** Pending  
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

This is a documentation and verification task. Add tests only for gaps against F011’s endpoint map. Do not invent new endpoints.

**Confirmation greps** (zero hits required except inside `tasks/`):

```bash
rg 'execute_infinite_scroll_query|after_id|has_more|next_cursor' --glob '*.py' --glob 'docs/openapi.yaml'
rg 'access_token|id_token' src/routes
```

Credential-minting HTTP routes must remain absent. Routes may mention tokens only as Bearer input.

## Goals

- `README.md` current-state and project-structure list Setting, Profile, Event, ExternalEvent, Customer consume, webhook ingress, and optional dev register. Pin remains `api-utils==1.0.0`.
- `README.md` curl examples cover at least:
  - `GET /api/config`
  - `GET /api/setting` (Bearer `$TOKEN`)
  - `GET /api/external-event` (optional `source`)
  - `POST /api/webhooks/stripe` (no Bearer; note `STRIPE_WEBHOOK_VERIFY`)
- Token minting for tests uses `test/e2e/e2e_auth.py` / `pipenv run e2e` JWT settings — not an API route.
- `src/server.py` startup logs list every registered prefix (config, docs, metrics, profile, event, external-event, setting, customer, webhooks, and dev register when enabled).
- `test/test_server.py` URL assertions match the registered surface; still forbids credential-minting and journey-domain leftovers; still forbids Profile PATCH and Customer POST/PATCH.
- E2E coverage (containerized API, admin JWT from `e2e_auth.py`) for:
  - Setting list / get (empty array is acceptable)
  - Profile list GET
  - ExternalEvent get-by-id 404 for an unknown id
  - Stripe webhook POST records without verify when `STRIPE_WEBHOOK_VERIFY` is false (or 400 on empty body if recording requires JSON — document the chosen assertion)
  - `/api/dev/register/primary` 404 when `REGISTRATION_DEV_MODE` is off
- `Pipfile` still pins `api-utils==1.0.0`.

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
  - `curl -s http://localhost:8389/docs/openapi.yaml` — contains `/api/setting`, `/api/webhooks/stripe`, `/api/external-event`
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
