"""
Black-box E2E integration tests for Admin operator REST endpoints.
Requires running containerized API (http://localhost:8389).
"""

import os
import pytest
import requests
from test.e2e.e2e_auth import get_auth_token

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8389")


@pytest.mark.e2e
def test_e2e_get_config():
    """Verify /api/config endpoint with Bearer token."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/api/config", headers=headers, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)


@pytest.mark.e2e
def test_e2e_operator_setting_crud():
    """Verify operator Setting CRUD with admin Bearer token conforming to Setting schema."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List settings
    res = requests.get(f"{BASE_URL}/api/setting", headers=headers, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

    # 2. Create Product setting
    create_payload = {
        "type": "Product",
        "name": "E2E Starter Plan",
        "description": "E2E test plan offering",
        "subscription": "e2e_starter",
        "unit_price": 4900,
        "status": "active",
    }
    res = requests.post(
        f"{BASE_URL}/api/setting",
        json=create_payload,
        headers=headers,
        timeout=5,
    )
    assert res.status_code == 201
    created_setting = res.json()
    assert "_id" in created_setting
    setting_id = created_setting["_id"]

    # 3. Get setting by ID
    res = requests.get(
        f"{BASE_URL}/api/setting/{setting_id}", headers=headers, timeout=5
    )
    assert res.status_code == 200
    fetched_setting = res.json()
    assert fetched_setting["_id"] == setting_id

    # 4. Patch setting
    patch_payload = {"description": "Updated E2E description"}
    res = requests.patch(
        f"{BASE_URL}/api/setting/{setting_id}",
        json=patch_payload,
        headers=headers,
        timeout=5,
    )
    assert res.status_code == 200
    patched_setting = res.json()
    assert patched_setting["description"] == "Updated E2E description"


@pytest.mark.e2e
def test_e2e_operator_event_routes():
    """Verify operator Event list and create with admin Bearer token conforming to Event schema."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create event
    event_payload = {
        "type": "identity_provisioned",
    }
    res = requests.post(
        f"{BASE_URL}/api/event", json=event_payload, headers=headers, timeout=5
    )
    assert res.status_code == 201
    created_event = res.json()
    assert "_id" in created_event

    # 2. List events
    res = requests.get(f"{BASE_URL}/api/event", headers=headers, timeout=5)
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert any(e.get("_id") == created_event["_id"] for e in events)


@pytest.mark.e2e
def test_e2e_operator_external_event_list():
    """Verify operator ExternalEvent list (read-only audit)."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(f"{BASE_URL}/api/external-event", headers=headers, timeout=5)
    assert res.status_code == 200
    external_events = res.json()
    assert isinstance(external_events, list)

    # Test source filter
    res_filtered = requests.get(
        f"{BASE_URL}/api/external-event?source=stripe",
        headers=headers,
        timeout=5,
    )
    assert res_filtered.status_code == 200
    filtered_events = res_filtered.json()
    assert isinstance(filtered_events, list)


@pytest.mark.e2e
def test_e2e_operator_unauthorized():
    """Verify operator endpoints return 401 without Bearer token."""
    res = requests.get(f"{BASE_URL}/api/setting", timeout=5)
    assert res.status_code == 401

    res = requests.get(f"{BASE_URL}/api/event", timeout=5)
    assert res.status_code == 401

    res = requests.get(f"{BASE_URL}/api/external-event", timeout=5)
    assert res.status_code == 401
