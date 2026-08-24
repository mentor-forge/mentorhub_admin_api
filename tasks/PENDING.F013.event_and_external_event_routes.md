# F013 – Event and ExternalEvent list routes

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F012_shared_service_subclasses`  
**Description:** Mount Event GET list + POST, and Admin ExternalEvent **list only** (source filter). No Profile or Customer routes. No ExternalEvent POST or get-by-id. Register blueprints from `server.py`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; OpenAPI is the SPA contract; Admin **controls** ExternalEvent and Setting
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — routes are HTTP-only (token, breadcrumb, exceptions, payload pass-through); no payload mutation in routes
- `tasks/_PLANNING.md`
- `README.md`
- `../mentorhub_api_utils/README.md` — `create_*_get_routes(service_cls)` then add POST on the returned blueprint; list GET body is a JSON array; `offset`/`size` headers only
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — `create_event_get_routes` (list only). Do **not** use `create_profile_get_routes` or `create_external_event_get_routes` (by-id only; this API has no ExternalEvent by-id)
- `src/services/event_service.py`
- `src/services/external_event_service.py`
- `src/server.py` — currently config / metrics / explorer only
- `docs/openapi.yaml` — F011 paths for Event and ExternalEvent list
- `test/test_server.py` — currently asserts `/api/event` is **absent**; update that once registered
- `../mentorhub_api_utils/api_utils/mongo_utils/list_query.py` — `execute_list_query` for the Admin ExternalEvent list

Routes import **local** subclasses, never `api_utils.services` directly.

**ExternalEvent list:** the shared factory is get-by-id only and must **not** be mounted. Admin **controls** ExternalEvent, so build a local blueprint with `GET ""` only: `offset`/`size` headers, optional `source` query filter, JSON array. Implement list on the local `ExternalEventService` (MongoIO / `execute_list_query`) with outbound match from the shared `_outbound_match` (admin unrestricted). Do not invent cursor pagination. Do not add POST or `GET /<event_id>`.

## Goals

- `src/routes/event_routes.py` — `bp = create_event_get_routes(EventService)` then `POST ""` → `EventService.create_event`; `201`.
- `src/routes/external_event_routes.py` — local list-only blueprint; `GET ""` with `source` filter. No POST. No by-id.
- Event POST uses `create_flask_token()`, `create_flask_breadcrumb(token)`, `request.get_json() or {}`, `@handle_route_exceptions`. Do not validate or alter payloads in the route.
- `src/server.py` registers `/api/event` and `/api/external-event` and logs those prefixes. Keep explorer, config, metrics. Do **not** register `/api/profile` or `/api/customer`.
- `test/test_server.py` asserts the new URL rules exist; `/api/profile`, `/api/customer`, ExternalEvent by-id, and ExternalEvent POST are absent; still forbids credential-minting routes and journey paths (`/api/journey`, `/api/note`, …).
- Route unit tests (Flask test client + mocked services) cover Event POST 201, non-admin 403 from the service, ExternalEvent list query `source`, ExternalEvent POST/by-id 404 (not registered).
- Add `test/e2e/e2e_auth.py` modeled on the Discovery helper: HS256 persona JWT with `iss`/`aud`/`sub`/`roles: ["admin"]` **and** `profile_id` (api-utils 1.0.0 rejects tokens without it). Do not register an HTTP path that mints tokens.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/routes/test_event_routes.py`
  - `test/routes/test_external_event_routes.py`
  - `test/test_server.py` — Event and ExternalEvent list present; no Profile/Customer; no ExternalEvent POST or by-id; no credential issuer
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — includes `/api/event` and `/api/external-event`; omits `/api/profile` and `/api/customer`

## Outputs

- `src/routes/event_routes.py`
- `src/routes/external_event_routes.py`
- `src/routes/__init__.py` — only if exports are needed
- `src/services/external_event_service.py` — add list method used by `GET /api/external-event`
- `src/server.py` — register Event and ExternalEvent list blueprints
- `test/test_server.py`
- `test/routes/test_event_routes.py`
- `test/routes/test_external_event_routes.py`
- `test/services/test_external_event_service.py` — list + source filter
- `test/e2e/e2e_auth.py`

The agent must not update files outside this list.

## Execution Notes
