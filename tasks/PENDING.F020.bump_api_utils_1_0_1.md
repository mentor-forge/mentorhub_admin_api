# F020 – Bump api-utils 1.0.1 (`token.display_name`)

**Status:** Pending  
**Type:** Feature  
**Depends On:** none  
**Description:** Implement [F-AA04 / issue #8](https://github.com/mentor-forge/mentorhub_admin_api/issues/8): pin `api-utils` to `1.0.1` and replace any use of `token.name` with `token.display_name`. Do not change Profile, Customer, or Setting document `name` fields.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — pin exact semver for `api-utils`; install via `pipenv run install` after `mh`
- `tasks/_PLANNING.md` — Shared Library / Version Bump Checklist
- `tasks/_ORCHESTRATE.md` — token-claim and signature audit before the packaging gate
- `README.md` — currently documents `api-utils==1.0.0`
- `../mentorhub_api_utils/README.md` — shared Token / list-GET / subclass contract
- `../mentorhub_api_utils/api_utils/flask_utils/token.py` — **1.0.0** local checkout still maps `to_dict()["name"]`; after install, treat the **installed** `api-utils==1.0.1` `Token.to_dict()` as the source of truth for claim keys
- `Pipfile` — currently `api-utils==1.0.0`
- `Pipfile.lock`
- `test/e2e/e2e_auth.py` — persona JWT minting (`iss` / `aud` / `sub` / `roles` / `profile_id`)
- `src/services/webhook_transport.py` — synthetic `WEBHOOK_SYSTEM_TOKEN`
- `src/services/event_service.py` — copies `dict(token)` into Event `context` when no explicit context is passed
- `src/routes/` — `create_flask_token()` consumers
- `test/services/` and `test/routes/` — mock token dicts
- `../mentorhub/Workshops/admin_journey_issues.md` — Admin is ingress + operators

**External prerequisite:** `api-utils==1.0.1` must resolve from the CodeArtifact index. If `pipenv run install` cannot resolve 1.0.1, set **Status** to `Blocked` and stop. Do not fall back to a path install of the sibling checkout.

**Token vs document `name`:** Collection documents (Profile `name`, Customer `name`, Setting `name`, Cognito payload `name`) are **not** the Token claim. Only the Flask token dict / JWT claim surface that `api_utils.flask_utils.token` exposes as `name` in 1.0.0 becomes `display_name` in 1.0.1.

**MongoDB I/O:** Service code must continue to use `MongoIO` (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`). Do not call PyMongo through `mongo.get_collection(...)`. This task should not add new service methods.

## Goals

- `Pipfile` and `Pipfile.lock` pin `api-utils==1.0.1` (single CodeArtifact `[[source]]` unchanged; keep the comment that public PyPI `api-utils` is unrelated).
- Dependencies are installed with `pipenv run install` (run `mh` first if CodeArtifact credentials are missing). Do **not** use bare `pipenv install`.
- After install, audit `api_utils.flask_utils.token.Token.to_dict` / `create_flask_token()` from the **installed 1.0.1 package**. Confirm the token dict key is `display_name` (not `name`). Also audit helper signatures (`MongoIO`, `execute_list_query` / `parse_list_request`, `encode_document`, exception classes, shared GET factories) against that installed package and fix any mismatches this bump introduces.
- Replace every Admin-API use of the token display claim:
  - `token["name"]` / `token.get("name")` / `token.name` (when `token` is the Flask token dict or `Token` object) → `display_name`
  - JWT payloads minted for tests (`test/e2e/e2e_auth.py`) include whatever claim 1.0.1 maps into `display_name` (typically JWT `display_name` or mapped from `name` — follow the installed `Token._map_claims` / `to_dict`)
  - Mock token fixtures in `test/` that intend to represent `create_flask_token()` output use `display_name` instead of `name`
  - `WEBHOOK_SYSTEM_TOKEN` includes `display_name` if 1.0.1 token dicts always expose that key (keep `user_id`, `roles`, `profile_id`)
- Event `context` copied from `dict(token)` must not keep a leftover token `name` key from this API’s own construction. Do not rename Profile/Customer/Setting document fields.
- `README.md` states the pinned `api-utils==1.0.1` contract (JSON-array list GETs, `offset`/`size` headers, no cursor envelope) and the token dict key `display_name`.
- No new domain routes. No local reimplementation of Token parsing.

### Craftsmanship Expectations

- Token claim shape is owned by `api_utils`; this API consumes it. Do not add a local alias that accepts both `name` and `display_name`.
- Do not treat document `name` (username, organization, product) as the token display claim.
- Prefer deleting obsolete `token["name"]` usage rather than leaving dual keys on synthetic tokens.

## Testing Expectations

Run all commands from this API repository root.

- **Install**
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `pipenv run install`
- **Unit / lint / build**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification (mandatory)**
  - `pipenv run container && pipenv run api && pipenv run e2e`
- **Negative / boundary**
  - Confirm tests that mint JWTs still satisfy 1.0.1 required claims (`profile_id`, roles, and `display_name` mapping). A token that only has document-style `name` and lacks the 1.0.1 display claim must not be treated as a successful Token dict.
  - Least-privileged (non-admin) cases in existing service tests still 403; do not weaken RBAC while updating fixtures.
  - `test/services/test_webhook_transport.py` still returns a system token that services accept after the key rename.

## Outputs

- `Pipfile` — pin `api-utils==1.0.1`
- `Pipfile.lock` — refresh via `pipenv run install` (use `scripts/pipenv-lock.sh` if the lock hashes must be regenerated first)
- `README.md` — document the `1.0.1` pin and `token.display_name`
- `src/services/webhook_transport.py` — synthetic token `display_name` if required by the 1.0.1 token dict
- `src/services/event_service.py` — only if Event context construction still injects token `name`
- `src/routes/*.py` — only if a route reads `token["name"]` / `token.name`
- `src/services/*.py` — only if a service reads the token display claim (not document `name`)
- `test/e2e/e2e_auth.py` — JWT claims aligned with 1.0.1 `Token`
- `test/e2e/test_operator_rest.py` — only if it asserts token `name`
- `test/e2e/test_webhooks.py` — only if it asserts token `name` (leave Cognito/profile payload `name` alone)
- `test/services/*.py` — mock tokens that represent Flask token dicts
- `test/routes/*.py` — mock `create_flask_token()` return values
- `test/services/test_webhook_transport.py` — assert `display_name` on the system token when that key is part of the contract

The agent must not update files outside this list. Skip files in the list that have no token-display-claim usage after the audit.

## Execution Notes
