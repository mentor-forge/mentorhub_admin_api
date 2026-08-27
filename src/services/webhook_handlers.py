"""
Provider webhook event handlers (Stripe, Cognito, SMS).
"""

from __future__ import annotations

import logging
from typing import Any
from api_utils.flask_utils.exceptions import HTTPBadRequest
from src.services.identity_provisioning_service import IdentityProvisioningService
from src.services.ingress_service import IngressService

logger = logging.getLogger(__name__)


def handle_stripe(payload: dict, token: dict, breadcrumb: dict) -> dict:
    """Handle incoming Stripe event payload."""
    event_id = payload.get("id")
    if not event_id:
        raise HTTPBadRequest("Missing Stripe event ID")

    context_refs = {}
    data_obj = payload.get("data", {}).get("object", {})
    if "customer" in data_obj:
        context_refs["stripe_customer_id"] = data_obj["customer"]
    if "metadata" in data_obj and "customer_id" in data_obj["metadata"]:
        context_refs["customer_id"] = data_obj["metadata"]["customer_id"]

    return IngressService.record_external_payload(
        source="stripe",
        external_id=str(event_id),
        raw_payload=payload,
        token=token,
        breadcrumb=breadcrumb,
        context=context_refs if context_refs else None,
    )


def handle_cognito(payload: dict, token: dict, breadcrumb: dict) -> dict:
    """Handle incoming Cognito event payload (PostConfirmation or general)."""
    trigger = payload.get("triggerSource") or payload.get("trigger") or ""

    user_attrs = payload.get("request", {}).get("userAttributes", {}) or payload.get(
        "userAttributes", {}
    )
    email = user_attrs.get("email") or payload.get("email")
    name = user_attrs.get("name") or payload.get("name")
    client_metadata = payload.get("request", {}).get(
        "clientMetadata", {}
    ) or payload.get("clientMetadata", {})
    org_name = (
        client_metadata.get("organization_name")
        or payload.get("organization_name")
        or ""
    )
    customer_id = client_metadata.get("customer_id") or payload.get("customer_id")
    sub = (
        user_attrs.get("sub") or payload.get("userName") or payload.get("sub") or email
    )

    if "PostConfirmation" in trigger or payload.get("trigger") == "PostConfirmation":
        if customer_id:
            # Invitee under existing organization
            return IdentityProvisioningService.provision_invitee(
                customer_id=customer_id,
                email=email,
                name=name,
                token=token,
                breadcrumb=breadcrumb,
                external_ids={"sub": str(sub)},
                source="cognito",
                raw_payload=payload,
            )
        else:
            # Primary organization owner
            return IdentityProvisioningService.provision_primary(
                email=email,
                name=name,
                organization_name=org_name or f"{email.split('@')[0]}'s Organization",
                token=token,
                breadcrumb=breadcrumb,
                external_ids={"sub": str(sub)},
                source="cognito",
                raw_payload=payload,
            )

    # General Cognito audit event
    event_id = sub or f"cognito-{email}"
    return IngressService.record_external_payload(
        source="cognito",
        external_id=str(event_id),
        raw_payload=payload,
        token=token,
        breadcrumb=breadcrumb,
    )


def handle_sms(payload: dict, token: dict, breadcrumb: dict) -> dict:
    """Handle incoming SMS payload."""
    message_id = payload.get("message_id") or payload.get("id")
    if not message_id:
        raise HTTPBadRequest("Missing SMS message ID")

    return IngressService.record_external_payload(
        source="sms",
        external_id=str(message_id),
        raw_payload=payload,
        token=token,
        breadcrumb=breadcrumb,
    )
