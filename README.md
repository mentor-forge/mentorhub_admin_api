# Mentor Hub — Admin API

## Current State
Guidance for LLM Code Assistants - NOTE: We are currently pre-release. At this time, no changes should consider backward compatibility. Likewise, while we anticipate versioning releases in the future at this point, no consideration should be given to bumping any versions beyond managing the internal api_utils spa_utils dependencies. We are in a rapid iteration phase where features can be deprecated and removed without pause. When working in this repo we should keep our eyes out for potential re-usable code that could be migrated to api_utils. This code should be implemented locally, and issues opened in the api_utils repo when it is time to migrate code.

The Admin API microservice serves two distinct roles:
1. **Admin SPA Operator BFF (`/api/*`)**: Controlled CRUD for system Settings (`/api/setting`), Event publishing and querying (`/api/event`), and read-only audit log queries for external events (`/api/external-event`). Enforces `ROLE_ADMIN` RBAC and adheres to the OpenAPI 3.0.3 specification (`docs/openapi.yaml`). Pinned to `api-utils==1.0.3` (JSON-array list GETs, `offset`/`size` headers, no cursor envelope). Flask token dicts from `create_flask_token()` use `display_name` (not `name`) for the human-readable identity.
2. **Provider & Process Ingress Listeners (`/webhooks/*`, `/dev/register/*`)**: Transport listeners mounted on the server process (excluded from SPA OpenAPI docs). Normalizes and records incoming Stripe, Cognito, and SMS events via `IngressService`, and coordinates initial account provisioning (Customer organization and owner Profile) via `IdentityProvisioningService`. Does not enrich Customers or mint JWTs directly.

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
  - `server.py` - Flask server entrypoint, lifecycle hooks, and blueprint registrations
  - `routes/` - HTTP request and response routes:
    - `setting_routes.py` - CRUD routes for system Settings (`/api/setting`)
    - `event_routes.py` - List and create routes for system Events (`/api/event`)
    - `external_event_routes.py` - List route for external event audit trail (`/api/external-event`)
    - `webhook_routes.py` - Ingress listeners for Stripe, Cognito, and SMS (`/webhooks/*`)
    - `dev_register_routes.py` - Developer Edition parity self-serve registration endpoints (`/dev/register/*`)
  - `services/` - Business logic and data access services:
    - `setting_service.py` - Admin-controlled CRUD for polymorphic Product and Discount Settings
    - `event_service.py` - Admin-controlled Event creation with context references
    - `external_event_service.py` - Read-only ExternalEvent list and lookup
    - `ingress_service.py` - Payload hashing, normalization, and deduplication
    - `customer_service.py` - Read queries and creation of provisioned Customer shells
    - `profile_service.py` - Read queries and creation of Profile records
    - `identity_provisioning_service.py` - Primary and invitee account provisioning orchestration
    - `webhook_transport.py` - Signature and secret verification for webhook listeners
    - `webhook_handlers.py` - Provider-specific event mapping and dispatching

- `docs/`
  - `openapi.yaml` - OpenAPI 3.0.3 specification for the Admin SPA REST surface

- `test/` - Test suite:
  - `test_server.py` - Server initialization, route registration, and signal handling tests
  - `routes/` - Unit tests for all REST, webhook, and dev registration routes
  - `services/` - Unit tests for all domain and provisioning services
  - `e2e/` - Black-box end-to-end integration tests (`test_operator_rest.py`, `test_webhooks.py`, `e2e_auth.py`)

## API Endpoints

See the [OpenAPI Specification](./docs/openapi.yaml) for full schema and parameter details of operator endpoints.

### Operator REST Surface (Bearer Auth Required)

```bash
# 1. Get API Configuration
curl -s http://localhost:8389/api/config \
  -H "Authorization: Bearer $TOKEN"

# 2. List Settings (optional type, name, status filters)
curl -s "http://localhost:8389/api/setting?type=Product&status=active" \
  -H "Authorization: Bearer $TOKEN"

# 3. Create a Product Setting
curl -s -X POST http://localhost:8389/api/setting \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Product",
    "name": "Standard Mentorship Plan",
    "description": "Monthly subscription offering",
    "subscription": "standard_plan",
    "unit_price": 4900,
    "status": "active"
  }'

# 4. Get Setting by ID
curl -s http://localhost:8389/api/setting/$SETTING_ID \
  -H "Authorization: Bearer $TOKEN"

# 5. Patch Setting
curl -s -X PATCH http://localhost:8389/api/setting/$SETTING_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated plan description"}'

# 6. List Events
curl -s "http://localhost:8389/api/event" \
  -H "Authorization: Bearer $TOKEN"

# 7. Create Event
curl -s -X POST http://localhost:8389/api/event \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "identity_provisioned"}'

# 8. List External Events Audit (optional source filter)
curl -s "http://localhost:8389/api/external-event?source=stripe" \
  -H "Authorization: Bearer $TOKEN"
```

### Provider Ingress & Dev Registration Surface (No Bearer Auth)

```bash
# 1. Stripe Webhook Ingress (signature verified when STRIPE_WEBHOOK_VERIFY=true)
curl -s -X POST http://localhost:8389/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: t=$TIMESTAMP,v1=$SIGNATURE" \
  -d '{"id": "evt_123", "type": "payment_intent.succeeded"}'

# 2. Cognito Post Confirmation Webhook (shared secret verified when COGNITO_WEBHOOK_SECRET is set)
curl -s -X POST http://localhost:8389/webhooks/cognito \
  -H "Content-Type: application/json" \
  -H "X-Cognito-Secret: $COGNITO_WEBHOOK_SECRET" \
  -d '{
    "triggerSource": "PostConfirmation_ConfirmSignUp",
    "request": {
      "userAttributes": {"email": "user@example.com", "name": "Jane Doe", "sub": "cognito-sub-123"},
      "clientMetadata": {"organization_name": "Acme Corp"}
    }
  }'

# 3. Dev Parity Organization Registration (Developer Edition login.html parity)
curl -s -X POST http://localhost:8389/dev/register/primary \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@example.com",
    "name": "Owner Name",
    "organization_name": "Acme Corp"
  }'

# 4. Dev Parity Invitee Registration
curl -s -X POST http://localhost:8389/dev/register/invite \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@example.com",
    "name": "Member Name",
    "customer_id": "$CUSTOMER_ID"
  }'
```
