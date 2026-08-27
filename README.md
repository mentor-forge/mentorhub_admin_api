# Mentor Hub — Admin API

## Current State
Guidance for LLM Code Assistants - NOTE: We are currently pre-release. At this time, no changes should consider backward compatibility. Likewise, while we anticipate versioning releases in the future at this point, no consideration should be given to bumping any versions beyond managing the internal api_utils spa_utils dependencies. We are in a rapid iteration phase where features can be deprecated and removed without pause. When working in this repo we should keep our eyes out for potential re-usable code that could be migrated to api_utils. This code should be implemented locally, and issues opened in the api_utils repo when it is time to migrate code.

Platform shell only (`/api/config`, `/docs`, `/metrics`). Pinned to `api-utils==1.0.0` (JSON-array list GETs, `offset`/`size` request headers, no cursor envelope). Admin domain routes (Setting control, Event/ExternalEvent list, Stripe and Cognito ingress, etc.) will be added in follow-on tasks.

## Prerequisites
- Mentor Hub [Developers Edition](https://github.com/mentor-forge/mentorhub/blob/main/CONTRIBUTING.md)
- Developer [API Standard Prerequisites](https://github.com/mentor-forge/mentorhub/blob/main/DeveloperEdition/standards/api_standards.md)

## Developer Commands

```bash
## Install dependencies (run `mh` first for CodeArtifact auth)
pipenv run install

# start backing db container
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8389
pipenv run dev

## run E2E tests (assumes running API at localhost:8389)
pipenv run e2e

## run tests with coverage report
pipenv run coverage

## build application (pre-compiles Python code)
pipenv run build

## build container
pipenv run container

## Run the backing database and api containers
pipenv run api

## Run the full microservice (db+api+spa)
pipenv run service

## format code
pipenv run format

## lint code
pipenv run lint
```

## Project Structure

- `src/` - Main package containing:
  - `server.py` - API entrypoint
  - `routes/` - HTTP request/response handlers (empty shell; domain routes added later)

- `test/` - Test suite:
  - `test_server.py` - Server initialization and route registration tests

## API Endpoints

See the [Open API Specifications](./docs/openapi.yaml) for details on the API.

### Simple Curl Commands:
```bash
# Get the API Configuration (requires Bearer token from Developer Edition IdP)
curl http://localhost:8389/api/config \
  -H "Authorization: Bearer $TOKEN"

```
