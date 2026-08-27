"""
Local ExternalEventService subclass for Mentor Hub Admin API.
"""

from api_utils import Config
from api_utils.flask_utils.exceptions import HTTPForbidden
from api_utils.mongo_utils.list_query import (
    DEFAULT_OFFSET,
    DEFAULT_SIZE,
    build_match_filter,
    build_sort_by,
    execute_list_query,
)
from api_utils.services import ExternalEventService as SharedExternalEventService
from api_utils.services.rbac import is_admin
import logging

logger = logging.getLogger(__name__)

EXTERNAL_EVENT_LIST_FILTERS = {
    "source": {"type": "in_list", "field": "source"},
}

EXTERNAL_EVENT_LIST_ORDER = {
    "default": {"field": "created.at_time", "order": "desc"},
    "allowed": {
        "source": ("asc", "desc"),
        "created.at_time": ("asc", "desc"),
    },
}


class ExternalEventService(SharedExternalEventService):
    """
    Ingress append-only create; Admin-only inbound create/read.
    List HTTP supported via get_external_events.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on the ExternalEvent subclass."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def get_external_events(
        cls,
        token,
        breadcrumb,
        offset=DEFAULT_OFFSET,
        size=DEFAULT_SIZE,
        filters=None,
        sort_by=None,
    ):
        """
        Get a paginated array of external event audit documents.

        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            offset: Zero-based start index
            size: Number of documents to return
            filters: Parsed filter dict from parse_filter_params
            sort_by: PyMongo sort list from build_sort_by

        Returns:
            list: ExternalEvent documents
        """
        cls._check_permission(token, "read")

        config = Config.get_instance()
        match = build_match_filter(
            cls._outbound_match(token), filters or {}, EXTERNAL_EVENT_LIST_FILTERS
        )
        if sort_by is None:
            default = EXTERNAL_EVENT_LIST_ORDER["default"]
            sort_by = build_sort_by(
                default["field"], default["order"], EXTERNAL_EVENT_LIST_ORDER
            )

        events = execute_list_query(
            config.EXTERNAL_EVENT_COLLECTION_NAME,
            match=match,
            sort_by=sort_by,
            offset=offset,
            size=size,
        )

        logger.info(
            f"Retrieved {len(events)} external events (offset={offset}, size={size}) "
            f"for user {token.get('user_id')}"
        )
        return events
