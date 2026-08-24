# F013 – Profile, Event, and ExternalEvent routes

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F012_shared_service_subclasses`  
**Description:** Mount shared GET factories with local subclasses, add control POST on each blueprint, and add Admin-only ExternalEvent list (source filter). Register blueprints from `server.py`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — routes are HTTP-only (token, breadcrumb, exceptions, payload pass-through); no payload mutation in routes
- `tasks/_PLANNING.md`
- `README.md`
- `../mentorhub_api_utils/README.md` — `create_*_get_routes(service_cls)` then add POST on the returned blueprint; list GET body is a JSON array; `offset`/`size` headers only
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — `create_profile_get_routes`, `create_event_get_routes` (list only), `create_external_event_get_routes` (by-id only)
- `src/services/profile_service.py`
- `src/services/event_service.py`
- `src/services/external_event_service.py`
- `src/server.py` — currently config / metrics / explorer only
- `docs/openapi.yaml` — F011 paths for Profile, Event, ExternalEvent
- `test/test_server.py` — currently asserts `/api/event` is **absent**; update that once registered
- `../mentorhub_api_utils/api_utils/mongo_utils/list_query.py` — `execute_list_query` for the Admin ExternalEvent list

Routes import **local** subclasses, never `api_utils.services` directly.

**ExternalEvent list:** the shared factory is get-by-id only. Admin **controls** ExternalEvent, so add `GET ""` on the same blueprint: `offset`/`size` headers, optional `source` query filter, JSON array. Implement list on the local `ExternalEventService` (MongoIO / `execute_list_query`) with outbound match from the shared `_outbound_match` (admin unrestricted). Do not invent cursor pagination.

## Goals

- `src/routes/profile_routes.py` — `bp = create_profile_get_routes(ProfileService)` then `POST ""` → `ProfileService.create_profile`; `201` with the document. No PATCH.
- `src/routes/event_routes.py` — `bp = create_event_get_routes(EventService)` then `POST ""` → `EventService.create_event`; `201`.
- `src/routes/external_event_routes.py` — `bp = create_external_event_get_routes(ExternalEventService)` then `POST ""` → `create_external_event` (`201`) and `GET ""` list with `source` filter.
- Each POST uses `create_flask_token()`, `create_flask_breadcrumb(token)`, `request.get_json() or {}`, `@handle_route_exceptions`. Do not validate or alter payloads in the route.
- `src/server.py` registers:
  - `/api/profile`
  - `/api/event`
  - `/api/external-event`
  and logs those prefixes. Keep explorer, config, metrics.
- `test/test_server.py` asserts the new URL rules exist and still forbids credential-minting routes and journey paths (`/api/journey`, `/api/note`, …).
- Route unit tests (Flask test client + mocked services) cover admin POST 201, non-admin 403 from the service, Profile PATCH 405/404 (not registered), ExternalEvent list query `source`.
- Add `test/e2e/e2e_auth.py` modeled on the Discovery helper: HS256 persona JWT with `iss`/`aud`/`sub`/`roles: ["admin"]` **and** `profile_id` (api-utils 1.0.0 rejects tokens without it). Do not register an HTTP path that mints tokens.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/routes/test_profile_routes.py`
  - `test/routes/test_event_routes.py`
  - `test/routes/test_external_event_routes.py`
  - `test/test_server.py` — new prefixes present; no credential issuer; no Profile PATCH rule
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — still includes `/api/profile`, `/api/event`, `/api/external-event`

## Outputs

- `src/routes/profile_routes.py`
- `src/routes/event_routes.py`
- `src/routes/external_event_routes.py`
- `src/routes/__init__.py` — only if exports are needed
- `src/services/external_event_service.py` — add list method used by `GET /api/external-event`
- `src/server.py` — register the three blueprints
- `test/test_server.py`
- `test/routes/test_profile_routes.py`
- `test/routes/test_event_routes.py`
- `test/routes/test_external_event_routes.py`
- `test/services/test_external_event_service.py` — list + source filter
- `test/e2e/e2e_auth.py`

The agent must not update files outside this list.

## Execution Notes
