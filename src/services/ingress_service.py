"""
Ingress service for external payload normalization, hashing, and event recording.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from api_utils import Config
from src.services.event_service import EventService
from src.services.external_event_service import ExternalEventService

logger = logging.getLogger(__name__)


def compute_payload_hash(raw_payload: Any) -> str:
    """
    Compute a deterministic SHA-256 hash of the incoming raw payload.

    Supports bytes, str, or dict objects.
    """
    if isinstance(raw_payload, bytes):
        payload_bytes = raw_payload
    elif isinstance(raw_payload, str):
        payload_bytes = raw_payload.encode("utf-8")
    elif isinstance(raw_payload, dict):
        canonical_str = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"))
        payload_bytes = canonical_str.encode("utf-8")
    else:
        payload_bytes = str(raw_payload).encode("utf-8")

    return hashlib.sha256(payload_bytes).hexdigest()


def normalize_payload_body(raw_payload: Any) -> dict:
    """
    Normalize raw payload to a JSON-compatible dictionary without altering domain values.
    """
    if isinstance(raw_payload, dict):
        return raw_payload
    if isinstance(raw_payload, (bytes, bytearray)):
        raw_str = raw_payload.decode("utf-8", errors="replace")
    else:
        raw_str = str(raw_payload)

    try:
        parsed = json.loads(raw_str)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except Exception:
        return {"raw": raw_str}


class IngressService:
    """
    Orchestrates ingress write operations:
    - Normalizes payload metadata (SHA-256 hash)
    - Records append-only ExternalEvent
    - Enforces idempotency per (source, external_id)
    - Appends corresponding system Event
    """

    @classmethod
    def record_external_payload(
        cls,
        source: str,
        external_id: str,
        raw_payload: Any,
        token: dict,
        breadcrumb: dict,
        *,
        event_type: str | None = None,
        context: dict | None = None,
    ) -> dict:
        """
        Record an incoming external webhook/message payload idempotently.

        Args:
            source: Provider name ('stripe', 'cognito', etc.)
            external_id: Provider event or message ID
            raw_payload: Raw payload (bytes, str, or dict)
            token: Authentication token with ROLE_ADMIN
            breadcrumb: Breadcrumb dictionary
            event_type: Optional event type (defaults to external_received)
            context: Optional explicit context references for the event

        Returns:
            dict: Dictionary with 'external_event' and 'event'
        """
        config = Config.get_instance()
        if not event_type:
            event_type = config.EVENT_TYPE_EXTERNAL_RECEIVED

        # Idempotency check: see if already recorded
        existing = ExternalEventService.get_by_source_and_external_id(
            source, external_id
        )
        if existing:
            logger.info(
                f"Duplicate external event ignored: source={source}, external_id={external_id}"
            )
            return {
                "external_event": existing,
                "event": None,
                "idempotent": True,
            }

        payload_hash = compute_payload_hash(raw_payload)
        normalized_body = normalize_payload_body(raw_payload)

        external_event_data = {
            "source": source,
            "external_id": external_id,
            "payload_hash": payload_hash,
            "normalized_body": normalized_body,
        }

        try:
            created_external_event = ExternalEventService.create_external_event(
                external_event_data, token, breadcrumb
            )
        except Exception as e:
            # Check if concurrent write created the record
            existing = ExternalEventService.get_by_source_and_external_id(
                source, external_id
            )
            if existing:
                return {
                    "external_event": existing,
                    "event": None,
                    "idempotent": True,
                }
            raise e

        # Create corresponding domain Event
        event_data = {"type": event_type}
        created_event = EventService.create_event(
            event_data, token, breadcrumb, context=context
        )

        return {
            "external_event": created_external_event,
            "event": created_event,
            "idempotent": False,
        }
