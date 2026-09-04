"""
Identity and Customer provisioning orchestration service for Mentor Hub Admin API.
"""

from __future__ import annotations

import logging
from typing import Any
from bson import ObjectId

from api_utils import Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPInternalServerError
from api_utils.services.rbac import is_admin
from src.services.customer_service import CustomerService
from src.services.event_service import EventService
from src.services.ingress_service import IngressService
from src.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

ALLOWED_ROLES = {"admin", "coordinator", "customer", "mentee", "mentor"}


class IdentityProvisioningService:
    """
    Orchestrates initial account identity provisioning:
    - provision_primary: Creates initial Customer organization shell and primary owner Profile
    - provision_invitee: Creates a Profile under an existing Customer
    - Records Ingress ExternalEvent and system Event with context references
    - Idempotent on email lookup
    """

    @classmethod
    def _check_permission(cls, token: dict) -> None:
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def provision_primary(
        cls,
        email: str,
        name: str | None,
        organization_name: str,
        token: dict,
        breadcrumb: dict,
        *,
        roles: list[str] | None = None,
        external_ids: dict[str, str] | None = None,
        source: str | None = None,
        raw_payload: Any = None,
    ) -> dict:
        """
        Provision primary owner Profile and paired Customer shell.

        Returns:
            dict: {"profile": profile_doc, "customer": customer_doc, "idempotent": bool}
        """
        cls._check_permission(token)

        # Idempotency check: see if profile already exists for email
        existing_profile = ProfileService.get_by_email(email)
        if existing_profile:
            customer_id = existing_profile.get("customer_id")
            existing_customer = None
            if customer_id:
                try:
                    existing_customer = CustomerService.get_customer(
                        str(customer_id), token, breadcrumb
                    )
                except Exception:
                    existing_customer = None

            logger.info(
                f"Provisioning identity already exists for {email}, returning existing account."
            )
            return {
                "profile": existing_profile,
                "customer": existing_customer,
                "idempotent": True,
            }

        config = Config.get_instance()

        try:
            # 1. Create Customer organization shell
            customer_data = {
                "name": organization_name or f"{email.split('@')[0]}'s Organization",
                "status": "provisioned",
            }
            customer_doc = CustomerService.create_provisioned_customer(
                customer_data, token, breadcrumb
            )

            # 2. Create paired primary Profile
            if roles:
                filtered_roles = [r for r in roles if r in ALLOWED_ROLES]
            else:
                filtered_roles = ["admin"]
            if not filtered_roles:
                filtered_roles = ["admin"]

            profile_data = {
                "email": email,
                "roles": filtered_roles,
                "customer_id": customer_doc["_id"],
                "status": "provisioned",
            }
            if name:
                profile_data["display_name"] = str(name)[:255]
            if external_ids and "sub" in external_ids:
                profile_data["cognito_sub"] = str(external_ids["sub"])[:40]

            created_profile = ProfileService.create_profile(
                profile_data, token, breadcrumb
            )

            # 3. Record Ingress Event & Audit with context refs
            event_type = getattr(
                config,
                "EVENT_TYPE_IDENTITY_PROVISIONED",
                "identity_provisioned",
            )
            context_refs = {
                "profile_id": created_profile["_id"],
                "customer_id": customer_doc["_id"],
            }

            ext_id = None
            if external_ids:
                ext_id = external_ids.get("external_id") or external_ids.get("sub")
            if not ext_id and source:
                ext_id = f"{source}:{email}"

            if source and ext_id:
                IngressService.record_external_payload(
                    source=source,
                    external_id=ext_id,
                    raw_payload=raw_payload
                    or {
                        "email": email,
                        "organization_name": organization_name,
                    },
                    token=token,
                    breadcrumb=breadcrumb,
                    event_type=event_type,
                    context=context_refs,
                )
            else:
                EventService.create_event(
                    {"type": event_type},
                    token,
                    breadcrumb,
                    context=context_refs,
                )

            logger.info(
                f"Successfully provisioned primary identity: profile={created_profile['_id']}, customer={customer_doc['_id']}"
            )
            return {
                "profile": created_profile,
                "customer": customer_doc,
                "idempotent": False,
            }
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Error provisioning primary identity for {email}: {error_msg}"
            )
            raise HTTPInternalServerError(
                f"Failed to provision primary identity: {error_msg}"
            )

    @classmethod
    def provision_invitee(
        cls,
        customer_id: str | ObjectId,
        email: str,
        name: str | None,
        token: dict,
        breadcrumb: dict,
        *,
        roles: list[str] | None = None,
        external_ids: dict[str, str] | None = None,
        source: str | None = None,
        raw_payload: Any = None,
    ) -> dict:
        """
        Provision an invitee Profile under an existing Customer.

        Returns:
            dict: {"profile": profile_doc, "customer": customer_doc, "idempotent": bool}
        """
        cls._check_permission(token)

        # Verify existing Customer
        customer_doc = CustomerService.get_customer(str(customer_id), token, breadcrumb)

        # Idempotency check: see if profile already exists for email
        existing_profile = ProfileService.get_by_email(email)
        if existing_profile:
            logger.info(
                f"Invitee profile already exists for {email}, returning existing."
            )
            return {
                "profile": existing_profile,
                "customer": customer_doc,
                "idempotent": True,
            }

        config = Config.get_instance()

        try:
            if roles:
                filtered_roles = [r for r in roles if r in ALLOWED_ROLES]
            else:
                filtered_roles = ["mentee"]
            if not filtered_roles:
                filtered_roles = ["mentee"]

            profile_data = {
                "email": email,
                "roles": filtered_roles,
                "customer_id": ObjectId(str(customer_id)),
                "status": "provisioned",
            }
            if name:
                profile_data["display_name"] = str(name)[:255]
            if external_ids and "sub" in external_ids:
                profile_data["cognito_sub"] = str(external_ids["sub"])[:40]

            created_profile = ProfileService.create_profile(
                profile_data, token, breadcrumb
            )

            event_type = getattr(
                config,
                "EVENT_TYPE_IDENTITY_PROVISIONED",
                "identity_provisioned",
            )
            context_refs = {
                "profile_id": created_profile["_id"],
                "customer_id": ObjectId(str(customer_id)),
            }

            ext_id = None
            if external_ids:
                ext_id = external_ids.get("external_id") or external_ids.get("sub")
            if not ext_id and source:
                ext_id = f"{source}:{email}"

            if source and ext_id:
                IngressService.record_external_payload(
                    source=source,
                    external_id=ext_id,
                    raw_payload=raw_payload
                    or {"email": email, "customer_id": str(customer_id)},
                    token=token,
                    breadcrumb=breadcrumb,
                    event_type=event_type,
                    context=context_refs,
                )
            else:
                EventService.create_event(
                    {"type": event_type},
                    token,
                    breadcrumb,
                    context=context_refs,
                )

            logger.info(
                f"Successfully provisioned invitee profile {created_profile['_id']} for customer {customer_id}"
            )
            return {
                "profile": created_profile,
                "customer": customer_doc,
                "idempotent": False,
            }
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error provisioning invitee for {email}: {error_msg}")
            raise HTTPInternalServerError(f"Failed to provision invitee: {error_msg}")
