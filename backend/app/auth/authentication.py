import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.errors import HttpError
from ninja.security import HttpBearer

User = get_user_model()


def _b64_url_decode(segment: str) -> bytes:
    padding = (4 - len(segment) % 4) % 4
    return base64.urlsafe_b64decode(segment + "=" * padding)


def verify_jwt(token: str) -> dict | None:
    """Verify HS256 JWT signature and expiry. Returns payload or None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        expected = hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            f"{h}.{p}".encode(),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _b64_url_decode(s)):
            return None
        payload = json.loads(_b64_url_decode(p))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


class JWTAuth(HttpBearer):
    """Django Ninja authenticator: reads Authorization: Bearer <token>.

    Falls back to the `auth_token` cookie when no Bearer header is present —
    the frontend relies on this fallback (see lib/auth.ts), and the Bearer
    header always takes priority when both are present.
    """

    def __call__(self, request):
        result = super().__call__(request)
        if result is not None:
            return result
        cookie_token = request.COOKIES.get("auth_token")
        if not cookie_token:
            return None
        return self.authenticate(request, cookie_token)

    def authenticate(self, request, token: str):
        payload = verify_jwt(token)
        if not payload:
            return None

        email = payload.get("email", "")
        role = payload.get("role", "student")
        ine = payload.get("ine", "") or ""

        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "is_staff": role == "admin"},
        )
        if not created:
            is_staff = role == "admin"
            if user.is_staff != is_staff or user.email != email:
                user.is_staff = is_staff
                user.email = email
                user.save(update_fields=["is_staff", "email"])

        # Link student profile on first authenticated request
        if ine and role == "student":
            from app.students.models import Student

            Student.objects.filter(ine=ine).update(user=user)

        request.jwt_payload = payload
        request.user_role = role
        request.user_ine = ine
        return user


class AdminJWTAuth(JWTAuth):
    """Django Ninja authenticator: valid JWT AND role=admin, else 403.

    Used as router/operation-level `auth=` to restrict entire routers (or
    individual endpoints) to administrators without needing a separate
    per-view decorator. Raising HttpError from authenticate() (rather than
    returning None) lets Ninja return 403 instead of the generic 401 that
    a failed authentication would produce.
    """

    def authenticate(self, request, token: str):
        user = super().authenticate(request, token)
        if user is None:
            return None
        if not user.is_staff:
            raise HttpError(403, "Accès réservé aux administrateurs RI")
        return user
