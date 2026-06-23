from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import Agreement, AgreementYear
from app.outgoing.models import Assignment, AssignmentResult
from app.outgoing.services.task_runners import run_gale_shapley
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student, StudentWish


def make_year(**kwargs) -> AcademicYear:
    defaults = {"label": "2026-2027", "start_date": date(2026, 9, 1), "end_date": date(2027, 8, 31)}
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


def make_full_fixture():
    year = make_year()
    dept = Department.objects.create(code="SN", name="Sciences du Numérique")
    level = Level.objects.create(code="3A", name="3e année")
    student = Student.objects.create(ine="111111111AA", first_name="Alice", last_name="Martin")
    enrollment = AnnualEnrollment.objects.create(student=student, academic_year=year, department=dept, level=level)
    country = Country.objects.create(iso2="DE", name_fr="Allemagne", name_en="Germany", cti_region=CTIRegion.EUROPE_HORS_FRANCE)
    university = PartnerUniversity.objects.create(name="TU Berlin", country=country)
    agreement = Agreement.objects.create(name="Acc TU Berlin", partner_university=university, direction="outgoing", inp_total_places=5)
    ay = AgreementYear.objects.create(agreement=agreement, academic_year=year, is_active=True, n7_places=2)
    StudentWish.objects.create(annual_enrollment=enrollment, agreement_year=ay, rank=1)
    return year, enrollment, ay


@pytest.mark.django_db
class TestRunGaleShapley:
    def test_creates_assignment_and_results(self):
        year, enrollment, ay = make_full_fixture()
        run_gale_shapley(year.id, triggered_by="test")
        assignment = Assignment.objects.get(academic_year=year)
        assert assignment.total_students == 1
        assert assignment.assigned_count == 1
        assert assignment.run_by == "test"
        result = AssignmentResult.objects.get(assignment=assignment)
        assert result.annual_enrollment_id == enrollment.id
        assert result.agreement_year_id == ay.id
        assert result.slot_type == "surplus"

    def test_skips_students_without_wishes(self):
        year = make_year(label="2027-2028", start_date=date(2027, 9, 1), end_date=date(2028, 8, 31))
        dept = Department.objects.create(code="MF", name="Mécanique des Fluides")
        level = Level.objects.create(code="3A2", name="3e année bis")
        student = Student.objects.create(ine="999999999ZZ", first_name="Bob", last_name="Dupont")
        AnnualEnrollment.objects.create(student=student, academic_year=year, department=dept, level=level)
        country = Country.objects.create(iso2="ES", name_fr="Espagne", name_en="Spain", cti_region=CTIRegion.EUROPE_HORS_FRANCE)
        university = PartnerUniversity.objects.create(name="UPM Madrid", country=country)
        agreement = Agreement.objects.create(name="Acc UPM", partner_university=university, direction="outgoing", inp_total_places=3)
        AgreementYear.objects.create(agreement=agreement, academic_year=year, is_active=True, n7_places=2)
        # No StudentWish created → algorithm should produce 0 outputs
        run_gale_shapley(year.id)
        assignment = Assignment.objects.get(academic_year=year)
        assert assignment.total_students == 0
        assert assignment.assigned_count == 0

    def test_raises_for_unknown_year(self):
        with pytest.raises(ValueError, match="introuvable"):
            run_gale_shapley(99999)

    def test_atomic_rollback_on_bulk_create_failure(self, monkeypatch):
        year, _, _ = make_full_fixture()

        def boom(*args, **kwargs):
            raise RuntimeError("DB error simulé")

        monkeypatch.setattr("app.outgoing.models.AssignmentResult.objects.bulk_create", boom)
        with pytest.raises(RuntimeError):
            run_gale_shapley(year.id)
        assert not Assignment.objects.filter(academic_year=year).exists()
