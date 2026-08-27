"""
Routes package for Mentor Hub Admin API.
"""

from src.routes.event_routes import create_event_routes
from src.routes.external_event_routes import create_external_event_routes
from src.routes.setting_routes import create_setting_routes
from src.routes.webhook_routes import create_webhook_routes

__all__ = [
    "create_event_routes",
    "create_external_event_routes",
    "create_setting_routes",
    "create_webhook_routes",
]
