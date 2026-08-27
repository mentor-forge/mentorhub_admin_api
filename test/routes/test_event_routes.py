"""
Unit tests for Event routes in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from bson import ObjectId
from api_utils import MongoJSONEncoder
from api_utils.flask_utils.exceptions import HTTPForbidden
from src.routes.event_routes import create_event_routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.json = MongoJSONEncoder(app)
    app.register_blueprint(create_event_routes(), url_prefix="/api/event")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@patch("src.routes.event_routes.EventService.create_event")
@patch("src.routes.event_routes.create_flask_breadcrumb")
@patch("src.routes.event_routes.create_flask_token")
def test_create_event_success(mock_token, mock_breadcrumb, mock_create, client):
    mock_token.return_value = {
        "user_id": "admin-user",
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
        "type": "login",
        "context": {"profile_id": "507f1f77bcf86cd799439011"},
    }

    response = client.post("/api/event", json={"type": "login"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["type"] == "login"
    assert data["_id"] == "507f1f77bcf86cd799439011"
    mock_create.assert_called_once()


@patch("src.routes.event_routes.EventService.create_event")
@patch("src.routes.event_routes.create_flask_breadcrumb")
@patch("src.routes.event_routes.create_flask_token")
def test_create_event_forbidden(mock_token, mock_breadcrumb, mock_create, client):
    mock_token.return_value = {
        "user_id": "user",
        "roles": ["mentor"],
        "profile_id": "507f1f77bcf86cd799439012",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_create.side_effect = HTTPForbidden("Admin role required")

    response = client.post("/api/event", json={"type": "login"})
    assert response.status_code == 403


@patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
@patch("api_utils.routes.shared_get_routes.create_flask_token")
@patch("src.services.event_service.EventService.get_events")
def test_get_events_list(mock_get_events, mock_token, mock_breadcrumb, client):
    mock_token.return_value = {
        "user_id": "admin-user",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }
    mock_breadcrumb.return_value = {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "c1",
        "from_ip": "127.0.0.1",
    }
    mock_get_events.return_value = [
        {"_id": ObjectId("507f1f77bcf86cd799439011"), "type": "login"}
    ]

    response = client.get("/api/event")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["type"] == "login"
