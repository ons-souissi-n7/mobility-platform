"""
Tests de sécurité — BNF02 : Authentification JWT & Contrôle d'accès basé sur les rôles (RBAC).

Couvre :
- Accès sans token → 401
- Token expiré → 401
- Token altéré (signature invalide) → 401
- Étudiant accède aux endpoints admin → 403
- Étudiant accède aux données d'un autre étudiant → 403
- Admin accède aux endpoints admin → 200/OK
- Admin accède aux endpoints étudiant → 200/OK (droit de supervision)
- Token dans l'en-tête Authorization (Bearer) ET dans le cookie
- Logout CAS retourne l'URL de déconnexion
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from app.academic.models import AcademicYear
from app.auth.test_utils import make_test_jwt
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_year():
    return AcademicYear.objects.create(
        label="2025-2026",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 7, 1),
    )


def _make_student(ine: str = "1234567890A") -> Student:
    student = Student.objects.create(ine=ine, first_name="Marie", last_name="Curie")
    User.objects.get_or_create(
        username=f"{ine}@etud.n7.fr",
        defaults={"email": f"{ine}@etud.n7.fr", "is_staff": False},
    )
    return student


def _tampered_token(original_token: str) -> str:
    """Return a token whose signature has been corrupted."""
    parts = original_token.split(".")
    corrupted_sig = base64.urlsafe_b64encode(b"X" * 32).rstrip(b"=").decode()
    return f"{parts[0]}.{parts[1]}.{corrupted_sig}"


def _expired_token(role: str = "admin", ine: str = "") -> str:
    """Return a token expired 60 seconds ago."""
    return make_test_jwt(role=role, ine=ine, expiry_seconds=-60)


# ---------------------------------------------------------------------------
# BNF02-SEC-01 : Accès sans token → 401
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Tous les endpoints protégés refusent les requêtes sans token (401)."""

    def setup_method(self):
        # Bypass auto-inject: use a client with NO authorization header
        self.client = Client()  # autouse fixture adds default bearer; override below

    def _anon_client(self) -> Client:
        """Client sans aucun en-tête Authorization."""
        return Client(HTTP_AUTHORIZATION="")

    def test_students_list_requires_auth(self):
        response = self._anon_client().get("/api/v1/students/students/")
        assert response.status_code == 401

    def test_agreements_list_requires_auth(self):
        response = self._anon_client().get("/api/v1/mobility/agreements/")
        assert response.status_code == 401

    def test_academic_years_requires_auth(self):
        response = self._anon_client().get("/api/v1/academic/years/")
        assert response.status_code == 401

    def test_audit_logs_requires_auth(self):
        response = self._anon_client().get("/api/v1/audit/logs/")
        assert response.status_code == 401

    def test_outgoing_assignments_requires_auth(self):
        response = self._anon_client().get("/api/v1/outgoing/assignments/")
        assert response.status_code == 401

    def test_reference_countries_requires_auth(self):
        response = self._anon_client().get("/api/v1/reference/countries/")
        assert response.status_code == 401

    def test_analytics_requires_auth(self):
        response = self._anon_client().get("/api/v1/analytics/trends/")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# BNF02-SEC-02 : Token expiré → 401
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExpiredToken:
    """Un token JWT expiré est rejeté avec 401."""

    def test_expired_admin_token_rejected(self):
        token = _expired_token(role="admin")
        client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/students/students/")
        assert response.status_code == 401, "Token expiré doit être refusé"

    def test_expired_student_token_rejected(self):
        token = _expired_token(role="student", ine="1234567890A")
        client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/student/1234567890A/profile/")
        assert response.status_code == 401, "Token étudiant expiré doit être refusé"


