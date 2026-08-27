"""
Unit tests for ExternalEventService subclass in Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden
from src.services.external_event_service import ExternalEventService


@pytest.fixture
def admin_token():
    return {
        "user_id": "admin-user",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }


@pytest.fixture
def non_admin_token():
    return {
        "user_id": "regular-user",
        "roles": ["mentor"],
        "profile_id": "507f1f77bcf86cd799439012",
    }


@pytest.fixture
def breadcrumb():
    return {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "corr-123",
        "from_ip": "127.0.0.1",
    }


@patch("api_utils.services.external_event_service.MongoIO.get_instance")
@patch("api_utils.services.external_event_service.Config.get_instance")
def test_create_external_event_allowed_for_admin(
    mock_config, mock_mongo, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.EXTERNAL_EVENT_COLLECTION_NAME = "external_events"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439011"
    mock_mongo.return_value = mock_mongo_instance

    data = {
        "source": "stripe",
        "external_id": "evt_123",
        "payload_hash": "hash123",
        "normalized_body": {"type": "charge.succeeded"},
    }
    result = ExternalEventService.create_external_event(data, admin_token, breadcrumb)

    assert result["source"] == "stripe"
    assert result["_id"] == ObjectId("507f1f77bcf86cd799439011")
    assert result["created"] == breadcrumb
    mock_mongo_instance.create_document.assert_called_once()


def test_create_external_event_forbidden_for_non_admin(non_admin_token, breadcrumb):
    data = {
        "source": "stripe",
        "external_id": "evt_123",
        "payload_hash": "hash123",
        "normalized_body": {"type": "charge.succeeded"},
    }
    with pytest.raises(HTTPForbidden) as exc_info:
        ExternalEventService.create_external_event(data, non_admin_token, breadcrumb)
    assert "Admin role required" in str(exc_info.value.message)


@patch("src.services.external_event_service.execute_list_query")
@patch("src.services.external_event_service.Config.get_instance")
def test_get_external_events_allowed_for_admin(
    mock_config, mock_query, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.EXTERNAL_EVENT_COLLECTION_NAME = "ExternalEvent"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_query.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "source": "stripe",
            "external_id": "evt_1",
        }
    ]

    events = ExternalEventService.get_external_events(
        admin_token,
        breadcrumb,
        offset=0,
        size=10,
        filters={"source": "stripe"},
    )
    assert len(events) == 1
    assert events[0]["source"] == "stripe"
    mock_query.assert_called_once()


def test_get_external_events_forbidden_for_non_admin(non_admin_token, breadcrumb):
    with pytest.raises(HTTPForbidden) as exc_info:
        ExternalEventService.get_external_events(non_admin_token, breadcrumb)
    assert "Admin role required" in str(exc_info.value.message)
