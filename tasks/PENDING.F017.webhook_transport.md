# F017 – Webhook transport and Stripe / Cognito / SMS handlers

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F016_customer_consume_and_provision`  
**Description:** HTTP ingress for Stripe, Cognito Post Confirmation, and SMS. Verify signatures, normalize via IngressService, and provision identities on Cognito Post Confirmation. SMS is a transport placeholder. No Customer enrichment, Stripe Checkout, or business workflow.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — APIs validate tokens; they must **not** mint JWTs; routes do not alter payloads beyond HTTP concerns
- `tasks/_PLANNING.md`
- `README.md`
- `../mentorhub/Workshops/admin_journey_issues.md` — F-AA01; verify, normalize, provision, record; SMS was listed as a webhook source in the refactor pass but is placeholder-only
- `../mentorhub/Research/local_dev_mocks.md` — `STRIPE_WEBHOOK_VERIFY=false` locally; stripe-mock posts to Admin ingress
- `docs/openapi.yaml` — F011 is the Admin SPA contract only; **do not** add webhook operations to it
- `src/services/ingress_service.py`
- `src/services/identity_provisioning_service.py`
- `src/server.py`

**URL space (locked):** these are provider ingress listeners on the Admin API **process**, not BFF `/api` operations. Register:

| Method and path | Caller |
| --- | --- |
| `POST /webhooks/stripe` | Stripe / stripe-mock |
| `POST /webhooks/cognito` | Cognito Post Confirmation (F-S01) |
| `POST /webhooks/sms` | SMS provider (placeholder) |

Do **not** mount them under `/api`. Do **not** add them to `docs/openapi.yaml` (SPA explorer). Auth is signature / shared secret, not operator JWT.

**Stripe:**

- Read raw request body for signature verification.
- Env `STRIPE_WEBHOOK_VERIFY` (default `false` for local dev). When true, verify `Stripe-Signature` with `STRIPE_WEBHOOK_SECRET`. When false, skip verify but still normalize + record.
- `external_id` = Stripe event id; `source` = `stripe` (or live enum value).
- Record via `IngressService` only. Do **not** update Customer.subscriptions, Payment, discounts, or create Checkout sessions.

**Cognito Post Confirmation:**

- Production (F-S01) will call this with a service credential. Implement a header/shared-secret check when `COGNITO_WEBHOOK_SECRET` (or equivalent env) is set; if unset (local), accept the JSON body so F-W10/dev can proceed.
- Map the Post Confirmation payload to `provision_primary` (email, name, org name from the live payload fields you can find; document the mapping in Execution Notes). Then `IngressService.record_external_payload` with `source` = `cognito` and the Cognito event / `sub` as `external_id`.
- Idempotent with F016.

**SMS:**

- Placeholder handler on the same transport (raw body in, verify hook optional).
- Persist an ExternalEvent **only if** the live ExternalEvent `source` enum includes `sms`. Otherwise return success after logging and do not write an invalid `source`. Document the choice in Execution Notes.

**Config:** do not extend `api_utils.Config` from this repo. Read `STRIPE_WEBHOOK_VERIFY`, `STRIPE_WEBHOOK_SECRET`, `COGNITO_WEBHOOK_SECRET` from `os.environ`.

**External prerequisite:** production Cognito wiring (F-S01) is outside this repo. This task ships the Admin HTTP handler; it must work locally without that stack.

No Stripe SDK requirement unless verification when `STRIPE_WEBHOOK_VERIFY=true` needs it; prefer the official Stripe signature algorithm (HMAC SHA256 of the signed payload) documented by Stripe. Do not add Checkout or Billing APIs.

## Goals

- `src/services/webhook_transport.py` — raw body, signature/secret verification helpers, synthetic ingress token/breadcrumb.
- `src/services/webhook_handlers.py` (or equivalently named module) — `handle_stripe`, `handle_cognito_post_confirmation`, `handle_sms` as event handlers. Handlers call IngressService / IdentityProvisioningService; they do not implement collection I/O themselves.
- `src/routes/webhook_routes.py` — `POST /webhooks/stripe`, `/webhooks/cognito`, `/webhooks/sms`; HTTP layer only. After verification, build a synthetic ingress token (`roles` includes `Config.ROLE_ADMIN`, `user_id` e.g. `ingress`) and breadcrumb for service calls.
- `src/server.py` registers a blueprint at `/webhooks` (not `/api/webhooks`) and logs it. Do not add these paths to `docs/openapi.yaml`.
- `test/test_server.py` asserts `/webhooks/stripe` (etc.) exist, `/api/webhooks/` does **not**, and credential-minting routes still do not.
- Unit tests: Stripe verify on/off, duplicate Stripe id idempotent, Cognito calls `provision_primary`, SMS placeholder does not write an illegal `source`, no JWT in responses.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_webhook_transport.py`
  - `test/services/test_webhook_handlers.py`
  - `test/routes/test_webhook_routes.py`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8389/webhooks/stripe` — route exists (not 404); exact status may be 400 without a body
  - `curl -s http://localhost:8389/docs/openapi.yaml` — must **not** contain `/webhooks` or `/api/webhooks`

## Outputs

- `src/services/webhook_transport.py`
- `src/services/webhook_handlers.py`
- `src/routes/webhook_routes.py`
- `src/server.py` — register webhook blueprint
- `test/test_server.py`
- `test/services/test_webhook_transport.py`
- `test/services/test_webhook_handlers.py`
- `test/routes/test_webhook_routes.py`

The agent must not update files outside this list.

## Execution Notes
