# F015 – Setting control service and routes

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F014_ingress_event_layer`  
**Description:** Admin **controls** Setting. There is no shared `SettingService` in api-utils 1.0.0. Add a local service and GET list (optional `type` filter), GET/PATCH by id, and POST create. All inbound writes and operator reads require `ROLE_ADMIN`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — Create / Retrieve / Patch; RBAC at the service layer; routes HTTP-only
- `tasks/_PLANNING.md` — MongoIO only; fetch Setting schema from configurator
- `README.md`
- `../mentorhub_api_utils/README.md` — list GET JSON array; `offset`/`size` headers; `parse_list_request` / `execute_list_query`
- `../mentorhub_api_utils/api_utils/config/config.py` — `SETTING_COLLECTION_NAME` (`Setting`); Product and Discount are `type` variants on Setting, not separate collections
- `../mentorhub_api_utils/api_utils/mongo_utils/list_query.py`
- `../mentorhub_api_utils/api_utils/flask_utils/list_request.py` — `parse_list_request`
- `../mentorhub_api_utils/api_utils/services/rbac.py` — `is_admin`, `build_outbound_match`, `require_outbound`
- `docs/openapi.yaml` — Setting paths and schema from F011
- `src/server.py` — register the new blueprint beside Profile / Event / ExternalEvent
- `src/routes/profile_routes.py` — POST-on-factory pattern to copy for a fully local blueprint (no shared Setting GET factory)

Fetch the live schema:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Setting.yaml/latest/" -H "accept: application/json"
```

If the configurator is unavailable, set **Status** to `Blocked` and stop.

**MongoDB I/O:** MongoIO only. Encode string ids with `encode_document` immediately before MongoIO. Do not stringify ObjectIds for output.

There is **no** `create_setting_get_routes` in api-utils. Build a local blueprint. Do not add a Setting class to api-utils from this repo.

## Goals

- `src/services/setting_service.py` — local `SettingService` (`classmethod`):
  - `_check_permission` requires `is_admin(token)` for create, read, and update.
  - `get_settings(token, breadcrumb, offset, size, filters, sort_by)` — `execute_list_query` on `config.SETTING_COLLECTION_NAME`; `type` filter (`in_list` or exact, matching OpenAPI).
  - `get_setting(setting_id, token, breadcrumb)` — `get_document`; hidden/missing → `HTTPNotFound` (do not leak ids via 403).
  - `create_setting(data, token, breadcrumb)` — strip system-managed fields; set `created` / `saved` breadcrumbs if the live schema has them; `create_document`.
  - `update_setting(setting_id, data, token, breadcrumb)` — PATCH; do not overwrite `_id` or `created`; set `saved` if the schema has it; `update_document`.
- Filter/order specs (`SETTING_LIST_FILTERS`, `SETTING_LIST_ORDER`) live next to the service, same pattern as Profile/Event.
- `src/routes/setting_routes.py` — `GET ""`, `POST ""`, `GET /<setting_id>`, `PATCH /<setting_id>`. Token + breadcrumb in the route; service does RBAC and Mongo I/O. List uses `parse_list_request`. POST `201`, PATCH `200`.
- `src/server.py` registers `/api/setting` and logs it.
- `test/test_server.py` asserts `/api/setting` is present.
- Unit tests mock MongoIO: admin-only, type filter, create/patch breadcrumbs, 404 on missing id.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_setting_service.py`
  - `test/routes/test_setting_routes.py`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — includes `/api/setting`

## Outputs

- `src/services/setting_service.py`
- `src/routes/setting_routes.py`
- `src/server.py` — register Setting blueprint
- `test/test_server.py`
- `test/services/test_setting_service.py`
- `test/routes/test_setting_routes.py`

The agent must not update files outside this list.

## Execution Notes
