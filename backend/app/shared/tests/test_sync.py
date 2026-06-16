"""Unit tests for shared/sync.py — pure Python, no DB required."""

from datetime import date, datetime

from app.shared.sync import SyncConflictError, detect_sync_conflict


class TestSyncConflictError:
    def test_message_without_source_date(self):
        local_dt = datetime(2025, 6, 1, 14, 30)
        err = SyncConflictError(local_updated_at=local_dt)
        assert "01/06/2025" in str(err)
        assert "Synchronisation bloquée" in str(err)
        assert "version source" not in str(err)

    def test_message_with_source_date(self):
        local_dt = datetime(2025, 6, 1, 14, 30)
        src_dt = date(2025, 5, 15)
        err = SyncConflictError(local_updated_at=local_dt, source_updated_at=src_dt)
        assert "15/05/2025" in str(err)
        assert "version source" in str(err)

    def test_attrs_stored(self):
        local_dt = datetime(2025, 6, 1, 14, 30)
        src_dt = date(2025, 5, 15)
        err = SyncConflictError(local_updated_at=local_dt, source_updated_at=src_dt)
        assert err.local_updated_at == local_dt
        assert err.source_updated_at == src_dt

    def test_is_exception(self):
        err = SyncConflictError(local_updated_at=datetime(2025, 1, 1))
        assert isinstance(err, Exception)


class _FakeRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestDetectSyncConflict:
    def test_none_last_sync_returns_none(self):
        rec = _FakeRecord(last_sync_moveon=None, updated_at=datetime(2025, 6, 1))
        assert detect_sync_conflict(rec, "last_sync_moveon") is None

    def test_none_updated_at_returns_none(self):
        rec = _FakeRecord(last_sync_moveon=datetime(2025, 1, 1), updated_at=None)
        assert detect_sync_conflict(rec, "last_sync_moveon") is None

    def test_unmodified_record_returns_none(self):
        ts = datetime(2025, 6, 1)
        rec = _FakeRecord(last_sync_moveon=ts, updated_at=ts)
        assert detect_sync_conflict(rec, "last_sync_moveon") is None

    def test_locally_modified_returns_conflict(self):
        sync_ts = datetime(2025, 5, 1)
        rec = _FakeRecord(last_sync_moveon=sync_ts, updated_at=datetime(2025, 6, 1))
        result = detect_sync_conflict(
            rec, "last_sync_moveon", source_updated_at=date(2025, 5, 15)
        )
        assert isinstance(result, SyncConflictError)
        assert result.source_updated_at == date(2025, 5, 15)
