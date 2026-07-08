from __future__ import annotations

from django_q.tasks import async_task


def enqueue_import_excel_incoming(
    year_id: int, file_bytes: bytes, source_file: str, triggered_by: str = ""
) -> str:
    return async_task(
        "app.incoming.services.task_runners.run_import_excel_incoming",
        year_id,
        file_bytes,
        source_file,
        triggered_by,
        group="excel-incoming-import",
        task_name="Excel incoming students import",
    )
