"""Tests d'intégration pour l'API internships — import errors & réconciliation."""

from __future__ import annotations

from datetime import date

import pytest
from ninja.testing import TestClient

from app.academic.models import AcademicYear
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.internships.api import router
from app.internships.models import Internship
from app.reference.models import Country
from app.students.models import Student


@pytest.fixture()
def client():
    return TestClient(router)


def _make_failed_raw(payload: dict, year=None) -> RawImport:
    return RawImport.objects.create(
        source="excel_internships",
        external_id="row_2_ACME",
        entity=RawImportEntity.INTERNSHIP,
        status=RawImportStatus.FAILED,
        error_message="Étudiant introuvable (INE : '99999999999').",
        payload=payload,
        academic_year=year,
    )


@pytest.mark.django_db
class TestGetInternshipReconciliationCandidates:
    def test_returns_404_for_nonexistent_id(self, client):
        response = client.get("/import-errors/99999/candidates/")
        assert response.status_code == 404

    def test_returns_404_for_non_failed_status(self, client):
        raw = RawImport.objects.create(
            source="excel_internships",
            external_id="row_1_ok",
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.IMPORTED,
            payload={"Étudiant (INE – Nom Prénom)": "1234567890A – MARTIN Jean"},
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 404

    def test_returns_empty_list_when_no_student_field(self, client):
        raw = _make_failed_raw(
            payload={"N°INE": "99999999999", "Raison sociale": "ACME"}
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_empty_list_when_no_similar_student(self, client):
        raw = _make_failed_raw(
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 – DUPONT Alice"}
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_matching_student_with_expected_fields(self, client):
        Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="jean.martin@n7.fr",
        )
        raw = _make_failed_raw(
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 – MARTIN Jean"}
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        candidate = data[0]
        assert candidate["ine"] == "12345678901"
        assert candidate["last_name"] == "Martin"
        assert candidate["first_name"] == "Jean"
        assert candidate["score"] >= 0.60
        assert candidate["confidence"] in ("high", "medium", "low")

    def test_parses_dash_separator_variant(self, client):
        Student.objects.create(
            ine="12345678901", first_name="Alice", last_name="Dupont"
        )
        raw = _make_failed_raw(
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 - DUPONT Alice"}
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_candidates_ordered_by_score_descending(self, client):
        Student.objects.create(ine="10000000001", first_name="Jean", last_name="Martin")
        Student.objects.create(ine="10000000002", first_name="Zzz", last_name="Marti")
        raw = _make_failed_raw(
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 – MARTIN Jean"}
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        scores = [c["score"] for c in response.json()]
        assert scores == sorted(scores, reverse=True)

    def test_returns_404_for_non_internship_entity(self, client):
        raw = RawImport.objects.create(
            source="excel_students",
            external_id="row_1",
            entity=RawImportEntity.STUDENT,
            status=RawImportStatus.FAILED,
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 – MARTIN Jean"},
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 404

    def test_returns_empty_for_eudonet_payload_without_name(self, client):
        raw = _make_failed_raw(
            payload={
                "N°INE": "99999999999",
                "Raison sociale": "Airbus",
                "Pays": "France",
                "Date de début": "01/06/2026",
                "Date de fin": "31/08/2026",
            }
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        assert response.json() == []

    def test_parses_eudonet_libelle_for_candidates(self, client):
        Student.objects.create(
            ine="12345678901", first_name="Pierre", last_name="Inconnu"
        )
        raw = _make_failed_raw(
            payload={
                "N°INE": "99999999999",
                "libelle": "INCONNU Pierre - SCHNEIDER ELECTRIC SE (01/04/2027)",
                "Raison sociale": "SCHNEIDER ELECTRIC SE",
                "Pays": "Canada",
            }
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ine"] == "12345678901"

    def test_department_code_included_when_year_given(self, client):
        from app.reference.models import Department, Level
        from app.students.models import AnnualEnrollment

        year = AcademicYear.objects.create(
            label="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 8, 31)
        )
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        student = Student.objects.create(
            ine="12345678901", first_name="Jean", last_name="Martin"
        )
        AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level
        )
        raw = _make_failed_raw(
            payload={"Étudiant (INE – Nom Prénom)": "99999999999 – MARTIN Jean"},
            year=year,
        )
        response = client.get(f"/import-errors/{raw.pk}/candidates/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["department_code"] == "SN"


# ---------------------------------------------------------------------------
# Shared helpers for force / retry / add / ignore tests
# ---------------------------------------------------------------------------

EUDONET_PAYLOAD = {
    "ine": "12345678901",
    "libelle": "MARTIN Jean - AIRBUS SAS (01/04/2026)",
    "company_name": "AIRBUS SAS",
    "country_name": "France",
    "city": "Toulouse",
    "internship_type": "PFE",
    "status": "Validé",
    "status_code": "9",
    "start_date": "2026-04-01",
    "end_date": "2026-09-30",
    "weeks": 26,
    "school_tutor": "M. Dupont",
    "company_tutor": "Mme Roux",
    "title": "Stage Airbus",
}


def _make_conflict_raw(student: Student, year: AcademicYear) -> RawImport:
    """Failed raw import with _existing for a student whose internship already exists."""
    return RawImport.objects.create(
        source="eudonet_internships",
        external_id=student.ine,
        entity=RawImportEntity.INTERNSHIP,
        status=RawImportStatus.FAILED,
        error_message="Données modifiées pour '12345678901' — confirmez le remplacement.",
        payload={
            **EUDONET_PAYLOAD,
            "_existing": {
                "ine": student.ine,
                "company_name": "ANCIENNE ENTREPRISE",
                "start_date": "2026-03-01",
                "end_date": "2026-08-31",
                "country_name": "France",
                "city": "Paris",
                "title": "Ancien stage",
                "internship_type": "PFA",
                "weeks": 24,
                "status": "En cours",
                "libelle": "MARTIN Jean - ANCIENNE ENTREPRISE (01/03/2026)",
                "status_code": "5",
                "school_tutor": "",
                "company_tutor": "",
            },
        },
        academic_year=year,
    )


def _setup_year_and_student():
    year = AcademicYear.objects.create(
        label="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 8, 31)
    )
    student = Student.objects.create(
        ine="12345678901", first_name="Jean", last_name="Martin"
    )
    return year, student


# ---------------------------------------------------------------------------
# POST /import-errors/{id}/force/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestForceImportError:
    def test_force_updates_existing_internship(self, client):
        year, student = _setup_year_and_student()
        country = Country.objects.create(iso2="FR", name_fr="France", name_en="France")
        # Existing internship with old company
        Internship.objects.create(
            student=student,
            academic_year=year,
            company_name="ANCIENNE ENTREPRISE",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 8, 31),
            country=country,
        )
        raw = _make_conflict_raw(student, year)

        response = client.post(f"/import-errors/{raw.pk}/force/", json={"payload": {}})

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        internship = Internship.objects.get(student=student, academic_year=year)
        assert internship.company_name == "AIRBUS SAS"
        assert internship.city == "Toulouse"

    def test_force_with_ine_correction_links_correct_student(self, client):
        year, _ = _setup_year_and_student()
        wrong_ine_student = Student.objects.create(
            ine="99999999999", first_name="Inconnu", last_name="Inconnu"
        )
        raw = RawImport.objects.create(
            source="eudonet_internships",
            external_id="99999999999",
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Étudiant introuvable (INE : '99999999999').",
            payload={**EUDONET_PAYLOAD, "ine": "99999999999"},
            academic_year=year,
        )
        _ = wrong_ine_student  # referenced in raw payload

        response = client.post(
            f"/import-errors/{raw.pk}/force/",
            json={"payload": {"ine": "12345678901"}},
        )

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        assert Internship.objects.filter(
            student__ine="12345678901", academic_year=year
        ).exists()

    def test_force_returns_404_for_nonexistent_raw(self, client):
        response = client.post("/import-errors/99999/force/", json={"payload": {}})
        assert response.status_code == 404

    def test_force_returns_400_when_student_not_found(self, client):
        year = AcademicYear.objects.create(
            label="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 8, 31)
        )
        raw = RawImport.objects.create(
            source="eudonet_internships",
            external_id="00000000000",
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Étudiant introuvable.",
            payload={**EUDONET_PAYLOAD, "ine": "00000000000"},
            academic_year=year,
        )
        response = client.post(f"/import-errors/{raw.pk}/force/", json={"payload": {}})
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /import-errors/{id}/add/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAddImportErrorAsNew:
    def test_add_creates_new_internship_alongside_existing(self, client):
        year, student = _setup_year_and_student()
        country = Country.objects.create(iso2="FR", name_fr="France", name_en="France")
        Internship.objects.create(
            student=student,
            academic_year=year,
            company_name="ANCIENNE ENTREPRISE",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 8, 31),
            country=country,
        )
        raw = _make_conflict_raw(student, year)

        response = client.post(f"/import-errors/{raw.pk}/add/")

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        # Both internships exist (old + new)
        assert (
            Internship.objects.filter(student=student, academic_year=year).count() == 2
        )

    def test_add_returns_409_when_exact_duplicate(self, client):
        year, student = _setup_year_and_student()
        country = Country.objects.create(iso2="FR", name_fr="France", name_en="France")
        # Create internship with same company + dates as the payload
        Internship.objects.create(
            student=student,
            academic_year=year,
            company_name="AIRBUS SAS",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 9, 30),
            country=country,
        )
        raw = _make_conflict_raw(student, year)

        response = client.post(f"/import-errors/{raw.pk}/add/")

        assert response.status_code == 409

    def test_add_returns_404_for_nonexistent_raw(self, client):
        response = client.post("/import-errors/99999/add/")
        assert response.status_code == 404

    def test_add_returns_400_when_student_not_found(self, client):
        year = AcademicYear.objects.create(
            label="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 8, 31)
        )
        raw = RawImport.objects.create(
            source="eudonet_internships",
            external_id="00000000000",
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Étudiant introuvable.",
            payload={**EUDONET_PAYLOAD, "ine": "00000000000"},
            academic_year=year,
        )
        response = client.post(f"/import-errors/{raw.pk}/add/")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /import-errors/{id}/retry/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRetryImportError:
    def test_retry_creates_internship_when_student_found(self, client):
        year, student = _setup_year_and_student()
        Country.objects.create(iso2="FR", name_fr="France", name_en="France")
        raw = RawImport.objects.create(
            source="eudonet_internships",
            external_id=student.ine,
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Données modifiées.",
            payload=EUDONET_PAYLOAD,
            academic_year=year,
        )

        response = client.post(f"/import-errors/{raw.pk}/retry/")

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        assert Internship.objects.filter(student=student, academic_year=year).exists()

    def test_retry_returns_400_when_student_not_found(self, client):
        year = AcademicYear.objects.create(
            label="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 8, 31)
        )
        raw = RawImport.objects.create(
            source="eudonet_internships",
            external_id="00000000000",
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Étudiant introuvable.",
            payload={**EUDONET_PAYLOAD, "ine": "00000000000"},
            academic_year=year,
        )

        response = client.post(f"/import-errors/{raw.pk}/retry/")
        assert response.status_code == 400

    def test_retry_returns_404_for_nonexistent_raw(self, client):
        response = client.post("/import-errors/99999/retry/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /import-errors/{id}/ignore/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIgnoreImportError:
    def test_ignore_marks_raw_as_ignored(self, client):
        year, student = _setup_year_and_student()
        raw = _make_conflict_raw(student, year)

        response = client.post(f"/import-errors/{raw.pk}/ignore/")

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IGNORED

    def test_ignore_also_ignores_earlier_raws_for_same_external_id(self, client):
        year, student = _setup_year_and_student()
        older = RawImport.objects.create(
            source="eudonet_internships",
            external_id=student.ine,
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
            error_message="Données modifiées (ancienne).",
            payload=EUDONET_PAYLOAD,
            academic_year=year,
        )
        current = _make_conflict_raw(student, year)

        client.post(f"/import-errors/{current.pk}/ignore/")

        older.refresh_from_db()
        assert older.status == RawImportStatus.IGNORED

    def test_ignore_returns_404_for_nonexistent_raw(self, client):
        response = client.post("/import-errors/99999/ignore/")
        assert response.status_code == 404
