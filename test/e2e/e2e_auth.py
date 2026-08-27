"""E2E Bearer JWT for black-box API tests (Developer Edition persona defaults).

Uses JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE, and JWT_ALGORITHM from the
environment when set.
"""

from __future__ import annotations

import os
import time
import jwt

_DEFAULT_JWT_SECRET = "local-dev-jwt-secret-fixed"
_DEFAULT_JWT_ISSUER = "dev-idp"
_DEFAULT_JWT_AUDIENCE = "dev-api"
_DEFAULT_JWT_ALGORITHM = "HS256"

_E2E_SUBJECT = "adam"
_E2E_ROLES = ("admin",)
_E2E_PROFILE_ID = "A00000000000000000000001"


def get_auth_token(**claims) -> str:
    """
    Mint a short-lived admin persona JWT for black-box tests.

    Keyword arguments override or add payload claims.
    """
    secret = os.environ.get("JWT_SECRET") or _DEFAULT_JWT_SECRET
    issuer = os.environ.get("JWT_ISSUER") or _DEFAULT_JWT_ISSUER
    audience = os.environ.get("JWT_AUDIENCE") or _DEFAULT_JWT_AUDIENCE
    algorithm = os.environ.get("JWT_ALGORITHM") or _DEFAULT_JWT_ALGORITHM
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": _E2E_SUBJECT,
        "iat": now,
        "exp": now + 10 * 365 * 24 * 60 * 60,
        "roles": list(_E2E_ROLES),
        "profile_id": _E2E_PROFILE_ID,
    }
    payload.update(claims)
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token
