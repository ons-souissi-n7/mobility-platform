from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementYear
from app.outgoing.models import Assignment, AssignmentResult, SlotType
from app.recommendation.services.historical_rate import compute_historical_rates
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student, StudentWish


def _closed_year(label: str = "2023-2024") -> AcademicYear:
    year = AcademicYear.objects.create(
        label=label, start_date=date(2023, 9, 1), end_date=date(2024, 8, 31)
    )
    AcademicYear.objects.filter(pk=year.pk).update(status="closed")
    return AcademicYear.objects.get(pk=year.pk)


def _agreement_year(year: AcademicYear, name: str = "Erasmus+ Test") -> AgreementYear:
    country = Country.objects.create(
        iso2="DE",
        name_fr="Allemagne",
        name_en="Germany",
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )
    univ = PartnerUniversity.objects.create(
        name="TU Test", short_name="TUT", country=country
    )
    agreement = Agreement.objects.create(
        name=name, partner_university=univ, direction="outgoing", inp_total_places=5
    )
    return AgreementYear.objects.create(
        agreement=agreement, academic_year=year, is_active=True, n7_places=5
    )


@pytest.mark.django_db
class TestComputeHistoricalRates:
    def test_empty_without_closed_campaigns(self):
        assert compute_historical_rates() == {}

    def test_rate_reflects_assigned_over_wished(self):
        year = _closed_year()
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay = _agreement_year(year)
        assignment = Assignment.objects.create(academic_year=year)

        for i in range(4):
            student = Student.objects.create(
                ine=f"23SN{i:03d}TST", first_name=f"S{i}", last_name="Test"
            )
            enrollment = AnnualEnrollment.objects.create(
                student=student,
                academic_year=year,
                department=dept,
                level=level,
                gpa="14.00",
            )
            StudentWish.objects.create(
                annual_enrollment=enrollment, agreement_year=ay, rank=1
            )
            is_assigned = i < 3  # 3 affectés sur 4 vœux -> taux attendu 0.75
            AssignmentResult.objects.create(
                assignment=assignment,
                annual_enrollment=enrollment,
                slot_type=SlotType.DEPT if is_assigned else SlotType.UNASSIGNED,
                agreement_year=ay if is_assigned else None,
            )

        rates = compute_historical_rates()
        assert rates[ay.agreement_id] == pytest.approx(0.75)

    def test_open_campaign_is_ignored(self):
        year = AcademicYear.objects.create(
            label="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 8, 31)
        )
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay = _agreement_year(year)
        student = Student.objects.create(
            ine="26SN001TST", first_name="A", last_name="B"
        )
        enrollment = AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level
        )
        StudentWish.objects.create(
            annual_enrollment=enrollment, agreement_year=ay, rank=1
        )

        assert compute_historical_rates() == {}

    def test_rate_generalizes_across_agreement_years(self):
        """Le taux est indexé par Agreement, pas par AgreementYear : il doit
        rester exploitable pour une AgreementYear future du même accord."""
        year = _closed_year()
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        level = Level.objects.create(code="3A", name="Troisieme annee")
        ay = _agreement_year(year)
        assignment = Assignment.objects.create(academic_year=year)
        student = Student.objects.create(
            ine="23SN000TST", first_name="A", last_name="B"
        )
        enrollment = AnnualEnrollment.objects.create(
            student=student, academic_year=year, department=dept, level=level
        )
        StudentWish.objects.create(
            annual_enrollment=enrollment, agreement_year=ay, rank=1
        )
        AssignmentResult.objects.create(
            assignment=assignment,
            annual_enrollment=enrollment,
            slot_type=SlotType.DEPT,
            agreement_year=ay,
        )

        future_year = AcademicYear.objects.create(
            label="2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 8, 31)
        )
        future_ay = AgreementYear.objects.create(
            agreement=ay.agreement,
            academic_year=future_year,
            is_active=True,
            n7_places=5,
        )

        rates = compute_historical_rates()
        assert rates[future_ay.agreement_id] == pytest.approx(1.0)
