from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.academic.models import AcademicYear
from app.reference.models import Department, Level, Parcours
from app.students.models import AnnualEnrollment, Student


@pytest.mark.django_db
class TestStudent:
    def test_create_student(self):
        student = Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="jean.martin@etud.n7.fr",
        )

        assert student.pk is not None
        assert str(student) == "MARTIN Jean (12345678901)"

    def test_ine_unique(self):
        Student.objects.create(ine="12345678901", first_name="Jean", last_name="Martin")

        with pytest.raises(IntegrityError):
            Student.objects.create(
                ine="12345678901", first_name="Autre", last_name="Doublon"
            )

    def test_default_gender_empty(self):
        student = Student.objects.create(
            ine="12345678901", first_name="X", last_name="Y"
        )

        assert student.gender == ""

    def test_gender_male(self):
        student = Student.objects.create(
            ine="12345678901", first_name="Jean", last_name="Martin", gender="M"
        )

        assert student.gender == "M"

    def test_gender_female(self):
        student = Student.objects.create(
            ine="12345678902", first_name="Marie", last_name="Dupont", gender="F"
        )

        assert student.gender == "F"

    def test_ordering_by_last_name(self):
        Student.objects.create(ine="10000000001", first_name="A", last_name="Zeta")
        Student.objects.create(ine="10000000002", first_name="B", last_name="Alpha")

        students = list(Student.objects.all())

        assert students[0].last_name == "Alpha"
        assert students[1].last_name == "Zeta"


@pytest.mark.django_db
class TestAnnualEnrollment:
    def setup_method(self):
        self.student = Student.objects.create(
            ine="12345678901", first_name="Jean", last_name="Martin"
        )
        self.academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
        )
        self.department = Department.objects.create(
            code="SN", name="Sciences du Numerique"
        )
        self.level = Level.objects.create(code="3A", name="Troisieme annee")

    def test_create_enrollment(self):
        enrollment = AnnualEnrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
            gpa=15.5,
        )

        assert enrollment.pk is not None
        assert (
            str(enrollment) == f"{self.student} — {self.academic_year} ({self.level})"
        )

    def test_gpa_nullable(self):
        enrollment = AnnualEnrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
        )

        assert enrollment.gpa is None

    def test_unique_per_student_year(self):
        AnnualEnrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
        )

        with pytest.raises(IntegrityError):
            AnnualEnrollment.objects.create(
                student=self.student,
                academic_year=self.academic_year,
                department=self.department,
                level=self.level,
            )

    def test_parcours_must_match_department(self):
        other_dept = Department.objects.create(code="TC", name="Tronc Commun")
        parcours = Parcours.objects.create(
            department=other_dept, code="IPA", label="IPA"
        )

        enrollment = AnnualEnrollment(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
            parcours=parcours,
        )

        with pytest.raises(ValidationError, match="parcours"):
            enrollment.clean()

    def test_parcours_same_department_accepted(self):
        parcours = Parcours.objects.create(
            department=self.department, code="IPA", label="IPA"
        )

        enrollment = AnnualEnrollment(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
            parcours=parcours,
        )

        enrollment.clean()  # ne doit pas lever d'exception

    def test_parcours_none_accepted(self):
        enrollment = AnnualEnrollment(
            student=self.student,
            academic_year=self.academic_year,
            department=self.department,
            level=self.level,
            parcours=None,
        )

        enrollment.clean()  # ne doit pas lever d'exception
