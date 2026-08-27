"""
Customer service (read-only consumed view & provisioned create) for Mentor Hub Admin API.
"""

from bson import ObjectId
from api_utils import Config, MongoIO
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from api_utils.mongo_utils import encode_document
from api_utils.services.rbac import is_admin
import logging

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id"]
DATE_PROPERTIES = []


class CustomerService:
    """
    Consumed Customer service for lookup and provisioned-create operations in Admin API.
    All operations require ROLE_ADMIN.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on consumed Customer lookups."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def get_customer(cls, customer_id, token, breadcrumb):
        """Lookup a customer document by ID."""
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        try:
            doc = mongo.get_document(config.CUSTOMER_COLLECTION_NAME, customer_id)
        except Exception:
            raise HTTPNotFound(f"Customer {customer_id} not found")
        if not doc:
            raise HTTPNotFound(f"Customer {customer_id} not found")
        return doc

    @classmethod
    def get_by_stripe_customer_id(cls, stripe_customer_id, token, breadcrumb):
        """Lookup a customer document by stripe_customer_id."""
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        docs = mongo.get_documents(
            config.CUSTOMER_COLLECTION_NAME,
            match={"stripe_customer_id": stripe_customer_id},
        )
        return docs[0] if docs else None

    @classmethod
    def get_by_name(cls, name, token, breadcrumb):
        """Lookup a customer document by organization name."""
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        docs = mongo.get_documents(
            config.CUSTOMER_COLLECTION_NAME,
            match={"name": name},
        )
        return docs[0] if docs else None

    @classmethod
    def create_provisioned_customer(cls, data, token, breadcrumb):
        """Create minimal Customer organization shell in provisioned status."""
        cls._check_permission(token, "create")
        customer_data = dict(data)
        for field in ("_id", "created", "saved"):
            customer_data.pop(field, None)
        if "status" not in customer_data:
            customer_data["status"] = "provisioned"

        encode_document(customer_data, ID_PROPERTIES, DATE_PROPERTIES)
        customer_data["created"] = breadcrumb
        customer_data["saved"] = breadcrumb

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        customer_id = mongo.create_document(
            config.CUSTOMER_COLLECTION_NAME, customer_data
        )
        customer_data["_id"] = ObjectId(customer_id)
        logger.info(f"Created provisioned Customer {customer_id}")
        return customer_data
