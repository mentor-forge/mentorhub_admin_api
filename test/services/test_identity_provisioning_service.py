"""
Unit tests for IdentityProvisioningService in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from src.services.identity_provisioning_service import (
    IdentityProvisioningService,
)


@pytest.fixture
def admin_token():
    return {
        "user_id": "admin-user",
        "display_name": "Admin User",
        "roles": ["admin"],
        "profile_id": "507f1f77bcf86cd799439011",
    }


@pytest.fixture
def non_admin_token():
    return {
        "user_id": "mentor-user",
        "display_name": "Mentor User",
        "roles": ["mentor"],
        "profile_id": "507f1f77bcf86cd799439012",
    }


@pytest.fixture
def breadcrumb():
    return {
        "at_time": "2026-08-27T12:00:00Z",
        "by_user": "admin-user",
        "correlation_id": "corr-prov-1",
        "from_ip": "127.0.0.1",
    }


@patch(
    "src.services.identity_provisioning_service.IngressService.record_external_payload"
)
@patch("src.services.identity_provisioning_service.ProfileService.create_profile")
@patch("src.services.identity_provisioning_service.ProfileService.get_by_email")
@patch(
    "src.services.identity_provisioning_service.CustomerService.create_provisioned_customer"
)
@patch("src.services.identity_provisioning_service.Config.get_instance")
def test_provision_primary_success(
    mock_config,
    mock_create_cust,
    mock_get_email,
    mock_create_prof,
    mock_record_ingress,
    admin_token,
    breadcrumb,
):
    mock_config_instance = MagicMock()
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config_instance.EVENT_TYPE_IDENTITY_PROVISIONED = "identity_provisioned"
    mock_config.return_value = mock_config_instance

    mock_get_email.return_value = None

    mock_create_cust.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "name": "Acme Corp",
        "status": "provisioned",
    }

    mock_create_prof.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "email": "owner@acme.com",
        "roles": ["admin", "member"],
        "customer_id": ObjectId("507f1f77bcf86cd799439022"),
        "status": "provisioned",
    }

    result = IdentityProvisioningService.provision_primary(
        email="owner@acme.com",
        name="Owner Name",
        organization_name="Acme Corp",
        token=admin_token,
        breadcrumb=breadcrumb,
        source="cognito",
        external_ids={"sub": "sub-123"},
    )

    assert result["idempotent"] is False
    assert result["customer"]["status"] == "provisioned"
    assert result["profile"]["status"] == "provisioned"
    assert result["profile"]["customer_id"] == ObjectId("507f1f77bcf86cd799439022")
    mock_create_cust.assert_called_once()
    mock_create_prof.assert_called_once()
    mock_record_ingress.assert_called_once()


@patch("src.services.identity_provisioning_service.EventService.create_event")
@patch(
    "src.services.identity_provisioning_service.IngressService.record_external_payload"
)
@patch("src.services.identity_provisioning_service.ProfileService.create_profile")
@patch("src.services.identity_provisioning_service.ProfileService.get_by_email")
@patch("src.services.identity_provisioning_service.CustomerService.get_customer")
@patch(
    "src.services.identity_provisioning_service.CustomerService.create_provisioned_customer"
)
@patch("src.services.identity_provisioning_service.Config.get_instance")
def test_provision_invitee_success(
    mock_config,
    mock_create_cust,
    mock_get_cust,
    mock_get_email,
    mock_create_prof,
    mock_record_ingress,
    mock_create_event,
    admin_token,
    breadcrumb,
):
    mock_config_instance = MagicMock()
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config_instance.EVENT_TYPE_IDENTITY_PROVISIONED = "identity_provisioned"
    mock_config.return_value = mock_config_instance

    mock_get_cust.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "name": "Acme Corp",
    }
    mock_get_email.return_value = None

    mock_create_prof.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439044"),
        "email": "member@acme.com",
        "roles": ["member"],
        "customer_id": ObjectId("507f1f77bcf86cd799439022"),
        "status": "provisioned",
    }

    result = IdentityProvisioningService.provision_invitee(
        customer_id="507f1f77bcf86cd799439022",
        email="member@acme.com",
        name="Member Name",
        token=admin_token,
        breadcrumb=breadcrumb,
    )

    assert result["idempotent"] is False
    assert result["profile"]["email"] == "member@acme.com"
    # Invitee does NOT create a Customer!
    mock_create_cust.assert_not_called()
    mock_create_prof.assert_called_once()


def test_provision_primary_forbidden_for_non_admin(non_admin_token, breadcrumb):
    with pytest.raises(HTTPForbidden):
        IdentityProvisioningService.provision_primary(
            email="test@example.com",
            name="Test",
            organization_name="Test Org",
            token=non_admin_token,
            breadcrumb=breadcrumb,
        )
