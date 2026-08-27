"""
Local ProfileService subclass for Mentor Hub Admin API.
"""

from bson import ObjectId
from api_utils import Config, MongoIO
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound
from api_utils.services import ProfileService as SharedProfileService
from api_utils.services.rbac import is_admin


class ProfileService(SharedProfileService):
    """
    Ingress may create Profile (shared create_profile).
    No Profile HTTP or PATCH here (Customer controls Profile).
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on the Profile subclass."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def get_by_email(cls, email):
        """Lookup a profile document by email for provisioning idempotency."""
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        docs = mongo.get_documents(
            config.PROFILE_COLLECTION_NAME,
            match={"email": email},
        )
        return docs[0] if docs else None

    @classmethod
    def get_profile(cls, profile_id, token, breadcrumb):
        """Lookup a single profile document by ID."""
        cls._check_permission(token, "read")
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        try:
            doc = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
        except Exception:
            raise HTTPNotFound(f"Profile {profile_id} not found")
        if not doc:
            raise HTTPNotFound(f"Profile {profile_id} not found")
        return doc
