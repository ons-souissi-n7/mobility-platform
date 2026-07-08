from __future__ import annotations

from app.academic.models import AcademicYear

from .internship_importer import import_internships_from_excel
from .sync_eudonet import sync_eudonet_internships


def run_sync_eudonet_internships(year_id: int, triggered_by: str = "") -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    sync_eudonet_internships(academic_year=academic_year, triggered_by=triggered_by)


def run_import_excel_internships(
    year_id: int,
    file_bytes: bytes,
    source_file: str,
    triggered_by: str = "",
) -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    import_internships_from_excel(
        file_bytes=file_bytes,
        source_file=source_file,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )
