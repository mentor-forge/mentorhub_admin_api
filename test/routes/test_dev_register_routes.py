"""
Unit tests for Developer Edition parity registration routes (/dev/register/*).
"""

import pytest
from unittest.mock import patch
from flask import Flask
from bson import ObjectId
from api_utils import MongoJSONEncoder
from src.routes.dev_register_routes import create_dev_register_routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.json = MongoJSONEncoder(app)
    app.register_blueprint(create_dev_register_routes(), url_prefix="/dev/register")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@patch("src.routes.dev_register_routes.IdentityProvisioningService.provision_primary")
def test_register_primary_success(mock_provision, client):
    mock_provision.return_value = {
        "profile": {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "dev.owner@example.com",
            "display_name": "Dev Owner",
            "roles": ["admin"],
            "status": "provisioned",
        },
        "customer": {
            "_id": ObjectId("507f1f77bcf86cd799439022"),
            "name": "Dev Corp",
            "status": "provisioned",
        },
        "idempotent": False,
    }

    payload = {
        "email": "dev.owner@example.com",
        "name": "Dev Owner",
        "organization_name": "Dev Corp",
    }
    response = client.post("/dev/register/primary", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["profile"]["email"] == "dev.owner@example.com"
    assert data["customer"]["name"] == "Dev Corp"
    # Ensure no JWT/token minting in response
    assert "token" not in data
    assert "jwt" not in data
    mock_provision.assert_called_once()


def test_register_primary_missing_email(client):
    response = client.post(
        "/dev/register/primary", json={"organization_name": "Dev Corp"}
    )
    assert response.status_code == 400


@patch("src.routes.dev_register_routes.IdentityProvisioningService.provision_invitee")
def test_register_invite_success(mock_provision, client):
    mock_provision.return_value = {
        "profile": {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "email": "dev.member@example.com",
            "display_name": "Dev Member",
            "roles": ["mentee"],
            "status": "provisioned",
        },
        "customer": {
            "_id": ObjectId("507f1f77bcf86cd799439022"),
            "name": "Dev Corp",
        },
        "idempotent": False,
    }

    payload = {
        "email": "dev.member@example.com",
        "name": "Dev Member",
        "customer_id": "507f1f77bcf86cd799439022",
    }
    response = client.post("/dev/register/invite", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["profile"]["email"] == "dev.member@example.com"
    assert "token" not in data
    mock_provision.assert_called_once()


def test_register_invite_missing_fields(client):
    r1 = client.post("/dev/register/invite", json={"email": "dev.member@example.com"})
    assert r1.status_code == 400

    r2 = client.post(
        "/dev/register/invite", json={"customer_id": "507f1f77bcf86cd799439022"}
    )
    assert r2.status_code == 400


def test_dev_register_disabled_returns_404(monkeypatch, client):
    monkeypatch.setenv("REGISTRATION_DEV_MODE", "false")
    response = client.post(
        "/dev/register/primary", json={"email": "dev.test@example.com"}
    )
    assert response.status_code == 404
