from datetime import date

import pytest
from django.db import IntegrityError
from django.test import Client

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementYear, NomenclatureMapping
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student, StudentWish
from app.students.services.sync_moveon import WishRow, import_wish_rows

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_year(**kwargs) -> AcademicYear:
    defaults = {
        "label": "2026-2027",
        "start_date": date(2026, 9, 1),
        "end_date": date(2027, 8, 31),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


def make_student(ine: str = "22010000001", **kwargs) -> Student:
    kwargs.setdefault("first_name", "Jean")
    kwargs.setdefault("last_name", "Martin")
    return Student.objects.create(ine=ine, **kwargs)


def make_department(code: str = "SN") -> Department:
    dept, _ = Department.objects.get_or_create(
        code=code, defaults={"name": f"Dept {code}"}
    )
    return dept


def make_level(code: str = "M1") -> Level:
    level, _ = Level.objects.get_or_create(
        code=code, defaults={"name": f"Niveau {code}"}
    )
    return level


def make_enrollment(student: Student, year: AcademicYear) -> AnnualEnrollment:
    return AnnualEnrollment.objects.create(
        student=student,
        academic_year=year,
        department=make_department(),
        level=make_level(),
    )


def make_agreement_year(
    agreement: Agreement, year: AcademicYear, **kwargs
) -> AgreementYear:
    defaults = {"is_active": True, "n7_places": 4}
    defaults.update(kwargs)
    ay, _ = AgreementYear.objects.get_or_create(
        agreement=agreement, academic_year=year, defaults=defaults
    )
    return ay


def make_agreement(moveon_id: str = "REL-001", name: str | None = None) -> Agreement:
    country, _ = Country.objects.get_or_create(
        iso2="ES",
        defaults={
            "name_fr": "Espagne",
            "name_en": "Spain",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        },
    )
    university, _ = PartnerUniversity.objects.get_or_create(
        moveon_id=1001,
        defaults={"name": "Universidad Test", "country": country},
    )
    return Agreement.objects.create(
        moveon_id=moveon_id,
        name=name or f"Accord {moveon_id}",
        partner_university=university,
        direction="outgoing",
        inp_total_places=4,
    )


def make_row(
    individu: str = "MARTIN Jean",
    offre_de_sejour: str = "Accord REL-001",
    rank: int = 1,
    ine: str = "",
    moveon_offer_id: str = "",
) -> WishRow:
    return WishRow(
        individu=individu,
        offre_de_sejour=offre_de_sejour,
        rank=rank,
        ine=ine,
        moveon_offer_id=moveon_offer_id,
    )


# ---------------------------------------------------------------------------
# TestStudentWishModel
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStudentWishModel:
    def setup_method(self):
        self.year = make_year()
        self.student = make_student()
        self.agreement = make_agreement()
        self.enrollment = make_enrollment(self.student, self.year)
        self.agreement_year = make_agreement_year(self.agreement, self.year)

    def test_create_wish(self):
        wish = StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

        assert wish.pk is not None
        assert str(wish) == f"{self.student} — Vœu 1 ({self.year})"

    def test_unique_rank_per_enrollment(self):
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )
        agreement2 = make_agreement("REL-002")
        agreement_year2 = make_agreement_year(agreement2, self.year)

        with pytest.raises(IntegrityError):
            StudentWish.objects.create(
                annual_enrollment=self.enrollment,
                agreement_year=agreement_year2,
                rank=1,
            )

    def test_unique_agreement_year_per_enrollment(self):
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

        with pytest.raises(IntegrityError):
            StudentWish.objects.create(
                annual_enrollment=self.enrollment,
                agreement_year=self.agreement_year,
                rank=2,
            )

    def test_different_ranks_same_enrollment_allowed(self):
        agreement2 = make_agreement("REL-002")
        agreement_year2 = make_agreement_year(agreement2, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

        wish2 = StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=agreement_year2,
            rank=2,
        )

        assert wish2.pk is not None

    def test_same_rank_different_enrollments_allowed(self):
        student2 = make_student(ine="22010000002")
        enrollment2 = make_enrollment(student2, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

        wish2 = StudentWish.objects.create(
            annual_enrollment=enrollment2,
            agreement_year=self.agreement_year,
            rank=1,
        )

        assert wish2.pk is not None


# ---------------------------------------------------------------------------
# TestImportWishRows (ETL)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestImportWishRows:
    def setup_method(self):
        self.year = make_year()
        self.student = make_student()
        self.agreement = make_agreement()
        self.enrollment = make_enrollment(self.student, self.year)
        self.agreement_year = make_agreement_year(self.agreement, self.year)

    def test_creates_wish(self):
        report = import_wish_rows([make_row()], self.year)

        assert report.created == 1
        assert report.updated == 0
        assert StudentWish.objects.filter(
            annual_enrollment=self.enrollment, rank=1
        ).exists()

    def test_updates_existing_wish(self):
        agreement2 = make_agreement("REL-002")
        agreement_year2 = make_agreement_year(agreement2, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=agreement_year2,
            rank=1,
        )

        report = import_wish_rows(
            [make_row(offre_de_sejour="Accord REL-001")], self.year
        )

        assert report.updated == 1
        assert report.created == 0
        wish = StudentWish.objects.get(annual_enrollment=self.enrollment, rank=1)
        assert wish.agreement_year.agreement == self.agreement

    def test_resolves_student_by_ine(self):
        report = import_wish_rows([make_row(ine="22010000001", individu="")], self.year)

        assert report.created == 1

    def test_ine_takes_priority_over_name(self):
        # INE matches the student even if individu is completely wrong
        report = import_wish_rows(
            [make_row(ine="22010000001", individu="NOM FAUX")], self.year
        )

        assert report.created == 1

    def test_falls_back_to_name_when_ine_missing(self):
        report = import_wish_rows([make_row(ine="", individu="MARTIN Jean")], self.year)

        assert report.created == 1

    def test_unknown_student_marks_unresolved(self):
        report = import_wish_rows(
            [make_row(ine="99999999999", individu="INCONNU NomTest")], self.year
        )

        assert len(report.unresolved) == 1
        assert "99999999999" in report.unresolved[0]["reason"]
        assert not StudentWish.objects.exists()

    def test_no_enrollment_marks_unresolved(self):
        make_student(ine="22010000002", first_name="Sophie", last_name="Dupont")
        # student has no AnnualEnrollment for self.year

        report = import_wish_rows(
            [make_row(ine="22010000002", individu="DUPONT Sophie")], self.year
        )

        assert len(report.unresolved) == 1
        assert "inscription annuelle" in report.unresolved[0]["reason"]
        assert not StudentWish.objects.exists()

    def test_unknown_agreement_marks_unresolved(self):
        report = import_wish_rows(
            [make_row(offre_de_sejour="Accord inexistant")], self.year
        )

        assert len(report.unresolved) == 1
        assert "Accord inexistant" in report.unresolved[0]["reason"]

    def test_agreement_fallback_by_moveon_id(self):
        # If the "Offre de séjour" doesn't match by name but matches a moveon_id,
        # the agreement is still resolved.
        report = import_wish_rows([make_row(offre_de_sejour="REL-001")], self.year)

        assert report.created == 1

    def test_multiple_wishes_per_student(self):
        make_agreement_year(make_agreement("REL-002"), self.year)
        make_agreement_year(make_agreement("REL-003"), self.year)
        rows = [
            make_row(rank=1, offre_de_sejour="Accord REL-001"),
            make_row(rank=2, offre_de_sejour="Accord REL-002"),
            make_row(rank=3, offre_de_sejour="Accord REL-003"),
        ]

        report = import_wish_rows(rows, self.year)

        assert report.created == 3
        assert (
            StudentWish.objects.filter(annual_enrollment=self.enrollment).count() == 3
        )

    def test_multiple_students(self):
        student2 = Student.objects.create(
            ine="22010000002", first_name="Sophie", last_name="Dupont"
        )
        make_enrollment(student2, self.year)
        make_agreement_year(make_agreement("REL-002"), self.year)
        rows = [
            make_row(individu="MARTIN Jean", rank=1, offre_de_sejour="Accord REL-001"),
            make_row(
                individu="DUPONT Sophie", rank=1, offre_de_sejour="Accord REL-002"
            ),
        ]

        report = import_wish_rows(rows, self.year)

        assert report.created == 2

    def test_case_insensitive_name_matching(self):
        # "martin jean" (all lowercase) should match Student(last_name="Martin", first_name="Jean")
        report = import_wish_rows([make_row(individu="martin jean")], self.year)

        assert report.created == 1

    def test_mixed_results(self):
        rows = [
            make_row(individu="MARTIN Jean", rank=1, offre_de_sejour="Accord REL-001"),
            make_row(
                individu="INCONNU NomTest", rank=1, offre_de_sejour="Accord REL-001"
            ),
        ]

        report = import_wish_rows(rows, self.year)

        assert report.created == 1
        assert len(report.unresolved) == 1

    def test_resolves_agreement_by_moveon_offer_id(self):
        # L'accord n'a pas le même nom que l'offre, mais le moveon_offer_id correspond.
        report = import_wish_rows(
            [make_row(offre_de_sejour="Nom différent", moveon_offer_id="REL-001")],
            self.year,
        )

        assert report.created == 1

    def test_resolves_agreement_by_nomenclature(self):
        # Accord créé manuellement (pas de moveon_id, nom différent) avec un mapping défini.
        country, _ = Country.objects.get_or_create(
            iso2="DE",
            defaults={
                "name_fr": "Allemagne",
                "name_en": "Germany",
                "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
            },
        )
        univ, _ = PartnerUniversity.objects.get_or_create(
            moveon_id=2001,
            defaults={"name": "TU Berlin", "country": country},
        )
        accord_manuel = Agreement.objects.create(
            moveon_id=None,
            name="Accord TUB Interne",
            partner_university=univ,
            direction="outgoing",
            inp_total_places=2,
        )
        make_agreement_year(accord_manuel, self.year)
        NomenclatureMapping.objects.create(
            partner_university=univ,
            moveon_offer_name="ERASMUS+ TU Berlin 2024",
            agreement=accord_manuel,
        )

        report = import_wish_rows(
            [make_row(offre_de_sejour="ERASMUS+ TU Berlin 2024")],
            self.year,
        )

        assert report.created == 1
        wish = StudentWish.objects.get(annual_enrollment=self.enrollment, rank=1)
        assert wish.agreement_year.agreement == accord_manuel

    def test_auto_updates_moveon_id_when_empty(self):
        # Si l'accord n'a pas de moveon_id mais qu'on reçoit un moveon_offer_id dans le vœu,
        # le moveon_id de l'accord est renseigné automatiquement.
        self.agreement.moveon_id = None
        self.agreement.save(update_fields=["moveon_id"])

        report = import_wish_rows(
            [
                make_row(
                    offre_de_sejour="Accord REL-001", moveon_offer_id="REL-AUTO-999"
                )
            ],
            self.year,
        )

        assert report.created == 1
        self.agreement.refresh_from_db()
        assert self.agreement.moveon_id == "REL-AUTO-999"


# ---------------------------------------------------------------------------
# TestWishesAPI
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSyncWishesAPI:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.student = make_student()
        self.agreement = make_agreement()
        self.enrollment = make_enrollment(self.student, self.year)
        self.agreement_year = make_agreement_year(self.agreement, self.year)

    def test_sync_triggers_background_task(self, monkeypatch):
        import app.students.api as students_api

        calls = []
        monkeypatch.setattr(
            students_api,
            "enqueue_sync_moveon_wishes",
            lambda year_id, triggered_by="": calls.append(year_id) or "fake-task-id",
        )

        response = self.client.post(
            f"/api/v1/students/students/wishes/sync-moveon/{self.year.id}/"
        )

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "fake-task-id"
        assert calls == [self.year.id]

    def test_sync_unknown_year_returns_404(self):
        response = self.client.post(
            "/api/v1/students/students/wishes/sync-moveon/99999/"
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestListWishesByYearAPI:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.student = make_student()
        self.agreement = make_agreement()
        self.enrollment = make_enrollment(self.student, self.year)
        self.agreement_year = make_agreement_year(self.agreement, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

    def test_list_by_year(self):
        response = self.client.get(
            f"/api/v1/students/students/wishes/by-year/{self.year.id}/"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ine"] == "22010000001"
        assert len(data[0]["wishes"]) == 1
        assert data[0]["wishes"][0]["rank"] == 1
        assert data[0]["wishes"][0]["agreement_name"] == "Accord REL-001"

    def test_list_by_year_ordered_by_rank(self):
        agreement2 = make_agreement("REL-002")
        agreement_year2 = make_agreement_year(agreement2, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=agreement_year2,
            rank=2,
        )

        response = self.client.get(
            f"/api/v1/students/students/wishes/by-year/{self.year.id}/"
        )

        data = response.json()
        wishes = data[0]["wishes"]
        assert wishes[0]["rank"] == 1
        assert wishes[1]["rank"] == 2

    def test_list_by_year_empty(self):
        year2 = make_year(
            label="2027-2028", start_date=date(2027, 9, 1), end_date=date(2028, 8, 31)
        )

        response = self.client.get(
            f"/api/v1/students/students/wishes/by-year/{year2.id}/"
        )

        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.django_db
class TestGetStudentWishesAPI:
    def setup_method(self):
        self.client = Client()
        self.year = make_year()
        self.student = make_student()
        self.agreement = make_agreement()
        self.enrollment = make_enrollment(self.student, self.year)
        self.agreement_year = make_agreement_year(self.agreement, self.year)
        StudentWish.objects.create(
            annual_enrollment=self.enrollment,
            agreement_year=self.agreement_year,
            rank=1,
        )

    def test_get_student_wishes(self):
        response = self.client.get(
            f"/api/v1/students/students/{self.student.id}/wishes/{self.year.id}/"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ine"] == "22010000001"
        assert len(data["wishes"]) == 1

    def test_get_student_not_found(self):
        response = self.client.get(
            f"/api/v1/students/students/99999/wishes/{self.year.id}/"
        )

        assert response.status_code == 404

    def test_get_student_no_wishes(self):
        student2 = make_student(ine="22010000002")
        make_enrollment(student2, self.year)

        response = self.client.get(
            f"/api/v1/students/students/{student2.id}/wishes/{self.year.id}/"
        )

        assert response.status_code == 200
        assert response.json()["wishes"] == []


# ---------------------------------------------------------------------------
# Fake MoveOn client for tests
# ---------------------------------------------------------------------------


class _FakeMoveOnWish:
    def __init__(self, payload):
        self._p = payload

    @property
    def ine(self):
        return str(self._p.get("Numéro étudiant") or self._p.get("ine", "")).strip()

    @property
    def individu(self):
        return str(self._p.get("Individu") or self._p.get("individu", "")).strip()

    @property
    def offre_de_sejour(self):
        return str(
            self._p.get("Offre de séjour") or self._p.get("offre_de_sejour", "")
        ).strip()

    @property
    def moveon_offer_id(self):
        val = (
            self._p.get("Offre de séjour ID")
            or self._p.get("offre_de_sejour_id")
            or self._p.get("moveon_offer_id")
        )
        return str(val).strip() if val not in (None, "") else None

    @property
    def rank(self):
        return int(self._p.get("No") or self._p.get("rank", 0))

    @property
    def date_creation(self):
        from app.integrations.moveon import _parse_moveon_date

        return _parse_moveon_date(
            self._p.get("Crée le") or self._p.get("date_creation")
        )

    @property
    def date_modification(self):
        from app.integrations.moveon import _parse_moveon_date

        return _parse_moveon_date(
            self._p.get("Dernière modification le") or self._p.get("date_modification")
        )

    @property
    def payload(self):
        return self._p


class _FakeClient:
    def __init__(self, records):
        self._records = records

    def fetch_student_wishes(self):
        return [_FakeMoveOnWish(r) for r in self._records]
