"""Tests d'intégration pour l'API CTI."""

from __future__ import annotations

from datetime import date

import pytest
from ninja.testing import TestClient

from app.cti.api import router
from app.students.models import Student

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    return TestClient(router)


@pytest.fixture()
def student(db) -> Student:
    return Student.objects.create(
        ine="CTI0000002B",
        first_name="Paul",
        last_name="Dupont",
        email="paul.dupont@example.com",
    )


@pytest.fixture()
def country_de(db):
    from app.reference.models import Country, CTIRegion

    return Country.objects.create(
        iso2="DE",
        name_fr="Allemagne",
        name_en="Germany",
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )


@pytest.fixture()
def academic_year(db):
    from app.academic.models import AcademicYear

    return AcademicYear.objects.create(
        label="2024-2025",
        start_date=date(2024, 9, 1),
        end_date=date(2025, 8, 31),
    )


# ---------------------------------------------------------------------------
# GET /students/{ine}/duration/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetCtiDuration:
    def test_returns_zeros_for_student_without_mobility(self, client, student):
        response = client.get(f"/students/{student.ine}/duration/")

        assert response.status_code == 200
        data = response.json()
        assert data["ine"] == student.ine
        assert data["exchange_weeks"] == 0.0
        assert data["internship_weeks"] == 0.0
        assert data["complementary_weeks"] == 0.0
        assert data["total_weeks"] == 0.0

    def test_response_does_not_contain_meets_cti(self, client, student):
        response = client.get(f"/students/{student.ine}/duration/")

        assert response.status_code == 200
        data = response.json()
        assert "meets_cti" not in data
        assert "cti_threshold_weeks" not in data

    def test_returns_404_for_unknown_ine(self, client, db):
        response = client.get("/students/UNKNOWN_INE/duration/")

        assert response.status_code == 404

    def test_accounts_for_international_internship(
        self, client, student, country_de, academic_year
    ):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Siemens AG",
            country=country_de,
            weeks_in_company=16,
        )

        response = client.get(f"/students/{student.ine}/duration/")

        assert response.status_code == 200
        data = response.json()
        assert data["internship_weeks"] == 16.0
        assert data["total_weeks"] == 16.0


# ---------------------------------------------------------------------------
# POST /students/{ine}/duration/refresh/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRefreshCtiDuration:
    def test_creates_mobility_duration_record(self, client, student):
        from app.cti.models import MobilityDuration

        assert not MobilityDuration.objects.filter(student=student).exists()

        response = client.post(f"/students/{student.ine}/duration/refresh/")

        assert response.status_code == 200
        assert MobilityDuration.objects.filter(student=student).exists()

    def test_returns_correct_structure(self, client, student):
        response = client.post(f"/students/{student.ine}/duration/refresh/")

        assert response.status_code == 200
        data = response.json()
        assert "ine" in data
        assert "exchange_weeks" in data
        assert "internship_weeks" in data
        assert "complementary_weeks" in data
        assert "total_weeks" in data
        assert "meets_cti" not in data

    def test_idempotent_updates_existing_record(self, client, student):
        from app.cti.models import MobilityDuration

        client.post(f"/students/{student.ine}/duration/refresh/")
        client.post(f"/students/{student.ine}/duration/refresh/")

        assert MobilityDuration.objects.filter(student=student).count() == 1

    def test_returns_404_for_unknown_ine(self, client, db):
        response = client.post("/students/UNKNOWN_INE/duration/refresh/")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /students/{ine}/history/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetStudentHistory:
    def test_returns_empty_history_for_student_without_mobility(self, client, student):
        response = client.get(f"/students/{student.ine}/history/")

        assert response.status_code == 200
        data = response.json()
        assert data["ine"] == student.ine
        assert data["exchanges"] == []
        assert data["internships"] == []
        assert data["complementary_mobilities"] == []

    def test_totals_are_zero_for_student_without_mobility(self, client, student):
        response = client.get(f"/students/{student.ine}/history/")

        assert response.status_code == 200
        totals = response.json()["totals"]
        assert totals["exchange_weeks"] == 0.0
        assert totals["internship_weeks"] == 0.0
        assert totals["complementary_weeks"] == 0.0
        assert totals["total_weeks"] == 0.0

    def test_returns_404_for_unknown_ine(self, client, db):
        response = client.get("/students/UNKNOWN_INE/history/")

        assert response.status_code == 404

    def test_lists_internships(self, client, student, country_de, academic_year):
        from app.internships.models import Internship

        Internship.objects.create(
            student=student,
            academic_year=academic_year,
            company_name="Volkswagen AG",
            country=country_de,
            weeks_in_company=10,
        )

        response = client.get(f"/students/{student.ine}/history/")

        assert response.status_code == 200
        internships = response.json()["internships"]
        assert len(internships) == 1
        assert internships[0]["company_name"] == "Volkswagen AG"
        assert internships[0]["is_international"] is True
        assert internships[0]["weeks_in_company"] == 10

    def test_lists_complementary_mobilities_regardless_of_status(
        self, client, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        # pending
        ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 14),
        )
        # validated
        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Séjour linguistique",
            destination_country=country_de,
            start_date=date(2024, 8, 1),
            end_date=date(2024, 8, 14),
        )
        m.validate()
        m.save()

        response = client.get(f"/students/{student.ine}/history/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["complementary_mobilities"]) == 2
        statuses = {m["status"] for m in data["complementary_mobilities"]}
        assert "pending" in statuses
        assert "validated" in statuses

    def test_totals_count_only_validated_complementary(
        self, client, student, country_de, academic_year
    ):
        from app.complementary.models import ComplementaryMobility

        # Pending — ne doit pas compter
        ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Summer school",
            destination_country=country_de,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 14),
        )
        # Validée — 14 jours = 2 semaines
        m = ComplementaryMobility.objects.create(
            student=student,
            academic_year=academic_year,
            experience_type="Séjour linguistique",
            destination_country=country_de,
            start_date=date(2024, 8, 1),
            end_date=date(2024, 8, 15),
        )
        m.validate()
        m.save()

        response = client.get(f"/students/{student.ine}/history/")

        totals = response.json()["totals"]
        assert totals["complementary_weeks"] == 2.0
        assert totals["total_weeks"] == 2.0
