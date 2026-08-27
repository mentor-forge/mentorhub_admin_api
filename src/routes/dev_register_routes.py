"""
Developer Edition parity registration routes (/dev/register/*).
"""

from __future__ import annotations

import os
import logging
from flask import Blueprint, jsonify, request

from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPNotFound
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.identity_provisioning_service import IdentityProvisioningService

logger = logging.getLogger(__name__)

# Synthetic system admin token for dev registration operations
DEV_SYSTEM_TOKEN = {
    "user_id": "dev-register",
    "roles": ["admin"],
    "profile_id": "000000000000000000000000",
}


def is_dev_registration_enabled() -> bool:
    """Check if dev registration endpoints are enabled in environment."""
    return os.environ.get("REGISTRATION_DEV_MODE", "true").lower() in (
        "true",
        "1",
        "yes",
    )


def create_dev_register_routes() -> Blueprint:
    """Create Flask Blueprint for /dev/register/* parity endpoints."""
    bp = Blueprint("dev_register_routes", __name__)

    @bp.route("/primary", methods=["POST"])
    @bp.route("/organization", methods=["POST"])
    @handle_route_exceptions
    def register_primary():
        if not is_dev_registration_enabled():
            raise HTTPNotFound("Dev registration disabled")

        payload = request.get_json(silent=True) or {}
        email = payload.get("email")
        if not email:
            raise HTTPBadRequest("Missing required field: email")

        org_name = (
            payload.get("organization_name") or f"{email.split('@')[0]}'s Organization"
        )
        name = payload.get("name")
        roles = payload.get("roles") or ["admin"]

        breadcrumb = create_flask_breadcrumb(DEV_SYSTEM_TOKEN)
        result = IdentityProvisioningService.provision_primary(
            email=email,
            name=name,
            organization_name=org_name,
            token=DEV_SYSTEM_TOKEN,
            breadcrumb=breadcrumb,
            roles=roles,
            source="cognito",
            external_ids={"external_id": f"dev-org:{email}"},
            raw_payload=payload,
        )

        return jsonify(result), 201

    @bp.route("/invite", methods=["POST"])
    @bp.route("/join", methods=["POST"])
    @handle_route_exceptions
    def register_invite():
        if not is_dev_registration_enabled():
            raise HTTPNotFound("Dev registration disabled")

        payload = request.get_json(silent=True) or {}
        email = payload.get("email")
        customer_id = payload.get("customer_id")

        if not email:
            raise HTTPBadRequest("Missing required field: email")
        if not customer_id:
            raise HTTPBadRequest("Missing required field: customer_id")

        name = payload.get("name")
        roles = payload.get("roles") or ["mentee"]

        breadcrumb = create_flask_breadcrumb(DEV_SYSTEM_TOKEN)
        result = IdentityProvisioningService.provision_invitee(
            customer_id=customer_id,
            email=email,
            name=name,
            token=DEV_SYSTEM_TOKEN,
            breadcrumb=breadcrumb,
            roles=roles,
            source="cognito",
            external_ids={"external_id": f"dev-join:{email}"},
            raw_payload=payload,
        )

        return jsonify(result), 201

    return bp
