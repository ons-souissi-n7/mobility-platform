from django_q.tasks import async_task

SYNC_PEGASE_DEPARTMENTS_TASK = (
    "app.reference.services.sync_pegase.sync_pegase_departments"
)
SYNC_PEGASE_DEPARTMENTS_GROUP = "pegase-departments-sync"
SYNC_PEGASE_DEPARTMENTS_TASK_NAME = "Pegase departments sync"


def enqueue_sync_pegase_departments() -> str:
    return async_task(
        SYNC_PEGASE_DEPARTMENTS_TASK,
        group=SYNC_PEGASE_DEPARTMENTS_GROUP,
        task_name=SYNC_PEGASE_DEPARTMENTS_TASK_NAME,
    )
