# F011 – OpenAPI for Admin SPA operator REST

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F010_pin_api_utils_1_0_0`  
**Description:** Replace the platform-shell OpenAPI with the Admin **SPA / operator REST** contract: Setting control, Event list/create, and ExternalEvent list. Component schemas come from the running configurator. No Python route implementation in this task. Webhook and login.html register listeners are **not** part of this spec. Profile and Customer have **no** HTTP surface (ingress provisions them via services).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; OpenAPI is the contract between the API and **SPA** engineers (BFF); Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — OpenAPI is grounded in the database validation schema; Create / Retrieve / Patch
- `tasks/_PLANNING.md` — fetch schemas from the running configurator; do not read dictionary YAML from other repos
- `README.md`
- `../mentorhub_api_utils/README.md` — list GET is a JSON **array**; pagination is request headers `offset` (default `0`) and `size` (default `20`, max `100`); query `contains` / `in_list` plus `sort_by` / `order`; no cursor envelope; no pagination response headers
- `docs/openapi.yaml` — current spec after F010 (config, metrics, errors only)
- `../mentorhub/Workshops/admin_journey_issues.md` — ingress verifies, normalizes, provisions, records events; no domain workflows beyond provisioning
- `../mentorhub/Specifications/architecture.yaml` — Admin **controls** ExternalEvent and Setting; **creates** Event and Profile; **consumes** Profile and Customer
- `../mentorhub/Research/local_dev_mocks.md` — login.html register/join is **not** Admin SPA; omit from this spec (F018)
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — Event list only; ExternalEvent factory is by-id only (do **not** document by-id; F013 implements a local list)
- `../mentorhub_api_utils/api_utils/services/event_service.py` — `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`

**Definitive schemas** must be fetched from the running MongoDB configurator. Start the backing database if needed (`pipenv run db`), then:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/ExternalEvent.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Setting.yaml/latest/" -H "accept: application/json"
```

If the configurator is unavailable, set **Status** to `Blocked` and stop — do not fall back to dictionary YAML in another repository.

**Auth (this spec):** every documented `/api/*` operation except `/metrics` requires Bearer JWT whose `roles` contain `admin` (`Config.ROLE_ADMIN`).

**Not SPA endpoints — omit from OpenAPI:**

- Provider webhooks (F017: `/webhooks/stripe`, `/webhooks/cognito`, `/webhooks/sms`). Same Admin API **process**, outside `/api`.
- F-W10 login.html register/join (`/dev/register/*`, F018).
- Profile and Customer HTTP of any method. Ingress (F016–F018) creates provisioned documents through services, not `/api/profile` or `/api/customer`.
- `POST /api/external-event` and `GET /api/external-event/{id}`. Operators list ingress via `GET /api/external-event`; append happens in `IngressService`.

**Out of scope for the spec:** Profile/Customer paths; ExternalEvent POST and get-by-id; Profile PATCH; Customer PATCH / enrichment; Stripe Checkout / Portal; Cognito `AdminCreateUser`; credential-minting paths; webhook and dev-register operations.

### Endpoint map

Operator REST (Bearer JWT, `roles` contains `admin`):

| Method and path | Body in | Body out | Notes |
| --- | --- | --- | --- |
| `GET /api/event` | — | `Event[]` | shared factory list; `offset`/`size` headers |
| `POST /api/event` | Event create subset (`type`) | created `Event` | |
| `GET /api/external-event` | — | `ExternalEvent[]` | list only; filter `source`; no by-id; no POST |
| `GET /api/setting` | — | `Setting[]` | optional filter by `type` |
| `GET /api/setting/{setting_id}` | — | `Setting` | |
| `POST /api/setting` | Setting create subset | created `Setting` | Admin **controls** Setting |
| `PATCH /api/setting/{setting_id}` | Setting patch subset | updated `Setting` | |

Keep existing `/api/config` and `/metrics`. The SPA observes webhook results via `GET /api/external-event`, not by calling webhook listeners and not via Profile/Customer GET.

## Goals

- `docs/openapi.yaml` `info` describes Admin as the **operator REST / Admin SPA** BFF (Setting control, Event list/create, ExternalEvent list). It must **not** describe webhook listeners, login.html register, Profile, or Customer as API operations. No Customer-domain enrichment or Stripe Checkout.
- Component schemas `Event`, `ExternalEvent`, `Setting` aligned to the latest configurator JSON schemas (types, required, descriptions). Factor a shared `Breadcrumb` if those schemas repeat it. Do **not** add unused `Profile` or `Customer` component schemas.
- Create request bodies omit system-managed fields (`_id`, `created`, `saved` where the collection has them). ExternalEvent is append-only (no `saved`) and has no POST in this spec.
- Every list GET:
  - Requires bearer auth.
  - Documents `offset` and `size` **request headers** (defaults `0` / `20`, max `100`).
  - `200` body is a JSON **array** (not `{items, has_more, next_cursor}`).
  - Documents `contains` / `in_list` filters and `sort_by` / `order` from the matching `api_utils` `*_LIST_FILTERS` / `*_LIST_ORDER` where a shared service exists. Setting list documents a `type` filter. ExternalEvent list documents a `source` filter.
- Setting by-id GET: path param `^[0-9a-fA-F]{24}$`; `404` when missing or hidden by outbound RBAC. No ExternalEvent by-id path.
- Operator operations document `401` / `403` (missing admin role) / `400` / `500` as appropriate.
- Tags: `Event`, `ExternalEvent`, `Setting`, plus existing Config / Metrics. No `Profile`, `Customer`, `Webhooks`, or `Dev` tags.
- Zero paths under `/webhooks`, `/api/webhooks`, `/api/dev`, `/api/profile`, `/api/customer`. No `POST /api/external-event`. No `GET /api/external-event/{id}`.
- The document remains valid OpenAPI 3.0.x.

## Testing Expectations

Run all commands from this API repository root.

- **Schema fetch** — all three configurator curls succeed; record schema versions in **Execution Notes**.
- **Spec validation**
  - `python3 -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - Confirm every path in the operator REST table above, array list responses, `offset`/`size` headers, no Profile/Customer paths, no ExternalEvent POST or by-id, no credential-minting paths, and **no** `/webhooks`, `/api/webhooks`, or `/api/dev` paths.
  - Confirm no `after_id`, `has_more`, or `next_cursor`.
- **Unit / lint / build** (must still pass after a docs-only change)
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — served file includes the new paths and omits Profile/Customer/webhook paths

## Outputs

- `docs/openapi.yaml` — Admin SPA operator REST from the endpoint map; configurator-grounded Event / ExternalEvent / Setting schemas; keep Config / Metrics / bearerAuth / Error; **no** Profile, Customer, webhook, or `/api/dev` operations

The agent must not update files outside this list.

## Execution Notes
