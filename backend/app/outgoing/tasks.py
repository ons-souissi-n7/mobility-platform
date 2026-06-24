from django_q.tasks import async_task


def enqueue_gale_shapley(year_id: int, triggered_by: str = "") -> str:
    return async_task(
        "app.outgoing.services.task_runners.run_gale_shapley",
        year_id,
        triggered_by,
        group="gale-shapley",
        task_name="Gale-Shapley assignment",
    )


def enqueue_sync_moveon_wishes(year_id: int, triggered_by: str = "") -> str:
    return async_task(
        "app.students.services.task_runners.run_sync_moveon_wishes",
        year_id,
        triggered_by,
        group="moveon-wishes-sync",
        task_name="MoveON wishes sync",
    )


def enqueue_import_excel_wishes(
    file_bytes: bytes, source_file: str, year_id: int, triggered_by: str = ""
) -> str:
    return async_task(
        "app.students.services.task_runners.run_import_excel_wishes",
        file_bytes,
        source_file,
        year_id,
        triggered_by,
        group="excel-wishes-import",
        task_name="Excel wishes import",
    )
