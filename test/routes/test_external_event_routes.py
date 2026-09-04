"""
Unit tests for ExternalEvent routes in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch
from flask import Flask
from bson import ObjectId
from api_utils import MongoJSONEncoder
from src.routes.external_event_routes import create_external_event_routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.json = MongoJSONEncoder(app)
    app.register_blueprint(
        create_external_event_routes(), url_prefix="/api/external-event"
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@patch("src.routes.external_event_routes.ExternalEventService.get_external_events")
@patch("src.routes.external_event_routes.create_flask_breadcrumb")
@patch("src.routes.external_event_routes.create_flask_token")
def test_get_external_events_list(mock_token, mock_breadcrumb, mock_get_events, client):
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
    mock_get_events.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "source": "stripe",
            "external_id": "evt_1",
        }
    ]

    response = client.get("/api/external-event?source=stripe")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["source"] == "stripe"
    mock_get_events.assert_called_once()


def test_external_event_post_not_allowed(client):
    response = client.post("/api/external-event", json={"source": "stripe"})
    assert response.status_code == 405


def test_external_event_by_id_not_found(client):
    response = client.get("/api/external-event/507f1f77bcf86cd799439011")
    assert response.status_code == 404