# ---------------------------------------------------------------------------
# BNF02-SEC-03 : Token altéré (signature invalide) → 401
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTamperedToken:
    """Un token avec une signature modifiée est rejeté avec 401."""

    def test_tampered_signature_rejected(self):
        valid = make_test_jwt(role="admin")
        token = _tampered_token(valid)
        client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/students/students/")
        assert response.status_code == 401, "Token altéré doit être refusé"

    def test_wrong_secret_rejected(self):
        """Token signé avec un autre secret doit être rejeté."""
        now = int(time.time())
        payload = {
            "sub": "admin@n7.fr",
            "email": "admin@n7.fr",
            "role": "admin",
            "iat": now,
            "exp": now + 3600,
        }

        def b64e(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = b64e(json.dumps(payload).encode())
        sig = hmac.new(
            b"wrong-secret", f"{header}.{body}".encode(), hashlib.sha256
        ).digest()
        token = f"{header}.{body}.{b64e(sig)}"

        client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get("/api/v1/students/students/")
        assert response.status_code == 401

    def test_malformed_token_rejected(self):
        """Token malformé (pas 3 segments) doit être rejeté."""
        for bad in ["notavalidtoken", "a.b", "a.b.c.d"]:
            client = Client(HTTP_AUTHORIZATION=f"Bearer {bad}")
            response = client.get("/api/v1/students/students/")
            assert (
                response.status_code == 401
            ), f"Token malformé «{bad}» devrait être refusé"

    def test_payload_role_elevation_rejected(self):
        """Un étudiant qui altère son role='admin' dans le payload est rejeté."""
        # Construire un token avec role=admin mais signature student
        student_token = make_test_jwt(role="student", ine="1234567890A")
        parts = student_token.split(".")
        # Remplacer le payload par role=admin
        now = int(time.time())
        evil_payload = {
            "sub": "etud@n7.fr",
            "email": "etud@n7.fr",
            "role": "admin",
            "ine": "1234567890A",
            "iat": now,
            "exp": now + 3600,
        }
        evil_body = (
            base64.urlsafe_b64encode(json.dumps(evil_payload).encode())
            .rstrip(b"=")
            .decode()
        )
        evil_token = f"{parts[0]}.{evil_body}.{parts[2]}"
        client = Client(HTTP_AUTHORIZATION=f"Bearer {evil_token}")
        response = client.get("/api/v1/students/students/")
        assert (
            response.status_code == 401
        ), "Élévation de rôle par altération de payload doit être refusée"


# ---------------------------------------------------------------------------
# BNF02-SEC-04 : RBAC — Étudiant ne peut pas accéder aux endpoints admin
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStudentCannotAccessAdminEndpoints:
    """Un étudiant reçoit 403 sur tous les endpoints réservés à l'admin."""

    def setup_method(self):
        self.student_token = make_test_jwt(
            email="etudiant@etud.n7.fr", role="student", ine="1234567890A"
        )
        self.client = Client(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

    def test_student_cannot_list_students(self):
        response = self.client.get("/api/v1/students/students/")
        assert response.status_code == 403

    def test_student_cannot_list_agreements(self):
        response = self.client.get("/api/v1/mobility/agreements/")
        assert response.status_code == 403

    def test_student_cannot_manage_academic_years(self):
        response = self.client.get("/api/v1/academic/years/")
        assert response.status_code == 403

    def test_student_cannot_access_outgoing_assignments(self):
        response = self.client.get("/api/v1/outgoing/assignments/")
        assert response.status_code == 403

    def test_student_cannot_read_audit_logs(self):
        response = self.client.get("/api/v1/audit/logs/")
        assert response.status_code == 403

    def test_student_cannot_access_analytics(self):
        response = self.client.get("/api/v1/analytics/trends/")
        assert response.status_code == 403

    def test_student_cannot_manage_mobility_categories(self):
        response = self.client.get("/api/v1/mobility/agreement-categories/")
        assert response.status_code == 403

    def test_student_cannot_access_cti_export(self):
        response = self.client.get("/api/v1/cti/stats/?academic_year_id=1")
        assert response.status_code == 403

    def test_student_cannot_create_academic_year(self):
        response = self.client.post(
            "/api/v1/academic/years/",
            data={"label": "2099-2100"},
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_student_cannot_delete_student(self):
        # Il n'existe pas d'endpoint de suppression directe d'un étudiant (seule
        # l'anonymisation RGPD existe côté admin) — on vérifie le RBAC sur la
        # suppression d'inscription, l'action de suppression réellement exposée
        # par le routeur admin `students`.
        response = self.client.delete("/api/v1/students/students/enrollments/9999/")
        assert response.status_code == 403

    def test_student_cannot_access_alerts(self):
        response = self.client.get("/api/v1/alerts/")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# BNF02-SEC-05 : RBAC — Étudiant ne peut accéder qu'à ses propres données
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStudentOwnership:
    """Un étudiant peut accéder à son propre dossier mais pas à celui d'un autre."""

    def setup_method(self):
        self.year = _make_year()
        dept = Department.objects.create(code="SN", name="Sciences")
        level = Level.objects.create(code="3A", name="3ème année")
        Country.objects.create(
            iso2="FR", name_fr="France", name_en="France", cti_region=CTIRegion.FRANCE
        )

        self.student_a = _make_student("AAAAAAAAAA1")
        self.student_b = _make_student("BBBBBBBBBB2")

        # Enrollment pour student_a
        AnnualEnrollment.objects.create(
            student=self.student_a,
            academic_year=self.year,
            department=dept,
            level=level,
        )

        self.token_a = make_test_jwt(
            email="AAAAAAAAAA1@etud.n7.fr", role="student", ine="AAAAAAAAAA1"
        )
        self.client_a = Client(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")

    def test_student_can_access_own_profile(self):
        response = self.client_a.get("/api/v1/student/AAAAAAAAAA1/profile/")
        assert response.status_code in (200, 404)  # 404 si pas de profil complet

    def test_student_cannot_access_other_student_profile(self):
        response = self.client_a.get("/api/v1/student/BBBBBBBBBB2/profile/")
        assert response.status_code == 403

    def test_student_cannot_access_other_student_wishes(self):
        response = self.client_a.get("/api/v1/student/BBBBBBBBBB2/wishes/")
        assert response.status_code == 403

    def test_student_cannot_access_other_student_assignment(self):
        response = self.client_a.get("/api/v1/student/BBBBBBBBBB2/assignment/")
        assert response.status_code == 403

    def test_student_cannot_access_other_complementary(self):
        response = self.client_a.get("/api/v1/complementary/student/BBBBBBBBBB2/")
        assert response.status_code == 403

    def test_admin_can_access_any_student_profile(self):
        admin_client = Client()  # token admin injecté par la fixture autouse
        response = admin_client.get("/api/v1/student/AAAAAAAAAA1/profile/")
        assert response.status_code in (200, 404)


# ---------------------------------------------------------------------------
# BNF02-SEC-06 : Admin accède correctement à tous les endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminAccess:
    """Un administrateur peut accéder à tous les endpoints admin (200)."""

    def setup_method(self):
        self.client = Client()  # admin JWT injecté par autouse fixture

    def test_admin_can_list_students(self):
        response = self.client.get("/api/v1/students/students/")
        assert response.status_code == 200

    def test_admin_can_list_agreements(self):
        response = self.client.get("/api/v1/mobility/agreements/")
        assert response.status_code == 200

    def test_admin_can_list_academic_years(self):
        response = self.client.get("/api/v1/academic/years/")
        assert response.status_code == 200

    def test_admin_can_read_audit_logs(self):
        response = self.client.get("/api/v1/audit/logs/")
        assert response.status_code == 200

    def test_admin_can_read_alerts(self):
        response = self.client.get("/api/v1/alerts/")
        assert response.status_code == 200

    def test_admin_can_read_reference_data(self):
        for endpoint in [
            "/api/v1/reference/countries/",
            "/api/v1/reference/departments/",
            "/api/v1/reference/levels/",
            "/api/v1/reference/parcours/",
        ]:
            response = self.client.get(endpoint)
            assert (
                response.status_code == 200
            ), f"Admin doit pouvoir accéder à {endpoint}"


# ---------------------------------------------------------------------------
# BNF02-SEC-07 : Token via cookie (fallback frontend)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAuth:
    """Le token peut être transmis via le cookie auth_token (fallback Next.js)."""

    def test_valid_cookie_grants_access(self):
        token = make_test_jwt(role="admin")
        client = Client(HTTP_AUTHORIZATION="")
        client.cookies["auth_token"] = token
        response = client.get("/api/v1/reference/countries/")
        assert response.status_code == 200

    def test_expired_cookie_denied(self):
        token = _expired_token(role="admin")
        client = Client(HTTP_AUTHORIZATION="")
        client.cookies["auth_token"] = token
        response = client.get("/api/v1/reference/countries/")
        assert response.status_code == 401

    def test_bearer_header_takes_priority_over_cookie(self):
        """Si les deux sont présents, l'en-tête Bearer prend la priorité."""
        valid_admin_token = make_test_jwt(role="admin")
        expired_cookie_token = _expired_token(role="admin")
        client = Client(HTTP_AUTHORIZATION=f"Bearer {valid_admin_token}")
        client.cookies["auth_token"] = expired_cookie_token
        response = client.get("/api/v1/reference/countries/")
        # Doit être 200 car le Bearer est valide
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# BNF02-SEC-08 : Endpoint public auth ne nécessite pas de token
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPublicAuthEndpoints:
    """/auth/login/ est public et déclenche la redirection CAS."""

    def test_login_redirects_to_cas(self):
        client = Client(HTTP_AUTHORIZATION="")
        response = client.get("/api/v1/auth/login/")
        assert response.status_code == 302
        assert (
            "cas" in response["Location"].lower()
            or "login" in response["Location"].lower()
        )

    def test_logout_returns_cas_url(self):
        client = Client()  # admin jwt
        response = client.post("/api/v1/auth/logout/")
        assert response.status_code == 200
        assert "cas_logout_url" in response.json()

    def test_me_returns_current_user(self):
        client = Client()  # admin jwt
        response = client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["role"] == "admin"
