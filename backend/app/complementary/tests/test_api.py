"""Tests d'intégration pour l'API mobilités complémentaires."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.testing import TestClient

from app.academic.models import AcademicYear
from app.complementary.api import router
from app.complementary.models import ComplementaryMobility, MobilityStatus
from app.reference.models import Country, CTIRegion
from app.students.models import Student


@pytest.fixture
def client():
    from app.auth.test_utils import make_test_jwt

    token = make_test_jwt(role="admin")
    return TestClient(router, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def country(db):
    return Country.objects.create(
        iso2="DE",
        name_fr="Allemagne",
        name_en="Germany",
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )


@pytest.fixture
def academic_year(db):
    return AcademicYear.objects.create(
        label="2026-2027",
        start_date=date(2026, 9, 1),
        end_date=date(2027, 8, 31),
    )


@pytest.fixture
def student(db):
    return Student.objects.create(
        ine="1234567890A",
        first_name="Alice",
        last_name="Durand",
        email="alice@example.com",
    )


@pytest.fixture
def pending_mobility(student, country, academic_year):
    return ComplementaryMobility.objects.create(
        student=student,
        academic_year=academic_year,
        experience_type="Summer school",
        destination_country=country,
        destination_institution="TU Berlin",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 8, 31),
        document_key="complementary/abc123.pdf",
        document_name="justificatif.pdf",
    )


def _pdf_file(name="doc.pdf", size=512, content_type="application/pdf"):
    data = b"%PDF" + b"0" * (size - 4)
    return SimpleUploadedFile(name, data, content_type=content_type)


def _declare_url(ine: str, **overrides) -> str:
    params = {
        "academic_year_id": "1",
        "experience_type": "Summer school",
        "country_id": "1",
        "destination_institution": "UPM",
        "start_date": "2026-06-01",
        "end_date": "2026-08-30",
    }
    params.update({k: str(v) for k, v in overrides.items()})
    return f"/student/{ine}/?{urlencode(params)}"


# ── List student mobilities ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestListStudentMobilities:
    def test_returns_404_for_unknown_ine(self, client):
        response = client.get("/student/ZZZZZZZZZZZ/")
        assert response.status_code == 404

    def test_returns_empty_list_for_student_with_no_submissions(self, client, student):
        response = client.get(f"/student/{student.ine}/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_submissions(self, client, pending_mobility, student):
        response = client.get(f"/student/{student.ine}/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["experience_type"] == "Summer school"
        assert data[0]["status"] == MobilityStatus.PENDING
        assert data[0]["destination_country_name"] == "Allemagne"
        assert data[0]["student_ine"] == student.ine


# ── List all mobilities (admin) ───────────────────────────────────────────────


@pytest.mark.django_db
class TestListAllMobilities:
    def test_returns_all_mobilities(self, client, pending_mobility):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1

    def test_includes_student_fields(self, client, pending_mobility, student):
        results = client.get("/").json()["results"]
        assert results[0]["student_ine"] == student.ine
        assert results[0]["student_first_name"] == student.first_name
        assert results[0]["student_last_name"] == student.last_name

    def test_filters_by_status_pending(self, client, pending_mobility):
        assert client.get("/?status=pending").json()["count"] == 1
        assert client.get("/?status=validated").json()["count"] == 0

    def test_filters_by_student_search_last_name(
        self, client, pending_mobility, student
    ):
        assert client.get(f"/?student_search={student.last_name}").json()["count"] == 1
        assert client.get("/?student_search=Inconnu").json()["count"] == 0

    def test_filters_by_student_search_ine(self, client, pending_mobility, student):
        assert client.get(f"/?student_search={student.ine}").json()["count"] == 1

    def test_filters_by_experience_type(self, client, pending_mobility):
        assert client.get("/?experience_type=summer").json()["count"] == 1
        assert client.get("/?experience_type=stage").json()["count"] == 0

    def test_filters_by_year_id(self, client, pending_mobility, academic_year):
        assert client.get(f"/?year_id={academic_year.pk}").json()["count"] == 1
        assert client.get("/?year_id=99999").json()["count"] == 0

    def test_pagination_structure(self, client, pending_mobility):
        data = client.get("/?page=1&page_size=10").json()
        assert "count" in data
        assert "page" in data
        assert "page_size" in data
        assert "results" in data
        assert data["page"] == 1
        assert data["page_size"] == 10


# ── Declare mobility ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestDeclareMobility:
    def test_returns_404_for_unknown_student(self, client, country, academic_year):
        with patch("app.complementary.api.upload_document", return_value="k/x.pdf"):
            response = client.post(
                _declare_url(
                    "ZZZZZZZZZZZ",
                    academic_year_id=academic_year.pk,
                    country_id=country.pk,
                ),
                FILES={"document": _pdf_file()},
            )
        assert response.status_code == 404

    def test_returns_400_for_empty_experience_type(
        self, client, student, country, academic_year
    ):
        with patch("app.complementary.api.upload_document", return_value="k/x.pdf"):
            response = client.post(
                _declare_url(
                    student.ine,
                    academic_year_id=academic_year.pk,
                    country_id=country.pk,
                    experience_type="   ",
                ),
                FILES={"document": _pdf_file()},
            )
        assert response.status_code == 400

    def test_returns_400_when_end_before_start(
        self, client, student, country, academic_year
    ):
        with patch("app.complementary.api.upload_document", return_value="k/x.pdf"):
            response = client.post(
                _declare_url(
                    student.ine,
                    academic_year_id=academic_year.pk,
                    country_id=country.pk,
                    start_date="2026-08-30",
                    end_date="2026-06-01",
                ),
                FILES={"document": _pdf_file()},
            )
        assert response.status_code == 400

    def test_returns_400_for_invalid_mime_type(
        self, client, student, country, academic_year
    ):
        with patch("app.complementary.api.upload_document", return_value="k/x.pdf"):
            response = client.post(
                _declare_url(
                    student.ine,
                    academic_year_id=academic_year.pk,
                    country_id=country.pk,
                ),
                FILES={"document": _pdf_file(content_type="text/plain")},
            )
        assert response.status_code == 400

    def test_creates_mobility_and_alert(self, client, student, country, academic_year):
        from app.alerts.models import SystemAlert

        initial_alert_count = SystemAlert.objects.count()
        with patch("app.complementary.api.upload_document", return_value="comp/x.pdf"):
            response = client.post(
                _declare_url(
                    student.ine,
                    academic_year_id=academic_year.pk,
                    country_id=country.pk,
                    experience_type="Séjour linguistique",
                    destination_institution="University of Bath",
                    start_date="2026-07-01",
                    end_date="2026-07-31",
                ),
                FILES={"document": _pdf_file()},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["experience_type"] == "Séjour linguistique"
        assert data["status"] == MobilityStatus.PENDING
        assert data["destination_country_name"] == "Allemagne"
        assert data["academic_year_label"] == "2026-2027"
        assert data["student_ine"] == student.ine
        assert ComplementaryMobility.objects.filter(student=student).count() == 1
        assert SystemAlert.objects.count() == initial_alert_count + 1


# ── Admin validate/reject ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestValidateMobility:
    def test_validate_pending_mobility(self, client, pending_mobility):
        with patch("app.complementary.api.log_action"):
            response = client.post(f"/{pending_mobility.pk}/validate/")
        assert response.status_code == 200
        refreshed = ComplementaryMobility.objects.get(pk=pending_mobility.pk)
        assert refreshed.status == MobilityStatus.VALIDATED

    def test_returns_404_for_unknown_mobility(self, client):
        response = client.post("/99999/validate/")
        assert response.status_code == 404

    def test_returns_409_when_already_validated(self, client, pending_mobility):
        pending_mobility.validate()
        pending_mobility.save()
        response = client.post(f"/{pending_mobility.pk}/validate/")
        assert response.status_code == 409

    def test_creates_audit_log_entry(self, client, pending_mobility):
        with patch("app.complementary.api.log_action") as mock_log:
            client.post(f"/{pending_mobility.pk}/validate/")
        mock_log.assert_called_once()
        assert mock_log.call_args.kwargs["action"] == "validate_complementary_mobility"


@pytest.mark.django_db
class TestRejectMobility:
    def test_reject_pending_mobility(self, client, pending_mobility):
        with patch("app.complementary.api.log_action"):
            response = client.post(
                f"/{pending_mobility.pk}/reject/",
                json={"reason": "Justificatif insuffisant."},
            )
        assert response.status_code == 200
        refreshed = ComplementaryMobility.objects.get(pk=pending_mobility.pk)
        assert refreshed.status == MobilityStatus.REJECTED
        assert refreshed.rejection_reason == "Justificatif insuffisant."

    def test_returns_422_for_empty_reason(self, client, pending_mobility):
        response = client.post(
            f"/{pending_mobility.pk}/reject/",
            json={"reason": ""},
        )
        assert response.status_code == 422

    def test_returns_422_for_whitespace_reason(self, client, pending_mobility):
        response = client.post(
            f"/{pending_mobility.pk}/reject/",
            json={"reason": "   "},
        )
        assert response.status_code == 422

    def test_returns_404_for_unknown_mobility(self, client):
        response = client.post("/99999/reject/", json={"reason": "Motif valide."})
        assert response.status_code == 404

    def test_returns_409_when_not_pending(self, client, pending_mobility):
        pending_mobility.validate()
        pending_mobility.save()
        response = client.post(
            f"/{pending_mobility.pk}/reject/",
            json={"reason": "trop tard"},
        )
        assert response.status_code == 409

    def test_creates_audit_log_entry(self, client, pending_mobility):
        with patch("app.complementary.api.log_action") as mock_log:
            client.post(
                f"/{pending_mobility.pk}/reject/",
                json={"reason": "Justificatif non conforme."},
            )
        mock_log.assert_called_once()
        assert mock_log.call_args.kwargs["action"] == "reject_complementary_mobility"
        assert "Justificatif non conforme" in mock_log.call_args.kwargs["detail"]


# ── Admin PATCH update ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateMobility:
    def test_patch_validates_mobility(self, client, pending_mobility):
        with patch("app.complementary.api.log_action"):
            response = client.patch(
                f"/{pending_mobility.pk}/",
                json={"status": "validated", "rejection_reason": ""},
            )
        assert response.status_code == 200
        refreshed = ComplementaryMobility.objects.get(pk=pending_mobility.pk)
        assert refreshed.status == MobilityStatus.VALIDATED

    def test_patch_rejects_mobility_with_reason(self, client, pending_mobility):
        with patch("app.complementary.api.log_action"):
            response = client.patch(
                f"/{pending_mobility.pk}/",
                json={"status": "rejected", "rejection_reason": "Motif test."},
            )
        assert response.status_code == 200
        refreshed = ComplementaryMobility.objects.get(pk=pending_mobility.pk)
        assert refreshed.status == MobilityStatus.REJECTED
        assert refreshed.rejection_reason == "Motif test."

    def test_patch_returns_400_when_rejection_reason_missing(
        self, client, pending_mobility
    ):
        response = client.patch(
            f"/{pending_mobility.pk}/",
            json={"status": "rejected", "rejection_reason": ""},
        )
        assert response.status_code == 400

    def test_patch_returns_400_for_invalid_status(self, client, pending_mobility):
        response = client.patch(
            f"/{pending_mobility.pk}/",
            json={"status": "unknown_status", "rejection_reason": ""},
        )
        assert response.status_code == 400

    def test_patch_returns_404_for_unknown_mobility(self, client):
        response = client.patch(
            "/99999/",
            json={"status": "validated", "rejection_reason": ""},
        )
        assert response.status_code == 404

    def test_patch_updates_timestamp(self, client, pending_mobility):
        original_updated_at = pending_mobility.updated_at
        with patch("app.complementary.api.log_action"):
            client.patch(
                f"/{pending_mobility.pk}/",
                json={"status": "validated", "rejection_reason": ""},
            )
        # refresh_from_db() also goes through the FSM protected descriptor,
        # so we fetch a fresh instance instead.
        refreshed = ComplementaryMobility.objects.get(pk=pending_mobility.pk)
        assert refreshed.updated_at > original_updated_at
