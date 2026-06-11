from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.reference.models import Department, Level, Parcours
from app.students.models import AnnualEnrollment, Student
from app.students.services.student_importer import StudentRow, import_students


def make_row(**kwargs) -> StudentRow:
    defaults = {
        "ine": "12345678901",
        "first_name": "Jean",
        "last_name": "Martin",
        "email": "jean.martin@etud.n7.fr",
        "gender": "M",
        "department_code": "SN",
        "level_code": "3A",
        "parcours_code": None,
        "gpa": 15.5,
    }
    defaults.update(kwargs)
    return StudentRow(**defaults)


@pytest.mark.django_db
class TestImportStudents:
    def setup_method(self):
        self.year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
        )
        self.dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        self.level = Level.objects.create(code="3A", name="Troisieme annee")

    def test_creates_student_and_enrollment(self):
        report = import_students([make_row()], self.year)

        assert report.created == 1
        assert report.updated == 0
        assert report.unresolved == []
        assert report.errors == []
        assert Student.objects.filter(ine="12345678901").exists()
        enrollment = AnnualEnrollment.objects.get(student__ine="12345678901")
        assert float(enrollment.gpa) == 15.5
        assert enrollment.department == self.dept
        assert enrollment.level == self.level
        assert enrollment.parcours is None

    def test_updates_existing_student_fields(self):
        Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="old@email.fr",
        )

        import_students([make_row(email="new@email.fr")], self.year)

        assert Student.objects.get(ine="12345678901").email == "new@email.fr"

    def test_does_not_overwrite_with_empty_fields(self):
        Student.objects.create(
            ine="12345678901",
            first_name="Jean",
            last_name="Martin",
            email="original@email.fr",
        )

        import_students([make_row(email="")], self.year)

        assert Student.objects.get(ine="12345678901").email == "original@email.fr"

    def test_updates_existing_enrollment_gpa(self):
        import_students([make_row(gpa=15.0)], self.year)

        report = import_students([make_row(gpa=16.0)], self.year)

        assert report.updated == 1
        assert report.created == 0
        enrollment = AnnualEnrollment.objects.get(student__ine="12345678901")
        assert float(enrollment.gpa) == 16.0

    def test_unknown_department_marks_as_unresolved(self):
        report = import_students([make_row(department_code="INCONNU")], self.year)

        assert len(report.unresolved) == 1
        assert report.unresolved[0]["ine"] == "12345678901"
        assert "Département introuvable" in report.unresolved[0]["reason"]
        assert not Student.objects.filter(ine="12345678901").exists()

    def test_unknown_level_marks_as_unresolved(self):
        report = import_students([make_row(level_code="INCONNU")], self.year)

        assert len(report.unresolved) == 1
        assert "Niveau introuvable" in report.unresolved[0]["reason"]

    def test_unknown_parcours_marks_as_unresolved(self):
        report = import_students([make_row(parcours_code="INCONNU")], self.year)

        assert len(report.unresolved) == 1
        assert "Parcours introuvable" in report.unresolved[0]["reason"]

    def test_known_parcours_accepted(self):
        parcours = Parcours.objects.create(
            department=self.dept, code="IPA", label="IPA"
        )

        report = import_students([make_row(parcours_code="IPA")], self.year)

        assert report.created == 1
        enrollment = AnnualEnrollment.objects.get(student__ine="12345678901")
        assert enrollment.parcours == parcours

    def test_raw_import_created_on_success(self):
        import_students([make_row()], self.year)

        raw = RawImport.objects.get(
            entity=RawImportEntity.STUDENT, external_id="12345678901"
        )
        assert raw.status == RawImportStatus.IMPORTED
        assert raw.imported_at is not None

    def test_raw_import_failed_on_unknown_department(self):
        import_students([make_row(department_code="INCONNU")], self.year)

        raw = RawImport.objects.get(entity=RawImportEntity.STUDENT)
        assert raw.status == RawImportStatus.FAILED
        assert "INCONNU" in raw.error_message

    def test_department_lookup_case_insensitive(self):
        report = import_students([make_row(department_code="sn")], self.year)

        assert report.created == 1

    def test_level_lookup_case_insensitive(self):
        report = import_students([make_row(level_code="3a")], self.year)

        assert report.created == 1

    def test_multiple_rows_mixed_results(self):
        Level.objects.create(code="4A", name="Quatrieme annee")
        rows = [
            make_row(ine="10000000001", level_code="3A"),
            make_row(ine="10000000002", level_code="4A"),
            make_row(ine="10000000003", department_code="INCONNU"),
        ]

        report = import_students(rows, self.year)

        assert report.created == 2
        assert len(report.unresolved) == 1
        assert Student.objects.count() == 2

    def test_gpa_none_accepted(self):
        report = import_students([make_row(gpa=None)], self.year)

        assert report.created == 1
        enrollment = AnnualEnrollment.objects.get(student__ine="12345678901")
        assert enrollment.gpa is None

    def test_raw_import_linked_to_db_report(self):
        from app.imports.models import ImportReport, ImportSource

        db_report = ImportReport.objects.create(
            source=ImportSource.PEGASE,
            academic_year=self.year,
        )

        import_students([make_row()], self.year, db_report=db_report)

        raw = RawImport.objects.get(entity=RawImportEntity.STUDENT)
        assert raw.import_report == db_report

    def test_db_report_counters_updated(self):
        from app.imports.models import ImportReport, ImportSource

        db_report = ImportReport.objects.create(
            source=ImportSource.PEGASE,
            academic_year=self.year,
        )

        import_students(
            [
                make_row(ine="10000000001"),
                make_row(ine="10000000002", department_code="INCONNU"),
            ],
            self.year,
            db_report=db_report,
        )

        assert db_report.success_count == 1
        assert db_report.error_count == 1
