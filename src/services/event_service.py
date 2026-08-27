"""
Local EventService subclass for Mentor Hub Admin API.
"""

from api_utils.flask_utils.exceptions import HTTPForbidden
from api_utils.services import EventService as SharedEventService
from api_utils.services.rbac import is_admin


class EventService(SharedEventService):
    """
    Admin-only inbound create for operator POST /api/event and ingress.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on the Event subclass."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")
