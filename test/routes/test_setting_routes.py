"""
Unit tests for Setting routes in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch
from flask import Flask
from bson import ObjectId
from api_utils import MongoJSONEncoder
from src.routes.setting_routes import create_setting_routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.json = MongoJSONEncoder(app)
    app.register_blueprint(create_setting_routes(), url_prefix="/api/setting")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@patch("src.routes.setting_routes.SettingService.get_settings")
@patch("src.routes.setting_routes.create_flask_breadcrumb")
@patch("src.routes.setting_routes.create_flask_token")
def test_get_settings_route(mock_token, mock_breadcrumb, mock_get_settings, client):
    mock_token.return_value = {
        "user_id": "admin-user",
        "display_name": "Admin User",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_get_settings.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "type": "Product",
            "name": "Standard Plan",
        }
    ]

    response = client.get("/api/setting?type=Product")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Standard Plan"


@patch("src.routes.setting_routes.SettingService.create_setting")
@patch("src.routes.setting_routes.create_flask_breadcrumb")
@patch("src.routes.setting_routes.create_flask_token")
def test_create_setting_route(mock_token, mock_breadcrumb, mock_create, client):
    mock_token.return_value = {
        "user_id": "admin-user",
        "display_name": "Admin User",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_create.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "New Plan",
    }

    response = client.post("/api/setting", json={"type": "Product", "name": "New Plan"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "New Plan"


@patch("src.routes.setting_routes.SettingService.get_setting")
@patch("src.routes.setting_routes.create_flask_breadcrumb")
@patch("src.routes.setting_routes.create_flask_token")
def test_get_setting_by_id_route(mock_token, mock_breadcrumb, mock_get, client):
    mock_token.return_value = {
        "user_id": "admin-user",
        "display_name": "Admin User",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_get.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "Single Plan",
    }

    response = client.get("/api/setting/507f1f77bcf86cd799439011")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Single Plan"


@patch("src.routes.setting_routes.SettingService.update_setting")
@patch("src.routes.setting_routes.create_flask_breadcrumb")
@patch("src.routes.setting_routes.create_flask_token")
def test_patch_setting_route(mock_token, mock_breadcrumb, mock_update, client):
    mock_token.return_value = {
        "user_id": "admin-user",
        "display_name": "Admin User",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_update.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "type": "Product",
        "name": "Updated Plan",
    }

    response = client.patch(
        "/api/setting/507f1f77bcf86cd799439011", json={"name": "Updated Plan"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Updated Plan"
