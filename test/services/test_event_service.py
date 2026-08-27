"""
Unit tests for EventService subclass in Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden
from src.services.event_service import EventService


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


@patch("src.services.event_service.MongoIO.get_instance")
@patch("src.services.event_service.Config.get_instance")
def test_create_event_allowed_for_admin(
    mock_config, mock_mongo, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.EVENT_COLLECTION_NAME = "events"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439011"
    mock_mongo.return_value = mock_mongo_instance

    data = {"type": "login"}
    result = EventService.create_event(data, admin_token, breadcrumb)

    assert result["type"] == "login"
    assert result["_id"] == ObjectId("507f1f77bcf86cd799439011")
    assert result["created"] == breadcrumb
    assert result["context"]["profile_id"] == ObjectId("507f1f77bcf86cd799439011")
    assert result["context"]["user_id"] == "admin-user"
    mock_mongo_instance.create_document.assert_called_once()


@patch("src.services.event_service.MongoIO.get_instance")
@patch("src.services.event_service.Config.get_instance")
def test_create_event_with_explicit_context(
    mock_config, mock_mongo, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.EVENT_COLLECTION_NAME = "events"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439011"
    mock_mongo.return_value = mock_mongo_instance

    data = {"type": "identity_provisioned"}
    explicit_context = {"profile_id": "507f1f77bcf86cd799439099"}
    result = EventService.create_event(
        data, admin_token, breadcrumb, context=explicit_context
    )

    assert result["type"] == "identity_provisioned"
    assert result["context"]["profile_id"] == ObjectId("507f1f77bcf86cd799439099")


def test_create_event_forbidden_for_non_admin(non_admin_token, breadcrumb):
    data = {"type": "login"}
    with pytest.raises(HTTPForbidden) as exc_info:
        EventService.create_event(data, non_admin_token, breadcrumb)
    assert "Admin role required" in str(exc_info.value.message)
