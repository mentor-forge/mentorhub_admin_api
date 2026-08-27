"""
Setting routes for Mentor Hub Admin API.
"""

from flask import Blueprint, jsonify, request

from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.list_request import parse_list_request
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.token import create_flask_token
from src.services.setting_service import (
    SettingService,
    SETTING_LIST_FILTERS,
    SETTING_LIST_ORDER,
)


def create_setting_routes():
    """Create Flask Blueprint for Setting routes."""
    bp = Blueprint("setting_routes", __name__)

    @bp.route("", methods=["GET"])
    @handle_route_exceptions
    def get_settings():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        offset, size, filters, sort_by = parse_list_request(
            request, SETTING_LIST_FILTERS, SETTING_LIST_ORDER
        )
        settings = SettingService.get_settings(
            token,
            breadcrumb,
            offset=offset,
            size=size,
            filters=filters,
            sort_by=sort_by,
        )
        return jsonify(settings), 200

    @bp.route("", methods=["POST"])
    @handle_route_exceptions
    def create_setting():
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        setting = SettingService.create_setting(data, token, breadcrumb)
        return jsonify(setting), 201

    @bp.route("/<setting_id>", methods=["GET"])
    @handle_route_exceptions
    def get_setting(setting_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        setting = SettingService.get_setting(setting_id, token, breadcrumb)
        return jsonify(setting), 200

    @bp.route("/<setting_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_setting(setting_id):
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        setting = SettingService.update_setting(setting_id, data, token, breadcrumb)
        return jsonify(setting), 200

    return bp
