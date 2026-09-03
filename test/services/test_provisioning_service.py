"""
Unit tests for ProvisioningService in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden
from src.services.provisioning_service import ProvisioningService


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


@patch("src.services.provisioning_service.IngressService.record_external_payload")
@patch("src.services.provisioning_service.ProfileService.create_profile")
@patch("src.services.provisioning_service.ProfileService.get_by_email")
@patch("src.services.provisioning_service.MongoIO.get_instance")
@patch("src.services.provisioning_service.Config.get_instance")
def test_provision_identity_new_account(
    mock_config,
    mock_mongo,
    mock_get_email,
    mock_create_profile,
    mock_record_ingress,
    admin_token,
    breadcrumb,
):
    mock_config_instance = MagicMock()
    mock_config_instance.CUSTOMER_COLLECTION_NAME = "Customer"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config_instance.EVENT_TYPE_IDENTITY_PROVISIONED = "identity_provisioned"
    mock_config.return_value = mock_config_instance

    mock_get_email.return_value = None

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.create_document.return_value = "507f1f77bcf86cd799439022"
    mock_mongo.return_value = mock_mongo_instance

    mock_create_profile.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "email": "new.member@example.com",
        "roles": ["admin", "member"],
        "customer_id": ObjectId("507f1f77bcf86cd799439022"),
        "status": "active",
    }

    result = ProvisioningService.provision_identity(
        email="new.member@example.com",
        organization_name="New Corp",
        token=admin_token,
        breadcrumb=breadcrumb,
        source="cognito",
        external_id="post_conf_123",
    )

    assert result["idempotent"] is False
    assert result["profile"]["email"] == "new.member@example.com"
    assert result["customer"]["_id"] == ObjectId("507f1f77bcf86cd799439022")
    mock_record_ingress.assert_called_once()


@patch("src.services.provisioning_service.CustomerService.get_customer")
@patch("src.services.provisioning_service.ProfileService.get_by_email")
def test_provision_identity_existing_account_idempotent(
    mock_get_email, mock_get_customer, admin_token, breadcrumb
):
    existing_profile = {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "email": "existing@example.com",
        "customer_id": ObjectId("507f1f77bcf86cd799439022"),
    }
    mock_get_email.return_value = existing_profile

    existing_customer = {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "name": "Existing Corp",
    }
    mock_get_customer.return_value = existing_customer

    result = ProvisioningService.provision_identity(
        email="existing@example.com",
        organization_name="Existing Corp",
        token=admin_token,
        breadcrumb=breadcrumb,
    )

    assert result["idempotent"] is True
    assert result["profile"] == existing_profile
    assert result["customer"] == existing_customer


def test_provision_identity_forbidden_for_non_admin(non_admin_token, breadcrumb):
    with pytest.raises(HTTPForbidden):
        ProvisioningService.provision_identity(
            email="test@example.com",
            organization_name="Test Org",
            token=non_admin_token,
            breadcrumb=breadcrumb,
        )
