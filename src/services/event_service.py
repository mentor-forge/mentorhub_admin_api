"""
Local EventService subclass for Mentor Hub Admin API.
"""

from bson import ObjectId
from api_utils import Config, MongoIO
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPInternalServerError
from api_utils.mongo_utils import encode_document
from api_utils.services import EventService as SharedEventService
from api_utils.services.rbac import is_admin
import logging

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id", "profile_id", "resource_id", "journey_id", "customer_id"]
DATE_PROPERTIES = []


class EventService(SharedEventService):
    """
    Local Event service subclass.

    Admin-only inbound create for operator POST /api/event and ingress.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on the Event subclass."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def create_event(cls, data, token, breadcrumb, *, context=None):
        """
        Create a new event document.

        Args:
            data: Dictionary containing event data (e.g. type)
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            context: Optional explicit context dict (overrides token-as-context)

        Returns:
            dict: The created event document including _id
        """
        try:
            cls._check_permission(token, "create")

            event_data = dict(data)
            if "_id" in event_data:
                del event_data["_id"]
            event_data.pop("created", None)

            if context is not None:
                event_data["context"] = dict(context)
            elif "context" in event_data and isinstance(event_data["context"], dict):
                event_data["context"] = dict(event_data["context"])
            else:
                event_data["context"] = dict(token)

            encode_document(event_data, ID_PROPERTIES, DATE_PROPERTIES)
            event_data["created"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event_id = mongo.create_document(config.EVENT_COLLECTION_NAME, event_data)
            if "_id" not in event_data:
                event_data["_id"] = ObjectId(event_id)
            logger.info(f"Created event {event_id} for user {token.get('user_id')}")

            return event_data
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating event: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create event: {error_msg}")
