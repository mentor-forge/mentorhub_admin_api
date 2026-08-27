"""
Unit tests for SettingService in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from src.services.setting_service import SettingService


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
        "user_id": "mentor-user",
        "roles": ["mentor"],
        "profile_id": "507f1f77bcf86cd799439012",
    }


@pytest.fixture
def breadcrumb():
    return {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "corr-setting-1",
        "from_ip": "127.0.0.1",
    }


@patch("src.services.setting_service.execute_list_query")
@patch("src.services.setting_service.Config.get_instance")
def test_get_settings_allowed_for_admin(
    mock_config, mock_query, admin_token, breadcrumb
):
    mock_config_instance = MagicMock()
    mock_config_instance.SETTING_COLLECTION_NAME = "Setting"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_query.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "type": "Product",
            "name": "Standard Plan",
        }
    ]

    result = SettingService.get_settings(
        admin_token, breadcrumb, filters={"type": "Product"}
    )
    assert len(result) == 1
    assert result[0]["type"] == "Product"
    mock_query.assert_called_once()


def test_get_settings_forbidden_for_non_admin(non_admin_token, breadcrumb):
    with pytest.raises(HTTPForbidden):
        SettingService.get_settings(non_admin_token, breadcrumb)


@patch("src.services.setting_service.MongoIO.get_instance")
@patch("src.services.setting_service.Config.get_instance")
def test_get_setting_by_id_success(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.SETTING_COLLECTION_NAME = "Setting"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.get_document.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "Standard Plan",
    }
    mock_mongo.return_value = mock_mongo_instance

    result = SettingService.get_setting(
        "507f1f77bcf86cd799439011", admin_token, breadcrumb
    )
    assert result["name"] == "Standard Plan"


@patch("src.services.setting_service.MongoIO.get_instance")
@patch("src.services.setting_service.Config.get_instance")
def test_get_setting_by_id_not_found(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.SETTING_COLLECTION_NAME = "Setting"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.get_document.return_value = None
    mock_mongo.return_value = mock_mongo_instance

    with pytest.raises(HTTPNotFound):
        SettingService.get_setting("507f1f77bcf86cd799439011", admin_token, breadcrumb)


@patch("src.services.setting_service.MongoIO.get_instance")
@patch("src.services.setting_service.Config.get_instance")
def test_create_setting_success(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.SETTING_COLLECTION_NAME = "Setting"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439011"
    mock_mongo.return_value = mock_mongo_instance

    data = {
        "type": "Product",
        "name": "Enterprise Plan",
        "subscription": "enterprise",
    }
    result = SettingService.create_setting(data, admin_token, breadcrumb)
    assert result["name"] == "Enterprise Plan"
    assert result["_id"] == ObjectId("507f1f77bcf86cd799439011")
    assert result["created"] == breadcrumb
    assert result["saved"] == breadcrumb


@patch("src.services.setting_service.MongoIO.get_instance")
@patch("src.services.setting_service.Config.get_instance")
def test_update_setting_success(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.SETTING_COLLECTION_NAME = "Setting"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    existing_doc = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "Old Plan",
        "created": {"at_time": "2026-01-01T00:00:00Z"},
    }
    mock_mongo_instance.get_document.return_value = existing_doc
    mock_mongo_instance.update_document.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "Updated Plan",
        "created": {"at_time": "2026-01-01T00:00:00Z"},
        "saved": breadcrumb,
    }
    mock_mongo.return_value = mock_mongo_instance

    update_data = {"name": "Updated Plan"}
    result = SettingService.update_setting(
        "507f1f77bcf86cd799439011", update_data, admin_token, breadcrumb
    )
    assert result["name"] == "Updated Plan"
    assert result["saved"] == breadcrumb
