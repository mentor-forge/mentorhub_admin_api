"""
Webhook transport and signature verification utilities for provider listeners.
"""

from __future__ import annotations

import hmac
import hashlib
import os
import time
import logging
from api_utils.flask_utils.exceptions import HTTPUnauthorized

logger = logging.getLogger(__name__)

WEBHOOK_SYSTEM_TOKEN = {
    "user_id": "webhook-ingress",
    "roles": ["admin"],
    "profile_id": "000000000000000000000000",
}


def get_webhook_system_token() -> dict:
    """Return synthetic system admin token for ingress writes."""
    return dict(WEBHOOK_SYSTEM_TOKEN)


def verify_secret_header(header_val: str | None, env_var_name: str) -> None:
    """Verify shared secret header against environment variable."""
    expected = os.environ.get(env_var_name)
    if expected:
        if not header_val or header_val != expected:
            raise HTTPUnauthorized(f"Invalid secret for {env_var_name}")


def verify_stripe_signature(
    raw_body: bytes,
    sig_header: str | None,
    tolerance: int = 300,
) -> bool:
    """
    Verify Stripe webhook signature header (t=...,v1=...).

    If STRIPE_WEBHOOK_VERIFY is 'false' or secret is unset, skips verification.
    """
    verify_enabled = os.environ.get("STRIPE_WEBHOOK_VERIFY", "false").lower() == "true"
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not verify_enabled or not secret:
        return True

    if not sig_header:
        raise HTTPUnauthorized("Missing Stripe-Signature header")

    try:
        elements = dict(item.strip().split("=", 1) for item in sig_header.split(","))
        timestamp = elements.get("t")
        signature = elements.get("v1")
        if not timestamp or not signature:
            raise HTTPUnauthorized("Malformed Stripe-Signature header")

        if abs(int(time.time()) - int(timestamp)) > tolerance:
            raise HTTPUnauthorized("Stripe webhook timestamp expired")

        signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
        expected_sig = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPUnauthorized("Stripe signature mismatch")
        return True
    except HTTPUnauthorized:
        raise
    except Exception as e:
        logger.error(f"Stripe signature verification error: {e}")
        raise HTTPUnauthorized("Stripe signature verification failed")
