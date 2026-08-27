"""
Unit tests for CustomerService (consumed view) in Mentor Hub Admin API.
"""

import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from src.services.customer_service import CustomerService


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
        "correlation_id": "corr-customer-1",
        "from_ip": "127.0.0.1",
    }


@patch("src.services.customer_service.MongoIO.get_instance")
@patch("src.services.customer_service.Config.get_instance")
def test_get_customer_success(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.CUSTOMER_COLLECTION_NAME = "Customer"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.get_document.return_value = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Acme Inc",
        "status": "active",
    }
    mock_mongo.return_value = mock_mongo_instance

    result = CustomerService.get_customer(
        "507f1f77bcf86cd799439011", admin_token, breadcrumb
    )
    assert result["name"] == "Acme Inc"


@patch("src.services.customer_service.MongoIO.get_instance")
@patch("src.services.customer_service.Config.get_instance")
def test_get_customer_not_found(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.CUSTOMER_COLLECTION_NAME = "Customer"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.get_document.return_value = None
    mock_mongo.return_value = mock_mongo_instance

    with pytest.raises(HTTPNotFound):
        CustomerService.get_customer(
            "507f1f77bcf86cd799439011", admin_token, breadcrumb
        )


def test_get_customer_forbidden_for_non_admin(non_admin_token, breadcrumb):
    with pytest.raises(HTTPForbidden):
        CustomerService.get_customer(
            "507f1f77bcf86cd799439011", non_admin_token, breadcrumb
        )


@patch("src.services.customer_service.MongoIO.get_instance")
@patch("src.services.customer_service.Config.get_instance")
def test_get_by_stripe_customer_id(mock_config, mock_mongo, admin_token, breadcrumb):
    mock_config_instance = MagicMock()
    mock_config_instance.CUSTOMER_COLLECTION_NAME = "Customer"
    mock_config_instance.ROLE_ADMIN = "admin"
    mock_config.return_value = mock_config_instance

    mock_mongo_instance = MagicMock()
    mock_mongo_instance.get_documents.return_value = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "stripe_customer_id": "cus_123",
        }
    ]
    mock_mongo.return_value = mock_mongo_instance

    result = CustomerService.get_by_stripe_customer_id(
        "cus_123", admin_token, breadcrumb
    )
    assert result["stripe_customer_id"] == "cus_123"
