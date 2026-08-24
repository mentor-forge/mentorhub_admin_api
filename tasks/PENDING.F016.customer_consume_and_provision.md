# F016 – Customer consume and identity provisioning

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F015_setting_control`  
**Description:** Local Customer consume (GET) plus the identity provisioning service used by Cognito Post Confirmation and F-W10 dev register. Create minimal Customer (Organization) + Profile in `provisioned` status and record immutable events via IngressService. No HTTP webhook or dev routes in this task (F017 / F018). No Customer enrichment.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md` — MongoIO only; fetch Customer and Profile schemas from configurator
- `README.md`
- `../mentorhub/Workshops/admin_journey_issues.md` — MVP exception: Admin may provision Profile and Customer aggregate roots; owning domains enrich later; documents start in `provisioned` status
- `../mentorhub/Specifications/architecture.yaml` — Admin **consumes** Customer (does not control PATCH); **creates** Profile
- `src/services/profile_service.py` — Admin `create_profile` (ROLE_ADMIN inbound)
- `src/services/ingress_service.py` — F014 record + Event types
- `../mentorhub_api_utils/api_utils/config/config.py` — `CUSTOMER_COLLECTION_NAME`, `EVENT_TYPE_IDENTITY_PROVISIONED`, `ROLE_ADMIN`
- `../mentorhub_api_utils/api_utils/mongo_utils/list_query.py`
- `../mentorhub_api_utils/api_utils/services/rbac.py` — `is_admin`
- `docs/openapi.yaml` — Customer GET paths from F011 (routes for Customer GET may be added here so consume is testable; webhook/dev POSTs stay F017/F018)

Fetch live schemas:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Customer.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Profile.yaml/latest/" -H "accept: application/json"
```

If the configurator is unavailable, set **Status** to `Blocked` and stop.

There is **no** shared `CustomerService` in api-utils 1.0.0. Implement a local consume + provisioned-create service. Do **not** PATCH Customer, populate `subscriptions[]`, billing fields, or other enrichment. Customer API owns that.

**Provisioning rules:**

- Minimal fields + generated `_id`s; `status` is `provisioned` when the live schema includes `status`.
- Primary org: create Customer (Organization) then owner Profile linked by `customer_id` (field names from live Profile/Customer schemas).
- Invitee: create Profile under an existing `customer_id` only; do not create a Customer; do not call Cognito AdminCreateUser (Customer API).
- Idempotent on Cognito `sub` / email when those fields exist on the live Profile schema — a retry must not create a second org.
- After writes, call `IngressService` with `EVENT_TYPE_IDENTITY_PROVISIONED` and context refs for the new Profile/Customer.
- Ingress/system callers pass a token that satisfies Admin `_check_permission` (synthetic ingress token with `ROLE_ADMIN` is acceptable). Do not mint JWTs.

**MongoDB I/O:** MongoIO only.

## Goals

- `src/services/customer_service.py` — local `CustomerService`:
  - Admin-only `_check_permission`.
  - `get_customers` / `get_customer` for consume (list JSON array via `execute_list_query`; by-id 404 when missing).
  - `create_provisioned_customer(data, token, breadcrumb)` — minimal org document in `provisioned` status. Not a general public create API.
- `src/services/identity_provisioning_service.py` — orchestration:
  - `provision_primary(email, name, organization_name, token, breadcrumb, external_ids=None)` → Profile + Customer + ingress events.
  - `provision_invitee(customer_id, email, name, token, breadcrumb, external_ids=None)` → Profile under existing Customer + ingress events.
  - Calls local `CustomerService`, `ProfileService`, and `IngressService` (service-to-service). Do not query collections from the orchestrator except through those services.
- `src/routes/customer_routes.py` — `GET ""` and `GET /<customer_id>` only. No POST/PATCH. Register `/api/customer` in `src/server.py`.
- Unit tests: provisioned status, owner `customer_id` link, invitee does not create Customer, duplicate primary is idempotent, no PATCH method, non-admin forbidden.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_customer_service.py`
  - `test/services/test_identity_provisioning_service.py`
  - `test/routes/test_customer_routes.py`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — includes `/api/customer` GET

## Outputs

- `src/services/customer_service.py`
- `src/services/identity_provisioning_service.py`
- `src/routes/customer_routes.py`
- `src/server.py` — register Customer GET blueprint
- `test/test_server.py` — `/api/customer` present; no Customer POST/PATCH
- `test/services/test_customer_service.py`
- `test/services/test_identity_provisioning_service.py`
- `test/routes/test_customer_routes.py`

The agent must not update files outside this list.

## Execution Notes
