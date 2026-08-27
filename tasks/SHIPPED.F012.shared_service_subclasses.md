# F012 – Profile, Event, and ExternalEvent service subclasses

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F011_openapi_admin_surface`  
**Description:** Add thin local subclasses so later routes and ingress never import shared service classes directly. Override inbound `_check_permission` so create requires `ROLE_ADMIN`. Profile create is **service-only** (no HTTP). No HTTP routes in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer; services aligned to one collection
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; outbound GET RBAC stays on the shared class; inbound write checks on the subclass
- `../mentorhub_api_utils/api_utils/services/profile_service.py` — shared `create_profile` has no write check; Admin subclass supplies it. Do not PATCH Profile (Customer **controls** Profile)
- `../mentorhub_api_utils/api_utils/services/external_event_service.py` — `create_external_event` (append-only), `get_external_event`; outbound GET is admin-only (`EMPTY_SCOPE_MATCH` for non-admin)
- `../mentorhub_api_utils/api_utils/services/event_service.py` — `create_event`, `get_events`; shared create copies `context` from the token (ingress override lands in F014)
- `../mentorhub_api_utils/api_utils/services/rbac.py` — `is_admin`
- `docs/openapi.yaml` — Event / ExternalEvent shapes from F011 (Profile is not in the SPA spec; subclass still required for ingress create)

**MongoDB I/O:** Use `MongoIO` or inherited shared methods. Do not call PyMongo via `mongo.get_collection(...)`. Do not stringify ObjectIds for output.

This API is operators-only for these creates: prefer `ROLE_ADMIN` on Profile, ExternalEvent, and Event create. Profile and ExternalEvent creates are called from ingress services, not from `/api` POST routes.

## Goals

- Add `src/services/__init__.py` if missing.
- Thin local subclasses (`classmethod`, inherit shared consume/create):

```python
from api_utils.services import ProfileService as SharedProfileService
from api_utils.services import ExternalEventService as SharedExternalEventService
from api_utils.services import EventService as SharedEventService

class ProfileService(SharedProfileService):
    """Ingress may create Profile (shared create_profile). No Profile HTTP or PATCH here."""

class ExternalEventService(SharedExternalEventService):
    """Ingress append-only create; Admin-only inbound create. List HTTP lands in F013."""

class EventService(SharedEventService):
    """Admin-only inbound create for operator POST /api/event and ingress."""
```

- Override `_check_permission` on **each** subclass so operations that write (`create`, and `read` if the shared method calls it on get) require `is_admin(token)`. Raise `HTTPForbidden` otherwise. Shared Profile/Event/ExternalEvent create has no write check — these subclasses supply it.
- Do **not** add `update_profile` / PATCH. Do **not** add ExternalEvent update/delete (append-only).
- Do **not** implement ingress normalize / payload hash / idempotency here (F014).
- Unit tests mock MongoIO / shared methods; they do not require a live database.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_profile_service.py` — `create_profile` allowed for admin; `HTTPForbidden` without `ROLE_ADMIN`; no PATCH method on the subclass
  - `test/services/test_external_event_service.py` — `create_external_event` admin-only
  - `test/services/test_event_service.py` — `create_event` admin-only
- **Packaging verification** (no new HTTP yet)
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — still served

## Outputs

- `src/services/__init__.py`
- `src/services/profile_service.py`
- `src/services/external_event_service.py`
- `src/services/event_service.py`
- `test/services/test_profile_service.py`
- `test/services/test_external_event_service.py`
- `test/services/test_event_service.py`

The agent must not update files outside this list.

## Execution Notes

1. **Service Subclasses Implementation:**
   - Created `src/services/__init__.py` exporting `ProfileService`, `ExternalEventService`, `EventService`.
   - Implemented `ProfileService`, `ExternalEventService`, and `EventService` subclasses inheriting from `api_utils.services`.
   - Overrode `_check_permission` on each subclass enforcing `ROLE_ADMIN` (`is_admin(token)`).
   - Ensured `ProfileService` does not implement `update_profile` / PATCH.
2. **Unit Tests:**
   - Created `test/services/test_profile_service.py`, `test/services/test_external_event_service.py`, `test/services/test_event_service.py`.
   - Verified `ROLE_ADMIN` authorization, forbidden non-admin rejection, and absence of PATCH on ProfileService.
3. **Verification & Packaging:**
   - `pipenv run test`: All 20 unit tests passed.
   - `pipenv run lint`: Black formatting clean.
   - `pipenv run build`: Compilation clean.
   - `pipenv run container`: Docker image built.
   - `pipenv run api`: API container restarted and verified with `curl -s http://localhost:8389/docs/openapi.yaml`.
