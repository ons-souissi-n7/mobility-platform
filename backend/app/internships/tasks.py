from __future__ import annotations

from django_q.tasks import async_task


def enqueue_sync_eudonet_internships(year_id: int, triggered_by: str = "") -> str:
    return async_task(
        "app.internships.services.task_runners.run_sync_eudonet_internships",
        year_id,
        triggered_by,
        group="eudonet-internships-sync",
        task_name="Eudonet internships sync",
    )


def enqueue_import_excel_internships(
    year_id: int, file_bytes: bytes, source_file: str, triggered_by: str = ""
) -> str:
    return async_task(
        "app.internships.services.task_runners.run_import_excel_internships",
        year_id,
        file_bytes,
        source_file,
        triggered_by,
        group="excel-internships-import",
        task_name="Excel internships import",
    )
