from django_q.tasks import async_task

SYNC_MOVEON_MOBILITY_TASK = "app.mobility.services.sync_moveon.sync_moveon_mobility"
SYNC_MOVEON_MOBILITY_GROUP = "moveon-mobility-sync"
SYNC_MOVEON_MOBILITY_TASK_NAME = "MoveON mobility sync"

SYNC_MOVEON_MOBILITY_CATEGORIES_TASK = (
    "app.mobility.services.sync_moveon.sync_moveon_mobility_categories"
)
SYNC_MOVEON_MOBILITY_CATEGORIES_GROUP = "moveon-mobility-categories-sync"
SYNC_MOVEON_MOBILITY_CATEGORIES_TASK_NAME = "MoveON mobility categories sync"

SYNC_EXCEL_AGREEMENTS_TASK = (
    "app.mobility.services.sync_excel.sync_agreements_from_excel"
)
SYNC_EXCEL_AGREEMENTS_GROUP = "excel-agreements-sync"
SYNC_EXCEL_AGREEMENTS_TASK_NAME = "Excel agreements import"


def enqueue_sync_moveon_mobility() -> str:
    return async_task(
        SYNC_MOVEON_MOBILITY_TASK,
        group=SYNC_MOVEON_MOBILITY_GROUP,
        task_name=SYNC_MOVEON_MOBILITY_TASK_NAME,
    )


def enqueue_sync_moveon_mobility_categories() -> str:
    return async_task(
        SYNC_MOVEON_MOBILITY_CATEGORIES_TASK,
        group=SYNC_MOVEON_MOBILITY_CATEGORIES_GROUP,
        task_name=SYNC_MOVEON_MOBILITY_CATEGORIES_TASK_NAME,
    )


def enqueue_sync_excel_agreements(file_bytes: bytes, source_file: str) -> str:
    return async_task(
        SYNC_EXCEL_AGREEMENTS_TASK,
        file_bytes,
        source_file,
        group=SYNC_EXCEL_AGREEMENTS_GROUP,
        task_name=SYNC_EXCEL_AGREEMENTS_TASK_NAME,
    )
