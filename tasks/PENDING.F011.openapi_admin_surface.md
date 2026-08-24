# F011 – OpenAPI for Admin control, consume, and ingress

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F010_pin_api_utils_1_0_0`  
**Description:** Replace the platform-shell OpenAPI with the Admin API contract: Setting control, Profile/Event/ExternalEvent create + consume, Customer consume, webhook ingress, and dev-parity register. Component schemas come from the running configurator. No Python route implementation in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — OpenAPI is grounded in the database validation schema; Create / Retrieve / Patch
- `tasks/_PLANNING.md` — fetch schemas from the running configurator; do not read dictionary YAML from other repos
- `README.md`
- `../mentorhub_api_utils/README.md` — list GET is a JSON **array**; pagination is request headers `offset` (default `0`) and `size` (default `20`, max `100`); query `contains` / `in_list` plus `sort_by` / `order`; no cursor envelope; no pagination response headers
- `docs/openapi.yaml` — current spec after F010 (config, metrics, errors only)
- `../mentorhub/Workshops/admin_journey_issues.md` — ingress verifies, normalizes, provisions, records events; no domain workflows beyond provisioning
- `../mentorhub/Specifications/architecture.yaml` — Admin **controls** ExternalEvent and Setting; **creates** Event and Profile; **consumes** Profile and Customer
- `../mentorhub/Research/local_dev_mocks.md` — `POST /api/dev/register/primary` and `/api/dev/register/invite`; APIs must not mint JWTs
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — Profile list+by-id; Event list only; ExternalEvent by-id only
- `../mentorhub_api_utils/api_utils/services/event_service.py` — `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`
- `../mentorhub_api_utils/api_utils/services/profile_service.py` — `PROFILE_LIST_FILTERS` / `PROFILE_LIST_ORDER`

**Definitive schemas** must be fetched from the running MongoDB configurator. Start the backing database if needed (`pipenv run db`), then:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Profile.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/ExternalEvent.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Setting.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Customer.yaml/latest/" -H "accept: application/json"
```

If the configurator is unavailable, set **Status** to `Blocked` and stop — do not fall back to dictionary YAML in another repository.

**Auth split (locked for this wave):**

- Operator REST (Setting, Profile, Event, ExternalEvent, Customer) requires Bearer JWT whose `roles` contain `admin` (`Config.ROLE_ADMIN`).
- Webhook POST ingress does **not** use operator JWT. Stripe uses signature verification; Cognito uses a service credential after F-S01. Document that on those operations.
- Dev register routes are gated by `REGISTRATION_DEV_MODE` and also do **not** mint JWTs (login.html mints after the API returns ids).

**Out of scope for the spec:** Profile PATCH (Customer **controls** Profile); Customer PATCH / enrichment; Stripe Checkout / Portal; Cognito `AdminCreateUser`; credential-minting paths.

### Endpoint map

Operator REST (Bearer JWT, `roles` contains `admin`):

| Method and path | Body in | Body out | Notes |
| --- | --- | --- | --- |
| `GET /api/profile` | — | `Profile[]` | shared factory list; `offset`/`size` headers |
| `GET /api/profile/{profile_id}` | — | `Profile` | shared factory by-id |
| `POST /api/profile` | Profile create subset | created `Profile` | no PATCH |
| `GET /api/event` | — | `Event[]` | shared factory list |
| `POST /api/event` | Event create subset (`type`) | created `Event` | |
| `GET /api/external-event` | — | `ExternalEvent[]` | **Admin list** (factory is by-id only); filter `source` |
| `GET /api/external-event/{event_id}` | — | `ExternalEvent` | shared factory by-id |
| `POST /api/external-event` | ExternalEvent create subset | created `ExternalEvent` | append-only |
| `GET /api/setting` | — | `Setting[]` | optional filter by `type` |
| `GET /api/setting/{setting_id}` | — | `Setting` | |
| `POST /api/setting` | Setting create subset | created `Setting` | Admin **controls** Setting |
| `PATCH /api/setting/{setting_id}` | Setting patch subset | updated `Setting` | |
| `GET /api/customer` | — | `Customer[]` | consume only |
| `GET /api/customer/{customer_id}` | — | `Customer` | consume only; no POST/PATCH here |

