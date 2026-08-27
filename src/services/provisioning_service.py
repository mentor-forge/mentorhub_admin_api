"""
Identity and Customer provisioning service for Mentor Hub Admin API.
"""

from __future__ import annotations

import logging
from typing import Any
from bson import ObjectId

from api_utils import Config, MongoIO
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPInternalServerError
from api_utils.mongo_utils import encode_document
from api_utils.services.rbac import is_admin
from src.services.customer_service import CustomerService
from src.services.event_service import EventService
from src.services.ingress_service import IngressService
from src.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id", "customer_id"]
DATE_PROPERTIES = []


class ProvisioningService:
    """
    Orchestrates initial account identity provisioning:
    - Creates initial Customer organization shell
    - Creates paired primary Profile
    - Records Ingress ExternalEvent and system Event with context references
    - Idempotent on email lookup
    """

    @classmethod
    def _check_permission(cls, token: dict) -> None:
        if not is_admin(token):
            raise HTTPForbidden("Admin role required")

    @classmethod
    def provision_identity(
        cls,
        email: str,
        organization_name: str,
        token: dict,
        breadcrumb: dict,
        *,
        name: str | None = None,
        roles: list[str] | None = None,
        source: str | None = None,
        external_id: str | None = None,
        raw_payload: Any = None,
    ) -> dict:
        """
        Provision initial Customer shell and initial Profile for an account.

        Args:
            email: Primary email for the account
            organization_name: Name of the organization
            token: Authenticated admin or system token
            breadcrumb: Breadcrumb dictionary
            name: Optional display name for the profile
            roles: Roles list (defaults to ["admin", "member"])
            source: Ingress source if triggered by external event ('cognito', etc.)
            external_id: Ingress provider event ID
            raw_payload: Raw external payload if triggered by ingress

        Returns:
            dict: Dictionary with 'profile', 'customer', and 'idempotent'
        """
        cls._check_permission(token)

        # 1. Idempotency check: see if profile already exists for email
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

        mongo = MongoIO.get_instance()
        config = Config.get_instance()

        try:
            # 2. Create Customer organization shell
            customer_data = {
                "name": organization_name or f"{email.split('@')[0]}'s Organization",
                "status": "active",
                "created": breadcrumb,
                "saved": breadcrumb,
            }
            encode_document(customer_data, ID_PROPERTIES, DATE_PROPERTIES)
            customer_id = mongo.create_document(
                config.CUSTOMER_COLLECTION_NAME, customer_data
            )
            customer_data["_id"] = ObjectId(customer_id)

            # 3. Create paired primary Profile
            profile_roles = roles or ["admin", "member"]
            profile_data = {
                "email": email,
                "name": name or email.split("@")[0].replace(".", " ").title(),
                "roles": profile_roles,
                "customer_id": customer_data["_id"],
                "status": "active",
            }
            created_profile = ProfileService.create_profile(
                profile_data, token, breadcrumb
            )

            # 4. Record Ingress Event & Audit with context refs
            event_type = getattr(
                config,
                "EVENT_TYPE_IDENTITY_PROVISIONED",
                "identity_provisioned",
            )
            context_refs = {
                "profile_id": created_profile["_id"],
                "customer_id": customer_data["_id"],
            }

            if source and external_id:
                IngressService.record_external_payload(
                    source=source,
                    external_id=external_id,
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
                f"Successfully provisioned identity: profile={created_profile['_id']}, customer={customer_data['_id']}"
            )
            return {
                "profile": created_profile,
                "customer": customer_data,
                "idempotent": False,
            }
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error provisioning identity for {email}: {error_msg}")
            raise HTTPInternalServerError(f"Failed to provision identity: {error_msg}")
