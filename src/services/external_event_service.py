"""
Local ExternalEventService subclass for Mentor Hub Admin API.
"""

from api_utils.flask_utils.exceptions import HTTPForbidden
from api_utils.services import ExternalEventService as SharedExternalEventService
from api_utils.services.rbac import is_admin


class ExternalEventService(SharedExternalEventService):
    """
    Ingress append-only create; Admin-only inbound create/read.
    List HTTP lands in F013.
    """

    @classmethod
    def _check_permission(cls, token, operation):
        """Require ROLE_ADMIN for operations on the ExternalEvent subclass."""
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")
