"""
Unit tests for webhook transport & signature verification.
"""

import hmac
import hashlib
import time
import pytest
from api_utils.flask_utils.exceptions import HTTPUnauthorized
from src.services.webhook_transport import (
    get_webhook_system_token,
    verify_secret_header,
    verify_stripe_signature,
)


def test_get_webhook_system_token():
    token = get_webhook_system_token()
    assert token["user_id"] == "webhook-ingress"
    assert "admin" in token["roles"]


def test_verify_secret_header_no_env():
    # If env var not set, no check is enforced
    verify_secret_header(None, "NON_EXISTENT_VAR")


def test_verify_secret_header_matching(monkeypatch):
    monkeypatch.setenv("TEST_SECRET_VAR", "secret_123")
    verify_secret_header("secret_123", "TEST_SECRET_VAR")


def test_verify_secret_header_mismatch(monkeypatch):
    monkeypatch.setenv("TEST_SECRET_VAR", "secret_123")
    with pytest.raises(HTTPUnauthorized):
        verify_secret_header("wrong_secret", "TEST_SECRET_VAR")


def test_verify_stripe_signature_disabled(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_VERIFY", "false")
    # Should pass without header
    assert verify_stripe_signature(b"{}", None) is True


def test_verify_stripe_signature_success(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_VERIFY", "true")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

    now = int(time.time())
    raw_body = b'{"id":"evt_123"}'
    signed_payload = f"{now}.".encode("utf-8") + raw_body
    sig = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()
    header = f"t={now},v1={sig}"

    assert verify_stripe_signature(raw_body, header) is True


def test_verify_stripe_signature_mismatch(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_VERIFY", "true")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

    now = int(time.time())
    raw_body = b'{"id":"evt_123"}'
    header = f"t={now},v1=bad_signature"

    with pytest.raises(HTTPUnauthorized):
        verify_stripe_signature(raw_body, header)
