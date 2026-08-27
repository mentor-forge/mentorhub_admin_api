"""
Black-box E2E integration tests for Admin provider ingress & dev registration.
Requires running containerized API (http://localhost:8389).
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8389")


@pytest.mark.e2e
def test_e2e_stripe_webhook_ingress():
    """Verify Stripe webhook ingress records external event and handles duplicates idempotently."""
    event_id = f"evt_e2e_{uuid.uuid4().hex[:12]}"
    payload = {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_123",
                "customer": "cus_123",
                "metadata": {"customer_id": "507f1f77bcf86cd799439011"},
            }
        },
    }

    # First call -> received: True, idempotent: False
    res1 = requests.post(f"{BASE_URL}/webhooks/stripe", json=payload, timeout=5)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1.get("received") is True
    assert data1.get("idempotent") is False

    # Second duplicate call -> received: True, idempotent: True
    res2 = requests.post(f"{BASE_URL}/webhooks/stripe", json=payload, timeout=5)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("received") is True
    assert data2.get("idempotent") is True


@pytest.mark.e2e
def test_e2e_cognito_webhook_post_confirmation():
    """Verify Cognito PostConfirmation webhook provisions Customer & Profile."""
    unique_email = f"cognito_e2e_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "triggerSource": "PostConfirmation_ConfirmSignUp",
        "userName": f"user_{uuid.uuid4().hex[:8]}",
        "request": {
            "userAttributes": {
                "email": unique_email,
                "name": "Cognito Owner",
                "sub": str(uuid.uuid4()),
            },
            "clientMetadata": {
                "organization_name": "Cognito E2E Org",
            },
        },
    }

    res = requests.post(f"{BASE_URL}/webhooks/cognito", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("received") is True
    assert data.get("provisioned") is True


@pytest.mark.e2e
def test_e2e_sms_webhook():
    """Verify SMS webhook endpoint logs and responds successfully."""
    msg_id = f"sms_{uuid.uuid4().hex[:8]}"
    payload = {
        "message_id": msg_id,
        "from": "+15551234567",
        "body": "E2E SMS TEST",
    }
    res = requests.post(f"{BASE_URL}/webhooks/sms", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("received") is True


@pytest.mark.e2e
def test_e2e_dev_registration_endpoints():
    """Verify Dev registration endpoints provision identities without minting JWTs."""
    unique_email = f"dev_owner_{uuid.uuid4().hex[:8]}@example.com"
    primary_payload = {
        "email": unique_email,
        "name": "Dev Owner",
        "organization_name": "Dev Test Org",
    }
    res = requests.post(
        f"{BASE_URL}/dev/register/primary", json=primary_payload, timeout=5
    )
    assert res.status_code == 201
    primary_data = res.json()
    assert "profile" in primary_data
    assert "customer" in primary_data
    assert primary_data["profile"]["email"] == unique_email
    assert "token" not in primary_data
    assert "jwt" not in primary_data

    customer_id = primary_data["customer"]["_id"]

    # Invitee registration under created customer
    invitee_email = f"dev_invitee_{uuid.uuid4().hex[:8]}@example.com"
    invitee_payload = {
        "email": invitee_email,
        "name": "Dev Invitee",
        "customer_id": customer_id,
    }
    res_inv = requests.post(
        f"{BASE_URL}/dev/register/invite", json=invitee_payload, timeout=5
    )
    assert res_inv.status_code == 201
    invite_data = res_inv.json()
    assert "profile" in invite_data
    assert invite_data["profile"]["email"] == invitee_email
    assert invite_data["profile"]["customer_id"] == customer_id
    assert "token" not in invite_data


@pytest.mark.e2e
def test_e2e_forbidden_and_non_existent_paths():
    """Verify /api/webhooks, /api/dev, /api/profile, /api/customer are 404."""
    assert requests.get(f"{BASE_URL}/api/webhooks", timeout=5).status_code == 404
    assert requests.get(f"{BASE_URL}/api/dev", timeout=5).status_code == 404
    assert requests.get(f"{BASE_URL}/api/profile", timeout=5).status_code == 404
    assert requests.get(f"{BASE_URL}/api/customer", timeout=5).status_code == 404
