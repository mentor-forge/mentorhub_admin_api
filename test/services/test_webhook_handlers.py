"""
Unit tests for webhook event handlers.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPBadRequest
from src.services.webhook_handlers import handle_cognito, handle_sms, handle_stripe


@pytest.fixture
def system_token():
    return {
        "user_id": "webhook-ingress",
        "roles": ["admin"],
        "profile_id": "000000000000000000000000",
    }


@pytest.fixture
def breadcrumb():
    return {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "webhook-ingress",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }


@patch("src.services.webhook_handlers.IngressService.record_external_payload")
def test_handle_stripe(mock_record, system_token, breadcrumb):
    mock_record.return_value = {"external_event": {}, "event": {}}

    payload = {"id": "evt_123", "type": "payment_intent.succeeded"}
    result = handle_stripe(payload, system_token, breadcrumb)
    assert "external_event" in result
    mock_record.assert_called_once()


def test_handle_stripe_missing_id(system_token, breadcrumb):
    with pytest.raises(HTTPBadRequest):
        handle_stripe({}, system_token, breadcrumb)


@patch("src.services.webhook_handlers.IdentityProvisioningService.provision_primary")
def test_handle_cognito_post_confirmation(mock_provision, system_token, breadcrumb):
    mock_provision.return_value = {
        "profile": {"_id": ObjectId("507f1f77bcf86cd799439011")},
        "customer": {"_id": ObjectId("507f1f77bcf86cd799439012")},
    }

    payload = {
        "triggerSource": "PostConfirmation_ConfirmSignUp",
        "request": {
            "userAttributes": {"email": "test@example.com", "name": "Test User"}
        },
    }
    result = handle_cognito(payload, system_token, breadcrumb)
    assert "profile" in result
    mock_provision.assert_called_once()


@patch("src.services.webhook_handlers.IngressService.record_external_payload")
def test_handle_sms(mock_record, system_token, breadcrumb):
    mock_record.return_value = {"external_event": {}, "event": {}}

    payload = {"message_id": "msg_001", "body": "HELP"}
    result = handle_sms(payload, system_token, breadcrumb)
    assert "external_event" in result
    mock_record.assert_called_once()


def test_handle_sms_missing_id(system_token, breadcrumb):
    with pytest.raises(HTTPBadRequest):
        handle_sms({}, system_token, breadcrumb)
