# F014 – Ingress Event + ExternalEvent write layer

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F013_event_and_external_event_routes`  
**Description:** Shared ingress service for append-only ExternalEvent and Event writes used by webhook handlers (F017) and identity provisioning (F016). Normalize payload metadata; no domain-specific business logic. Designed so a future EventBridge/SQS bus can replace MongoDB writes without changing consumer contracts.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub/Workshops/admin_journey_issues.md` — F-AA02; MongoDB is the MVP bus; consumers must not depend on Mongo-specific polling details
- `src/services/external_event_service.py`
- `src/services/event_service.py`
- `../mentorhub_api_utils/api_utils/services/external_event_service.py` — thin create; unique `source` + `external_id` idempotency is **this** layer’s job
- `../mentorhub_api_utils/api_utils/services/event_service.py` — shared `create_event` overwrites `context` with `dict(token)`. Ingress events need context refs for the **provisioned** Profile/Customer, not the webhook caller. Override or wrap locally; do not change `api_utils` in this repo
- `../mentorhub_api_utils/api_utils/config/config.py` — `EVENT_TYPE_EXTERNAL_RECEIVED`, `EVENT_TYPE_IDENTITY_PROVISIONED`
- `docs/openapi.yaml` — ExternalEvent / Event field names from F011 (confirm against configurator if needed)

Re-fetch if F011 notes are incomplete:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/ExternalEvent.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

If the configurator is unavailable, set **Status** to `Blocked` and stop.

**ExternalEvent fields (confirm live):** `source`, `external_id`, `payload_hash`, `normalized_body`, `created`. Append-only. `source` enum is whatever the live schema lists (planning snapshot: `cognito` | `stripe`). Do not invent extra source values.

**Idempotency:** unique `source` + `external_id`. On duplicate, return the existing ExternalEvent (do not raise to webhook callers). Duplicate Mongo unique-index errors from `create_document` should be translated into a fetch-and-return of the existing document.

**Consumer contract:** callers receive the created (or existing) ExternalEvent plus the created Event. Do not leak Mongo connection details, collection names, or change-stream semantics. A later bus should be able to replace the Mongo writes behind this service without changing those return shapes.

**MongoDB I/O:** MongoIO only. Encode string ids with `encode_document` immediately before MongoIO.

No HTTP routes in this task.

## Goals

- `src/services/ingress_service.py` — `IngressService` orchestration (not a collection-aligned CRUD class; it **calls** local `ExternalEventService` and `EventService`):
  - `record_external_payload(source, external_id, raw_payload, token, breadcrumb) -> dict` with at least `external_event` and `event`.
  - Normalize metadata: `source`, `external_id`, SHA-256 `payload_hash` of the canonical raw body, `normalized_body` as a JSON object suitable for consumers (pass through parsed JSON; do not interpret Stripe/Cognito business fields).
  - Idempotent on `(source, external_id)`: second call returns the original ExternalEvent and does **not** append a second Event.
  - Event `type` is `Config.EVENT_TYPE_EXTERNAL_RECEIVED` unless the caller passes a different allowed type (provisioning will pass `EVENT_TYPE_IDENTITY_PROVISIONED` in F016).
- Local `EventService` (or IngressService helper) must set Event `context` from explicit refs (`profile_id`, `customer_id`, and other ids the live Event schema allows) when provided, instead of blindly copying the webhook/service token. Operator `POST /api/event` from F013 may keep shared token-as-context behavior. Do **not** add `POST /api/external-event`; ingress calls `ExternalEventService.create_external_event` directly.
- No Stripe Checkout, subscription mutation, Customer enrichment, or Profile PATCH.
- Unit tests mock MongoIO / subclass creates: hash stability, normalize shape, duplicate `external_id` is idempotent, Event context refs are the provisioned ids when supplied.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_ingress_service.py` — create path, hash, idempotent duplicate, context refs, no domain-field interpretation
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — still served

## Outputs

- `src/services/ingress_service.py`
- `src/services/event_service.py` — only if an override is required for ingress context refs
- `src/services/external_event_service.py` — only if a get-by-`source`+`external_id` helper is required for idempotency
- `test/services/test_ingress_service.py`
- `test/services/test_event_service.py` — only if EventService gained an override

The agent must not update files outside this list.

## Execution Notes

1. **Ingress Service Implementation:**
   - Implemented `src/services/ingress_service.py` with `record_external_payload`, `compute_payload_hash` (deterministic SHA-256), and `normalize_payload_body`.
   - Enhanced `src/services/external_event_service.py` with `get_by_source_and_external_id` for idempotency queries.
   - Overrode `create_event` in `src/services/event_service.py` to allow passing explicit `context` references (e.g., provisioned `profile_id`, `customer_id`).
2. **Testing:**
   - Created `test/services/test_ingress_service.py` verifying hash determinism, payload normalization, event recording, and idempotent duplicate handling.
   - Updated `test/services/test_event_service.py` testing explicit context handling.
   - `pipenv run test`: All 34 tests passed.
   - `pipenv run lint`: Black formatting check clean.
   - `pipenv run build`: Compilation clean.
3. **Packaging Verification:**
   - `pipenv run container`: Docker image built.
   - `pipenv run api`: API container restarted.
   - Verified `/docs/openapi.yaml` served.
