"""Helpers for tests that need JWT authentication."""

import base64
import hashlib
import hmac
import json
import time
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_test_jwt(
    email: str = "admin@n7.fr",
    role: str = "admin",
    ine: str = "",
    expiry_seconds: int = 3600,
) -> str:
    """Generate a signed JWT for use in tests."""
    now = int(time.time())
    payload = {
        "sub": email,
        "email": email,
        "role": role,
        "ine": ine,
        "iat": now,
        "exp": now + expiry_seconds,
        "jti": str(uuid.uuid4()),
    }
    header = _b64_url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    )
    body = _b64_url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        f"{header}.{body}".encode(),
        hashlib.sha256,
    ).digest()
    return f"{header}.{body}.{_b64_url_encode(sig)}"


def make_admin_user(email: str = "admin@n7.fr") -> "User":  # type: ignore[name-defined]
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "is_staff": True},
    )
    return user


def make_student_user(
    email: str = "etudiant@etud.n7.fr", ine: str = "1234567890A"
) -> "User":  # type: ignore[name-defined]
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "is_staff": False},
    )
    return user


def auth_header(email: str = "admin@n7.fr", role: str = "admin", ine: str = "") -> dict:
    """Return the Authorization header dict for use with Django's test client."""
    token = make_test_jwt(email=email, role=role, ine=ine)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
