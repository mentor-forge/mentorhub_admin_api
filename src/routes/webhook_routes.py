"""
Webhook transport routes for provider listeners (Stripe, Cognito, SMS).
"""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request

from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.webhook_handlers import handle_cognito, handle_sms, handle_stripe
from src.services.webhook_transport import (
    get_webhook_system_token,
    verify_secret_header,
    verify_stripe_signature,
)

logger = logging.getLogger(__name__)


def create_webhook_routes() -> Blueprint:
    """Create Flask Blueprint for provider webhook listeners."""
    bp = Blueprint("webhook_routes", __name__)

    @bp.route("/stripe", methods=["POST"])
    @handle_route_exceptions
    def stripe_webhook():
        # Verify Stripe signature (or transport secret)
        raw_body = request.get_data()
        sig_header = request.headers.get("Stripe-Signature")
        if sig_header:
            verify_stripe_signature(raw_body, sig_header)
        else:
            verify_secret_header(
                request.headers.get("X-Webhook-Secret"),
                "STRIPE_WEBHOOK_SECRET",
            )

        payload = request.get_json(silent=True) or {}
        token = get_webhook_system_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = handle_stripe(payload, token, breadcrumb)
        return (
            jsonify({"received": True, "idempotent": result.get("idempotent", False)}),
            200,
        )

    @bp.route("/cognito", methods=["POST"])
    @handle_route_exceptions
    def cognito_webhook():
        verify_secret_header(
            request.headers.get("X-Cognito-Secret")
            or request.headers.get("X-Webhook-Secret"),
            "COGNITO_WEBHOOK_SECRET",
        )

        payload = request.get_json(silent=True) or {}
        token = get_webhook_system_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = handle_cognito(payload, token, breadcrumb)
        return (
            jsonify(
                {
                    "received": True,
                    "provisioned": "profile" in result,
                    "idempotent": result.get("idempotent", False),
                }
            ),
            200,
        )

    @bp.route("/sms", methods=["POST"])
    @handle_route_exceptions
    def sms_webhook():
        verify_secret_header(
            request.headers.get("X-SMS-Secret")
            or request.headers.get("X-Webhook-Secret"),
            "SMS_WEBHOOK_SECRET",
        )

        payload = request.get_json(silent=True) or {}
        token = get_webhook_system_token()
        breadcrumb = create_flask_breadcrumb(token)

        result = handle_sms(payload, token, breadcrumb)
        return (
            jsonify({"received": True, "idempotent": result.get("idempotent", False)}),
            200,
        )

    return bp
