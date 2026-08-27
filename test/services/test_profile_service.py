"""
Unit tests for ProfileService subclass in Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden
from src.services.profile_service import ProfileService


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


def test_profile_subclass_has_no_update_or_patch():
    assert not hasattr(ProfileService, "update_profile")
    assert not hasattr(ProfileService, "patch_profile")


@patch("api_utils.services.profile_service.MongoIO.get_instance")
@patch("api_utils.services.profile_service.Config.get_instance")
def test_create_profile_allowed_for_admin(
    mock_config, mock_mongo, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.PROFILE_COLLECTION_NAME = "profiles"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439011"
    mock_mongo.return_value = mock_mongo_instance

    data = {"name": "test-user", "email": "test@example.com"}
    result = ProfileService.create_profile(data, admin_token, breadcrumb)

    assert result["name"] == "test-user"
    assert result["_id"] == ObjectId("507f1f77bcf86cd799439011")
    assert result["created"] == breadcrumb
    assert result["saved"] == breadcrumb
    mock_mongo_instance.create_document.assert_called_once()


def test_create_profile_forbidden_for_non_admin(non_admin_token, breadcrumb):
    data = {"name": "test-user", "email": "test@example.com"}
    with pytest.raises(HTTPForbidden) as exc_info:
        ProfileService.create_profile(data, non_admin_token, breadcrumb)
    assert "Admin role required" in str(exc_info.value.message)
