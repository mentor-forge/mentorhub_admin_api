"""
Local ProfileService subclass for Mentor Hub Admin API.
"""

from api_utils.flask_utils.exceptions import HTTPForbidden
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
