"""
Unit tests for Webhook transport routes in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch
from flask import Flask
from bson import ObjectId
from api_utils import MongoJSONEncoder
from src.routes.webhook_routes import create_webhook_routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.json = MongoJSONEncoder(app)
    app.register_blueprint(create_webhook_routes(), url_prefix="/webhooks")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# --- Stripe Webhook Tests ---


@patch("src.routes.webhook_routes.handle_stripe")
def test_stripe_webhook_success(mock_handle, client):
    mock_handle.return_value = {
        "external_event": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "event": {"_id": ObjectId("507f1f77bcf86cd799439012")},
        "idempotent": False,
    }

    payload = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
    }
    response = client.post("/webhooks/stripe", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["received"] is True
    assert data["idempotent"] is False
    mock_handle.assert_called_once()


def test_stripe_webhook_invalid_secret(monkeypatch, client):
    monkeypatch.setenv("STRIPE_WEBHOOK_VERIFY", "true")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_secret")
    response = client.post(
        "/webhooks/stripe",
        json={"id": "evt_1"},
        headers={"Stripe-Signature": "t=1000,v1=invalid_sig"},
    )
    assert response.status_code == 401


# --- Cognito Webhook Tests ---


@patch("src.routes.webhook_routes.handle_cognito")
def test_cognito_webhook_post_confirmation_primary(mock_handle, client):
    mock_handle.return_value = {
        "profile": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "customer": {"_id": ObjectId("507f1f77bcf86cd799439012")},
        "idempotent": False,
    }

    payload = {
        "triggerSource": "PostConfirmation_ConfirmSignUp",
        "userName": "cognito_user_1",
        "request": {
            "userAttributes": {"email": "owner@example.com", "name": "Owner Name"},
            "clientMetadata": {"organization_name": "Owner Org"},
        },
    }
    response = client.post("/webhooks/cognito", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["received"] is True
    assert data["provisioned"] is True
    mock_handle.assert_called_once()


@patch("src.routes.webhook_routes.handle_cognito")
def test_cognito_webhook_post_confirmation_invitee(mock_handle, client):
    mock_handle.return_value = {
        "profile": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "customer": {"_id": ObjectId("507f1f77bcf86cd799439012")},
        "idempotent": False,
    }

    payload = {
        "triggerSource": "PostConfirmation_ConfirmSignUp",
        "userName": "cognito_user_2",
        "request": {
            "userAttributes": {"email": "invitee@example.com", "name": "Invitee Name"},
            "clientMetadata": {"customer_id": "507f1f77bcf86cd799439012"},
        },
    }
    response = client.post("/webhooks/cognito", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["received"] is True
    assert data["provisioned"] is True
    mock_handle.assert_called_once()


@patch("src.routes.webhook_routes.handle_cognito")
def test_cognito_webhook_general_audit(mock_handle, client):
    mock_handle.return_value = {
        "external_event": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "event": {"_id": ObjectId("507f1f77bcf86cd799439012")},
        "idempotent": False,
    }

    payload = {
        "triggerSource": "CustomMessage_SignUp",
        "userName": "user_123",
        "request": {"userAttributes": {"email": "test@example.com"}},
    }
    response = client.post("/webhooks/cognito", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["received"] is True
    mock_handle.assert_called_once()


def test_cognito_webhook_invalid_secret(monkeypatch, client):
    monkeypatch.setenv("COGNITO_WEBHOOK_SECRET", "cognito_secret_123")
    response = client.post(
        "/webhooks/cognito",
        json={"trigger": "PostConfirmation"},
        headers={"X-Cognito-Secret": "wrong_secret"},
    )
    assert response.status_code == 401


# --- SMS Webhook Tests ---


@patch("src.routes.webhook_routes.handle_sms")
def test_sms_webhook_success(mock_handle, client):
    mock_handle.return_value = {
        "external_event": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "event": {"_id": ObjectId("507f1f77bcf86cd799439012")},
        "idempotent": False,
    }

    payload = {
        "message_id": "sms_msg_001",
        "from": "+15551234567",
        "body": "STOP",
    }
    response = client.post("/webhooks/sms", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["received"] is True
    mock_handle.assert_called_once()


def test_sms_webhook_invalid_secret(monkeypatch, client):
    monkeypatch.setenv("SMS_WEBHOOK_SECRET", "sms_secret_123")
    response = client.post(
        "/webhooks/sms",
        json={"message_id": "sms_1"},
        headers={"X-SMS-Secret": "wrong_secret"},
    )
    assert response.status_code == 401
