# F010 – Pin api-utils 1.0.0

**Status:** Shipped  
**Type:** Feature  
**Depends On:** none  
**Description:** This repo owns the 1.0.0 wave pin. Bump `api-utils` from `0.5.2` to `1.0.0` and keep the platform shell (config, metrics, explorer) importing cleanly. No domain routes or services in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; Admin **controls** ExternalEvent and Setting, **creates** Event and Profile, **consumes** Profile and Customer
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `README.md`
- `../mentorhub_api_utils/README.md` — pin `api-utils==1.0.0`; list GET is a JSON array; pagination is request headers `offset` / `size`; routes import local subclasses, never `api_utils.services` directly
- `Pipfile` — currently `api-utils==0.5.2`
- `Pipfile.lock`
- `src/server.py` — registers explorer, config, and metrics only
- `test/test_server.py`
- `../mentorhub/Workshops/admin_journey_issues.md` — Admin is ingress + operators; no domain workflows beyond provisioning

**External prerequisite:** `api-utils==1.0.0` must resolve from the CodeArtifact index. If `pipenv run install` cannot resolve 1.0.0, set **Status** to `Blocked` and stop.

This Admin API is already a stub (no `src/services/` modules, no domain blueprints). Do **not** add domain routes here. Later tasks add thin subclasses and factories against 1.0.0.

**MongoDB I/O:** Any future service code must use `MongoIO` (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`). Do not call PyMongo through `mongo.get_collection(...)`. This task should not add service code.

## Goals

- `Pipfile` and `Pipfile.lock` pin `api-utils==1.0.0` (single CodeArtifact `[[source]]` unchanged; keep the comment that public PyPI `api-utils` is unrelated).
- Dependencies are installed with `pipenv run install` (run `mh` first if CodeArtifact credentials are missing). Do **not** use bare `pipenv install`.
- `src/server.py` still registers only `/docs`, `/api/config`, and `/metrics`.
- `test/test_server.py` still asserts the platform shell and that credential-minting routes and journey-domain paths are absent.
- `README.md` states the pinned `api-utils==1.0.0` contract (JSON-array list GETs, `offset`/`size` headers, no cursor envelope) and that domain routes land in follow-up tasks.

## Testing Expectations

Run all commands from this API repository root.

- **Install**
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `pipenv run install`
- **Unit / lint / build**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8389/docs/openapi.yaml` — served; still only documents `/api/config` and `/metrics`

## Outputs

- `Pipfile` — pin `api-utils==1.0.0`
- `Pipfile.lock` — refresh via `pipenv run install` (use `scripts/pipenv-lock.sh` if the lock hashes must be regenerated first)
- `README.md` — note the 1.0.0 pin and that domain routes follow

The agent must not update files outside this list.

## Execution Notes

1. **Plan & Dependency Bump:**
   - Updated `Pipfile` to specify `api-utils = {version = "==1.0.0", index = "codeartifact"}`.
   - Ran `sh scripts/pipenv-lock.sh` to refresh `Pipfile.lock` against AWS CodeArtifact.
   - Installed dependencies with `pipenv run install` (installed `api-utils-1.0.0`).
   - Updated `README.md` to describe the pinned `api-utils==1.0.0` contract.
2. **Testing & Packaging Verification:**
   - `pipenv run test`: All 13 unit tests passed.
   - `pipenv run lint`: Black check clean.
   - `pipenv run build`: Python compilation clean.
   - `pipenv run container`: Docker image `ghcr.io/mentor-forge/mentorhub_admin_api:latest` built successfully.
   - `pipenv run api`: Containers started and verified healthy.
   - `curl -s http://localhost:8389/docs/openapi.yaml`: Responded 200 OK with platform shell OpenAPI.
   - `curl -s http://localhost:8389/metrics`: Responded with Prometheus metrics.
