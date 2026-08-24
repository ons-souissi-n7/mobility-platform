from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementYear
from app.outgoing.models import Assignment, AssignmentResult, SlotType
from app.recommendation.services.dataset import build_training_dataset
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student, StudentWish


def _closed_year() -> AcademicYear:
    year = AcademicYear.objects.create(
        label="2023-2024", start_date=date(2023, 9, 1), end_date=date(2024, 8, 31)
    )
    AcademicYear.objects.filter(pk=year.pk).update(status="closed")
    return AcademicYear.objects.get(pk=year.pk)


def _agreement_year(year: AcademicYear, name: str) -> AgreementYear:
    country, _ = Country.objects.get_or_create(
        iso2="DE",
        defaults={
            "name_fr": "Allemagne",
            "name_en": "Germany",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        },
    )
    univ = PartnerUniversity.objects.create(
        name=name, short_name=name[:10], country=country
    )
    agreement = Agreement.objects.create(
        name=name, partner_university=univ, direction="outgoing", inp_total_places=5
    )
    return AgreementYear.objects.create(
        agreement=agreement, academic_year=year, is_active=True, n7_places=5
    )


@pytest.mark.django_db
class TestBuildTrainingDataset:
    def test_target_is_one_only_for_the_granted_wish(self):
        """Un étudiant qui vœux A (obtenu) et B (non obtenu) doit produire une
        ligne positive pour A et une ligne négative pour B — pas l'inverse."""
        year = _closed_year()
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay_granted = _agreement_year(year, "Accord obtenu")
        ay_declined = _agreement_year(year, "Accord refusé")

        student = Student.objects.create(
            ine="23SN001TST", first_name="A", last_name="B"
        )
        enrollment = AnnualEnrollment.objects.create(
            student=student,
            academic_year=year,
            department=dept,
            level=level,
            gpa="15.00",
        )
        StudentWish.objects.create(
            annual_enrollment=enrollment, agreement_year=ay_granted, rank=1
        )
        StudentWish.objects.create(
            annual_enrollment=enrollment, agreement_year=ay_declined, rank=2
        )
        assignment = Assignment.objects.create(academic_year=year)
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            slot_type=SlotType.DEPT,
            agreement_year=ay_granted,
        )

        rows, targets = build_training_dataset()

        assert len(rows) == 2
        # 2 lignes, cibles différentes : une positive, une négative.
        assert sorted(targets) == [0, 1]
        # La ligne positive porte le taux historique du bon accord (100% : le
        # seul vœu jamais exprimé pour ay_granted a été satisfait).
        positive_row = rows[targets.index(1)]
        assert positive_row[0] == 15.0
        assert positive_row[1] == "SN"

    def test_is_french_feature_reflects_student_nationality(self):
        """La colonne is_french (index 3) doit valoir 1 pour un étudiant de
        nationalité française, 0 pour une autre nationalité ou une
        nationalité non renseignée (cf. gale_shapley.py::_score, même
        critère que celui utilisé pour la priorité d'affectation)."""
        year = _closed_year()
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay = _agreement_year(year, "Accord")
        france, _ = Country.objects.get_or_create(
            iso2="FR",
            defaults={
                "name_fr": "France",
                "name_en": "France",
                "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
            },
        )
        germany, _ = Country.objects.get_or_create(
            iso2="DE",
            defaults={
                "name_fr": "Allemagne",
                "name_en": "Germany",
                "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
            },
        )

        french_student = Student.objects.create(
            ine="23SN010TST", first_name="E", last_name="F", nationality=france
        )
        foreign_student = Student.objects.create(
            ine="23SN011TST", first_name="G", last_name="H", nationality=germany
        )
        unknown_student = Student.objects.create(
            ine="23SN012TST", first_name="I", last_name="J"
        )

        for student in (french_student, foreign_student, unknown_student):
            enrollment = AnnualEnrollment.objects.create(
                student=student, academic_year=year, department=dept, level=level
            )
            StudentWish.objects.create(
                annual_enrollment=enrollment, agreement_year=ay, rank=1
            )

        rows, _ = build_training_dataset()

        # gpa/dept/rate sont identiques pour les 3 lignes (aucun ne diffère
        # sauf la nationalité) : seule la colonne is_french (index 3) doit
        # varier, un 1 (français) et deux 0 (étranger / non renseignée).
        assert len(rows) == 3
        assert sorted(row[3] for row in rows) == [0, 0, 1]

    def test_unassigned_student_produces_only_negative_rows(self):
        year = _closed_year()
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay = _agreement_year(year, "Accord non obtenu")

        student = Student.objects.create(
            ine="23SN002TST", first_name="C", last_name="D"
        )
        enrollment = AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level
        )
        StudentWish.objects.create(
            annual_enrollment=enrollment, agreement_year=ay, rank=1
        )
        assignment = Assignment.objects.create(academic_year=year)
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            slot_type=SlotType.UNASSIGNED,
        )

        rows, targets = build_training_dataset()

        assert rows and targets == [0]