Webhook ingress (no operator JWT):

| Method and path | Auth | Behavior |
| --- | --- | --- |
| `POST /api/webhooks/stripe` | Stripe-Signature; `STRIPE_WEBHOOK_VERIFY` true in prod, false in local dev | verify, normalize, record ExternalEvent/Event; no subscription/Checkout logic |
| `POST /api/webhooks/cognito` | service credential (prod); may be relaxed in local dev | Post Confirmation: provision Profile + Customer (`provisioned`), record events |
| `POST /api/webhooks/sms` | transport placeholder | no domain logic; persist only if live ExternalEvent `source` enum includes `sms` |

Dev parity (F-W10; `REGISTRATION_DEV_MODE`; do **not** mint JWT):

| Method and path | Body in | Body out |
| --- | --- | --- |
| `POST /api/dev/register/primary` | `email`, `name`, `organization_name` | provisioned `Profile` + `Customer` (ids for login.html to mint JWT) |
| `POST /api/dev/register/invite` | `customer_id`, `email`, `name` | provisioned `Profile` under existing Customer (no AdminCreateUser) |

Keep existing `/api/config` and `/metrics`.

## Goals

- `docs/openapi.yaml` `info` describes Admin as operator REST plus ingress (webhooks, identity provisioning, immutable events). No Customer-domain enrichment or Stripe Checkout.
- Component schemas `Profile`, `Event`, `ExternalEvent`, `Setting`, `Customer` aligned to the latest configurator JSON schemas (types, required, descriptions). Factor a shared `Breadcrumb` if those schemas repeat it.
- Create request bodies omit system-managed fields (`_id`, `created`, `saved` where the collection has them). ExternalEvent is append-only (no `saved`).
- Every list GET:
  - Requires bearer auth (except webhooks / dev register as specified).
  - Documents `offset` and `size` **request headers** (defaults `0` / `20`, max `100`).
  - `200` body is a JSON **array** (not `{items, has_more, next_cursor}`).
  - Documents `contains` / `in_list` filters and `sort_by` / `order` from the matching `api_utils` `*_LIST_FILTERS` / `*_LIST_ORDER` where a shared service exists. Setting list documents a `type` filter. ExternalEvent list documents a `source` filter.
- `GET /api/external-event/{event_id}` and other by-id GETs: path param `^[0-9a-fA-F]{24}$`; `404` when missing or hidden by outbound RBAC.
- Operator operations document `401` / `403` (missing admin role) / `400` / `500` as appropriate.
- Webhook operations document raw provider JSON bodies (`additionalProperties: true`), success `200` or `204`, and `400`/`401` on failed verification. Descriptions state: verify → normalize → record; Cognito Post Confirmation also provisions Profile + Customer in `provisioned` status; no business workflow.
- Dev register operations document `404` when `REGISTRATION_DEV_MODE` is not enabled, and that responses are documents/ids — never a JWT.
- Tags: `Profile`, `Event`, `ExternalEvent`, `Setting`, `Customer`, `Webhooks`, `Dev`, plus existing Config / Metrics.
- The document remains valid OpenAPI 3.0.x.

## Testing Expectations

Run all commands from this API repository root.

- **Schema fetch** — all five configurator curls succeed; record schema versions in **Execution Notes**.
- **Spec validation**
  - `python3 -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - Confirm every path in the tables above, array list responses, `offset`/`size` headers, no Profile PATCH, no Customer POST/PATCH, no credential-minting paths.
  - Confirm no `after_id`, `has_more`, or `next_cursor`.
- **Unit / lint / build** (must still pass after a docs-only change)
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — served file includes the new paths

## Outputs

- `docs/openapi.yaml` — full Admin contract from the endpoint map; configurator-grounded component schemas; keep Config / Metrics / bearerAuth / Error

The agent must not update files outside this list.

## Execution Notes
