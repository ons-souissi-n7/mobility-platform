from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from django.utils import timezone

from app.imports.models import RawImport, RawImportStatus


class SyncConflictError(Exception):
    """
    Raised when a sync would overwrite a locally-modified record with older source data.

    The sync loop catches this, marks the RawImport as CONFLICT, and records it in the
    ImportReport so the user can choose to force the overwrite via the API.
    """

    def __init__(
        self,
        local_updated_at: datetime,
        source_updated_at: date | None = None,
    ) -> None:
        self.local_updated_at = local_updated_at
        self.source_updated_at = source_updated_at
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        local_str = self.local_updated_at.strftime("%d/%m/%Y à %H:%M")
        msg = f"Cet enregistrement a été modifié localement le {local_str}"
        if self.source_updated_at is not None:
            src_str = self.source_updated_at.strftime("%d/%m/%Y")
            msg += f" (version source : {src_str})"
        msg += ". Synchronisation bloquée — cliquez sur « Forcer » pour écraser la version locale."
        return msg


def record_is_unchanged(record: Any, **incoming: Any) -> bool:
    """
    Return True if every incoming field value matches the record's current value.

    None and "" are treated as equivalent for string fields so that a source
    sending None for an optional field does not trigger a spurious conflict against
    a DB row that stores "".
    """
    for field, value in incoming.items():
        current = getattr(record, field)
        if isinstance(value, str) or isinstance(current, str):
            if (value or "") != (current or ""):
                return False
        elif value != current:
            return False
    return True


def touch_last_sync(record: Any, attr: str) -> None:
    """Refresh the last_sync_* timestamp without touching updated_at."""
    type(record).objects.filter(pk=record.pk).update(**{attr: timezone.now()})


def already_up_to_date(
    record: Any,
    last_sync_attr: str,
    source_updated_at: date | None = None,
    **incoming_fields: Any,
) -> bool:
    """
    Return True (and refresh last_sync_*) when the record needs no update.

    1. If source_updated_at is provided and last_sync already covers it, the
       record already reflects the latest external version — skip.
    2. If source_updated_at is absent, fall back to comparing field values.

    The last_sync_* timestamp is refreshed so the next run knows this record
    was verified on the current sync date.
    """
    last_sync: datetime | None = getattr(record, last_sync_attr, None)
    if last_sync is None:
        return False  # Never synced — always process

    # Primary: timestamp says we're already at the latest version — fast path
    if source_updated_at is not None and last_sync.date() >= source_updated_at:
        touch_last_sync(record, last_sync_attr)
        return True

    # Fallback: compare field values even when the source timestamp is newer.
    # This covers two cases:
    # 1. source_updated_at is absent (Pégase doesn't always provide it)
    # 2. source_updated_at is newer but the tracked fields are identical — the
    #    source may have bumped its timestamp without changing any data we store,
    #    OR the DB has updated_at > last_sync due to legacy import ordering.
    if incoming_fields and record_is_unchanged(record, **incoming_fields):
        touch_last_sync(record, last_sync_attr)
        return True

    return False


def detect_sync_conflict(
    record: Any,
    last_sync_attr: str,
    source_updated_at: date | None = None,
) -> SyncConflictError | None:
    """
    Return a SyncConflictError if the record was locally modified after the last sync.

    Args:
        record: Django model instance with updated_at and a last_sync_* field.
        last_sync_attr: Attribute name of the last-sync timestamp (e.g. 'last_sync_moveon').
        source_updated_at: Update date from the external payload (shown in the message).

    Returns None when there is no conflict (record unmodified, or never synced).
    """
    last_sync: datetime | None = getattr(record, last_sync_attr, None)
    if last_sync is None:
        return None  # Never synced — no baseline to compare against
    updated_at: datetime | None = getattr(record, "updated_at", None)
    if updated_at is None:
        return None
    if updated_at <= last_sync:
        return None  # Not modified since last sync — safe to overwrite
    return SyncConflictError(updated_at, source_updated_at)


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    conflicted: int = 0
    total: int = 0


def mark_raw_import(
    raw_import: RawImport,
    status: RawImportStatus,
    error_message: str = "",
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == RawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )
