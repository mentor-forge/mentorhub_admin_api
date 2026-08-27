"""
ExternalEvent routes for Mentor Hub Admin API (list only).
"""

from flask import Blueprint, jsonify, request

from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.list_request import parse_list_request
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from src.services.external_event_service import (
    ExternalEventService,
    EXTERNAL_EVENT_LIST_FILTERS,
    EXTERNAL_EVENT_LIST_ORDER,
)


def create_external_event_routes():
    """Create Flask Blueprint for ExternalEvent routes (GET list only)."""
    bp = Blueprint("external_event_routes", __name__)

    @bp.route("", methods=["GET"])
    @handle_route_exceptions
    def get_external_events():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        offset, size, filters, sort_by = parse_list_request(
            request, EXTERNAL_EVENT_LIST_FILTERS, EXTERNAL_EVENT_LIST_ORDER
        )
        events = ExternalEventService.get_external_events(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )
        return jsonify(events), 200

    return bp
