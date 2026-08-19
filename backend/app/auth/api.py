import base64
import hashlib
import hmac
import json
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET  # noqa: N817
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from ninja import Router

from .authentication import JWTAuth

router = Router(tags=["Auth"])

# URI d'espace de noms XML fixe du protocole CAS (spec Yale/Apereo) —
# jamais résolue en réseau, ce n'est pas un endpoint.
_CAS_NS = {"cas": "http://www.yale.edu/tp/cas"}  # NOSONAR
# Fixed backend callback URL — never includes query params so it always matches
# what was registered with the CAS server.
CALLBACK_PATH = "/api/v1/auth/callback/"


# ── JWT helpers ────────────────────────────────────────────────────────────────


def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(payload: dict) -> str:
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


def _service_url() -> str:
    return settings.BACKEND_PUBLIC_URL.rstrip("/") + CALLBACK_PATH


# ── CAS XML parser ─────────────────────────────────────────────────────────────


def _parse_cas_xml(xml_text: str) -> dict | None:
    try:
        root = ET.fromstring(xml_text)
        success = root.find("cas:authenticationSuccess", _CAS_NS)
        if success is None:
            return None
        attrs_node = success.find("cas:attributes", _CAS_NS)
        attrs: dict[str, str] = {}
        if attrs_node is not None:
            for elem in attrs_node:
                tag = elem.tag.split("}")[-1]
                attrs[tag] = elem.text or ""
        # Fallback: use <cas:user> as email if no email attribute
        user_val = success.findtext("cas:user", namespaces=_CAS_NS) or ""
        attrs.setdefault("email", user_val)
        return attrs
    except ET.ParseError:
        return None


# ── Auth endpoints ─────────────────────────────────────────────────────────────


@router.get("/login/", auth=None)
def cas_login(request, next: str = "/"):
    """Redirect the browser to the CAS login page."""
    # Store the post-login destination in the session (avoids polluting service URL)
    request.session["auth_next"] = next
    service = _service_url()
    cas_url = (
        f"{settings.CAS_SERVER_PUBLIC_URL}/cas/login?service={quote(service, safe='')}"
    )
    return HttpResponseRedirect(cas_url)


@router.get("/callback/", auth=None)
def cas_callback(request, ticket: str):
    """
    CAS redirects here after successful login.
    Validates the ticket server-side, creates/syncs the Django user, issues a JWT,
    then redirects the browser to the frontend with the token.
    """
    next_url = request.session.pop("auth_next", "/")
    service = _service_url()
    frontend_url = settings.FRONTEND_PUBLIC_URL.rstrip("/")

    validate_url = (
        f"{settings.CAS_SERVER_INTERNAL_URL}/cas/serviceValidate"
        f"?service={quote(service, safe='')}&ticket={ticket}"
    )
    try:
        with urllib.request.urlopen(validate_url, timeout=5) as resp:
            xml_text = resp.read().decode("utf-8")
    except Exception:
        return HttpResponseRedirect(f"{frontend_url}/login?error=cas_unavailable")

    attrs = _parse_cas_xml(xml_text)
    if not attrs:
        return HttpResponseRedirect(f"{frontend_url}/login?error=invalid_ticket")

    # Create or sync Django user
    user_model = get_user_model()
    email = attrs.get("email", "")
    role = attrs.get("role", "student")
    ine = attrs.get("ine", "") or ""

    user, _ = user_model.objects.get_or_create(
        username=email,
        defaults={"email": email, "is_staff": role == "admin"},
    )
    is_staff = role == "admin"
    if user.is_staff != is_staff or user.email != email:
        user.is_staff = is_staff
        user.email = email
        user.save(update_fields=["is_staff", "email"])

    # Link student profile by INE
    if ine and role == "student":
        from app.students.models import Student

        Student.objects.filter(ine=ine).update(user=user)

    # Issue JWT (15-minute lifetime per rapport §3.4.7.3)
    now = int(time.time())
    token = _make_jwt(
        {
            "sub": email,
            "email": email,
            "role": role,
            "ine": ine,
            "iat": now,
            "exp": now + settings.JWT_EXPIRY_MINUTES * 60,
            "jti": str(uuid.uuid4()),
        }
    )

    # Redirect to frontend callback with token + original destination
    redirect = (
        f"{frontend_url}/auth/callback"
        f"?token={token}&next={quote(next_url, safe='/')}"
    )
    return HttpResponseRedirect(redirect)


@router.post("/refresh/", auth=JWTAuth())
def refresh_token(request):
    """Issue a new JWT for the currently authenticated user (silent renewal)."""
    payload = request.jwt_payload
    now = int(time.time())
    new_payload = {
        **payload,
        "iat": now,
        "exp": now + settings.JWT_EXPIRY_MINUTES * 60,
        "jti": str(uuid.uuid4()),
    }
    return {"token": _make_jwt(new_payload)}


@router.get("/me/", auth=JWTAuth())
def me(request):
    """Return the current user's identity and role."""
    # Read from `request.auth` — the User instance JWTAuth.authenticate() just
    # returned for this request — rather than `request.user` (populated by the
    # separate JWTMiddleware). Ninja guarantees `request.auth` is set to a real
    # user whenever this view runs (auth=JWTAuth() already rejected with 401
    # otherwise), so this can never see an AnonymousUser.
    user = request.auth
    return {
        "authenticated": True,
        "email": user.email,
        "role": "admin" if user.is_staff else "student",
        "ine": getattr(request, "user_ine", ""),
    }


@router.post("/logout/", auth=None)
def logout(request):
    """
    Returns the CAS logout URL. The frontend clears the local token and then
    redirects the browser to cas_logout_url to terminate the CAS session.
    """
    frontend_url = settings.FRONTEND_PUBLIC_URL.rstrip("/")
    cas_logout = (
        f"{settings.CAS_SERVER_PUBLIC_URL}/cas/logout"
        f"?service={quote(frontend_url + '/login', safe='')}"
    )
    return {"cas_logout_url": cas_logout}
