"""
Setting service for Admin control over system catalog and ops configurations.
"""

from bson import ObjectId
from api_utils import Config, MongoIO
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
    HTTPBadRequest,
)
from api_utils.mongo_utils import encode_document
from api_utils.mongo_utils.list_query import (
    DEFAULT_OFFSET,
    DEFAULT_SIZE,
    build_match_filter,
    build_sort_by,
    execute_list_query,
)
from api_utils.services.rbac import (
    EMPTY_SCOPE_MATCH,
    build_outbound_match,
    is_admin,
    require_outbound,
)
import logging

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id"]
DATE_PROPERTIES = ["expires_at"]
SYSTEM_MANAGED_FIELDS = ("_id", "created", "saved")

SETTING_LIST_FILTERS = {
    "type": {"type": "in_list", "field": "type"},
    "name": {"type": "contains", "field": "name"},
    "status": {"type": "in_list", "field": "status"},
}

SETTING_LIST_ORDER = {
    "default": {"field": "name", "order": "asc"},
    "allowed": {
        "name": ("asc", "desc"),
        "type": ("asc", "desc"),
        "created.at_time": ("asc", "desc"),
        "saved.at_time": ("asc", "desc"),
    },
}


class SettingService:
    """
    Service class for Setting operations (Admin controlled).
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """All Setting operations require ROLE_ADMIN."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def _outbound_match(cls, token):
        """Admin callers are unrestricted; non-admin callers see nothing."""
        return build_outbound_match(token, [EMPTY_SCOPE_MATCH])

    @classmethod
    def get_settings(
        cls,
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
    ):
        """
        Retrieve a paginated list of Setting documents.
        """
        cls._check_permission(token, "read")

        config = Config.get_instance()
        match = build_match_filter(
            cls._outbound_match(token), filters or {}, SETTING_LIST_FILTERS
        )
        if sort_by is None:
            default = SETTING_LIST_ORDER["default"]
            sort_by = build_sort_by(
                default["field"], default["order"], SETTING_LIST_ORDER
            )

        settings = execute_list_query(
            config.SETTING_COLLECTION_NAME,
            match=match,
            sort_by=sort_by,
            offset=offset,
            size=size,
        )

        logger.info(
            f"Retrieved {len(settings)} settings (offset={offset}, size={size}) "
            f"for user {token.get('user_id')}"
        )
        return settings

    @classmethod
    def get_setting(cls, setting_id, token, breadcrumb):
        """
        Retrieve a single Setting document by ID.
        """
        cls._check_permission(token, "read")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        try:
            setting = mongo.get_document(config.SETTING_COLLECTION_NAME, setting_id)
        except Exception:
            raise HTTPNotFound(f"Setting {setting_id} not found")

        require_outbound(
            setting,
            cls._outbound_match(token),
            not_found_message=f"Setting {setting_id} not found",
        )

        logger.info(f"Retrieved setting {setting_id} for user {token.get('user_id')}")
        return setting

    @classmethod
    def create_setting(cls, data, token, breadcrumb):
        """
        Create a new Setting document.
        """
        try:
            cls._check_permission(token, "create")

            setting_data = dict(data)
            for field in SYSTEM_MANAGED_FIELDS:
                setting_data.pop(field, None)

            encode_document(setting_data, ID_PROPERTIES, DATE_PROPERTIES)
            setting_data["created"] = breadcrumb
            setting_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            setting_id = mongo.create_document(
                config.SETTING_COLLECTION_NAME, setting_data
            )
            if "_id" not in setting_data:
                setting_data["_id"] = ObjectId(setting_id)

            logger.info(f"Created setting {setting_id} for user {token.get('user_id')}")
            return setting_data
        except (HTTPForbidden, HTTPBadRequest):
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating setting: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create setting: {error_msg}")

    @classmethod
    def update_setting(cls, setting_id, data, token, breadcrumb):
        """
        Update mutable fields on an existing Setting document.
        """
        try:
            cls._check_permission(token, "update")

            # Verify existence and outbound visibility
            existing = cls.get_setting(setting_id, token, breadcrumb)

            update_data = dict(data)
            # Never overwrite _id or created
            update_data.pop("_id", None)
            update_data.pop("created", None)

            encode_document(update_data, ID_PROPERTIES, DATE_PROPERTIES)
            update_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated_doc = mongo.update_document(
                config.SETTING_COLLECTION_NAME, setting_id, update_data
            )

            logger.info(f"Updated setting {setting_id} for user {token.get('user_id')}")
            return updated_doc or {**existing, **update_data}
        except (HTTPForbidden, HTTPNotFound, HTTPBadRequest):
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error updating setting: {error_msg}")
            raise HTTPInternalServerError(f"Failed to update setting: {error_msg}")
