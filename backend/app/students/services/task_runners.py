from app.academic.models import AcademicYear
from app.imports.models import ImportReport as DbImportReport
from app.imports.models import ImportSource

from .adapters import excel as excel_adapter
from .adapters import excel_wishes as excel_wishes_adapter
from .adapters import pegase as pegase_adapter
from .student_importer import import_students
from .sync_moveon import import_wish_rows, sync_moveon_wishes


def run_sync_pegase_students(year_id: int, triggered_by: str = "") -> None:
    from datetime import date

    academic_year = AcademicYear.objects.get(pk=year_id)
    # Dériver les bornes réelles depuis le label (ex. "2027-2028") plutôt que
    # start_date/end_date qui représentent la période de campagne.
    start_year = int(academic_year.label.split("-")[0])
    rows = pegase_adapter.fetch_enrollments(
        date(start_year, 9, 1),
        date(start_year + 1, 8, 31),
    )
    db_report = DbImportReport.objects.create(
        source=ImportSource.PEGASE,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )
    import_students(rows, academic_year, db_report=db_report, source_file="")
    db_report.finalize()


def run_import_excel_students(
    file_bytes: bytes, source_file: str, year_id: int, triggered_by: str = ""
) -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    rows = excel_adapter.parse(file_bytes)
    db_report = DbImportReport.objects.create(
        source=ImportSource.EXCEL,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )
    import_students(rows, academic_year, db_report=db_report, source_file=source_file)
    db_report.finalize()


def run_sync_moveon_wishes(year_id: int, triggered_by: str = "") -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    sync_moveon_wishes(academic_year=academic_year, triggered_by=triggered_by)


def run_import_excel_wishes(
    file_bytes: bytes, source_file: str, year_id: int, triggered_by: str = ""
) -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    rows = excel_wishes_adapter.parse_wish_excel(file_bytes)
    db_report = DbImportReport.objects.create(
        source=ImportSource.EXCEL,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )
    import_wish_rows(rows, academic_year, db_report=db_report)
    db_report.finalize()
