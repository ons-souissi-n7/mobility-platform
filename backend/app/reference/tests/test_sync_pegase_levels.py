"""Unit tests for reference/services/sync_pegase_levels.py."""

import pytest

from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.integrations.pegase import PegaseLevel
from app.reference.models import Level
from app.reference.services.sync_pegase_levels import sync_pegase_levels


class FakeClient:
    def __init__(self, payloads):
        self.payloads = payloads

    def fetch_levels(self):
        return [PegaseLevel(payload=payload) for payload in self.payloads]


@pytest.mark.django_db
class TestPegaseLevelSync:
    def test_sync_creates_levels(self):
        result = sync_pegase_levels(FakeClient([level_payload()]))

        assert result.total == 1
        assert result.created == 1
        assert Level.objects.filter(pegase_id="201").exists()
        assert RawImport.objects.filter(
            entity=RawImportEntity.LEVEL,
            status=RawImportStatus.IMPORTED,
        ).exists()

    def test_sync_updates_existing_level(self):
        sync_pegase_levels(FakeClient([level_payload()]))
        payload = level_payload(name="Bachelor Updated")

        result = sync_pegase_levels(FakeClient([payload]))

        level = Level.objects.get(pegase_id="201")
        assert result.created == 0
        assert result.updated == 1
        assert level.name == "Bachelor Updated"

    def test_sync_marks_invalid_payload_as_failed(self):
        payload = level_payload()
        payload.pop("code")

        result = sync_pegase_levels(FakeClient([payload]))

        assert result.failed == 1
        assert not Level.objects.exists()
        assert RawImport.objects.filter(
            entity=RawImportEntity.LEVEL,
            status=RawImportStatus.FAILED,
        ).exists()

    def test_sync_marks_missing_pegase_id_as_failed(self):
        payload = level_payload()
        payload.pop("pegase_id")

        result = sync_pegase_levels(FakeClient([payload]))

        assert result.failed == 1
        assert not Level.objects.exists()

    def test_sync_marks_missing_name_as_failed(self):
        payload = level_payload()
        payload.pop("name")

        result = sync_pegase_levels(FakeClient([payload]))

        assert result.failed == 1

    def test_fallback_finds_manual_level_by_code_and_backfills_pegase_id(self):
        Level.objects.create(code="L1", name="Bachelor", pegase_id=None)

        result = sync_pegase_levels(FakeClient([level_payload()]))

        assert result.created == 0
        assert result.updated == 1
        assert Level.objects.count() == 1
        level = Level.objects.get(code="L1")
        assert level.pegase_id == "201"

    def test_fallback_code_match_is_case_insensitive(self):
        Level.objects.create(code="l1", name="Bachelor", pegase_id=None)

        result = sync_pegase_levels(FakeClient([level_payload()]))

        assert result.created == 0
        assert Level.objects.count() == 1
        level = Level.objects.first()
        assert level.pegase_id == "201"

    def test_empty_payload_list_returns_zero_total(self):
        result = sync_pegase_levels(FakeClient([]))

        assert result.total == 0
        assert result.created == 0


def level_payload(**overrides):
    payload = {
        "pegase_id": 201,
        "code": "L1",
        "name": "Bachelor",
    }
    payload.update(overrides)
    return payload
