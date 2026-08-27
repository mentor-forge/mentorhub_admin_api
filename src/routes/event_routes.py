"""
Event routes for Mentor Hub Admin API.
"""

from flask import jsonify, request

from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from api_utils.routes.shared_get_routes import create_event_get_routes
from src.services.event_service import EventService


def create_event_routes():
    """Create Flask Blueprint for Event routes (GET list + POST create)."""
    bp = create_event_get_routes(EventService, name="event_routes")

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_event():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        event = EventService.create_event(data, token, breadcrumb)
        return jsonify(event), 201

    return bp
