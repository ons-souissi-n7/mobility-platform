from __future__ import annotations

from app.academic.models import AcademicYear

from .excel_importer import import_incoming_from_excel


def run_import_excel_incoming(
    year_id: int,
    file_bytes: bytes,
    source_file: str,
    triggered_by: str = "",
) -> None:
    academic_year = AcademicYear.objects.get(pk=year_id)
    import_incoming_from_excel(
        file_bytes=file_bytes,
        source_file=source_file,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )
