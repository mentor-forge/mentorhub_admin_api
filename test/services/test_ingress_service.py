"""
Unit tests for IngressService in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.ingress_service import (
    IngressService,
    compute_payload_hash,
    normalize_payload_body,
)


@pytest.fixture
def admin_token():
    return {
        "user_id": "ingress",
        "display_name": "Ingress",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }


@pytest.fixture
def breadcrumb():
    return {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "ingress",
        "correlation_id": "corr-ingress-1",
        "from_ip": "127.0.0.1",
    }


def test_compute_payload_hash():
    payload_str = '{"key":"value"}'
    payload_bytes = b'{"key":"value"}'
    payload_dict = {"key": "value"}

    hash1 = compute_payload_hash(payload_str)
    hash2 = compute_payload_hash(payload_bytes)
    hash3 = compute_payload_hash(payload_dict)

    assert hash1 == hash2
    assert hash1 == hash3
    assert len(hash1) == 64


def test_normalize_payload_body():
    assert normalize_payload_body({"foo": "bar"}) == {"foo": "bar"}
    assert normalize_payload_body(b'{"foo": "bar"}') == {"foo": "bar"}
    assert normalize_payload_body('{"foo": "bar"}') == {"foo": "bar"}
    assert normalize_payload_body("invalid json") == {"raw": "invalid json"}


@patch(
    "src.services.ingress_service.ExternalEventService.get_by_source_and_external_id"
)
@patch("src.services.ingress_service.ExternalEventService.create_external_event")
@patch("src.services.ingress_service.EventService.create_event")
@patch("src.services.ingress_service.Config.get_instance")
def test_record_external_payload_success(
    mock_config,
    mock_create_event,
    mock_create_ext_event,
    mock_get_existing,
    admin_token,
    breadcrumb,
):
    mock_config_instance = MagicMock()
    mock_config_instance.EVENT_TYPE_EXTERNAL_RECEIVED = "external_received"
    mock_config.return_value = mock_config_instance

    mock_get_existing.return_value = None

    mock_create_ext_event.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "source": "stripe",
        "external_id": "evt_stripe_1",
    }
    mock_create_event.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "type": "external_received",
        "context": {"profile_id": "507f1f77bcf86cd799439099"},
    }

    result = IngressService.record_external_payload(
        source="stripe",
        external_id="evt_stripe_1",
        raw_payload={"type": "payment_intent.succeeded"},
        token=admin_token,
        breadcrumb=breadcrumb,
        context={"profile_id": "507f1f77bcf86cd799439099"},
    )

    assert result["idempotent"] is False
    assert result["external_event"]["source"] == "stripe"
    assert result["event"]["type"] == "external_received"
    mock_create_ext_event.assert_called_once()
    mock_create_event.assert_called_once()


@patch(
    "src.services.ingress_service.ExternalEventService.get_by_source_and_external_id"
)
@patch("src.services.ingress_service.ExternalEventService.create_external_event")
@patch("src.services.ingress_service.EventService.create_event")
@patch("src.services.ingress_service.Config.get_instance")
def test_record_external_payload_idempotent_duplicate(
    mock_config,
    mock_create_event,
    mock_create_ext_event,
    mock_get_existing,
    admin_token,
    breadcrumb,
):
    mock_config_instance = MagicMock()
    mock_config_instance.EVENT_TYPE_EXTERNAL_RECEIVED = "external_received"
    mock_config.return_value = mock_config_instance

    existing_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "source": "stripe",
        "external_id": "evt_stripe_1",
    }
    mock_get_existing.return_value = existing_doc

    result = IngressService.record_external_payload(
        source="stripe",
        external_id="evt_stripe_1",
        raw_payload={"type": "payment_intent.succeeded"},
        token=admin_token,
        breadcrumb=breadcrumb,
    )

    assert result["idempotent"] is True
    assert result["external_event"] == existing_doc
    assert result["event"] is None
    mock_create_ext_event.assert_not_called()
    mock_create_event.assert_not_called()
