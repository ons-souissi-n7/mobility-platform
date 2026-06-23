from django_q.tasks import async_task


def enqueue_sync_pegase_students(year_id: int, triggered_by: str = "") -> str:
    return async_task(
        "app.students.services.task_runners.run_sync_pegase_students",
        year_id,
        triggered_by,
        group="pegase-students-sync",
        task_name="Pegase students sync",
    )


def enqueue_import_excel_students(
    file_bytes: bytes, source_file: str, year_id: int, triggered_by: str = ""
) -> str:
    return async_task(
        "app.students.services.task_runners.run_import_excel_students",
        file_bytes,
        source_file,
        year_id,
        triggered_by,
        group="excel-students-import",
        task_name="Excel students import",
    )
