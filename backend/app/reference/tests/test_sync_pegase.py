import pytest

from app.reference.models import Department, DepartmentRawImport, DepartmentRawImportStatus
from app.reference.services.pegase_client import PegaseDepartment
from app.reference.services.sync_pegase import sync_pegase_departments


class FakeClient:
    def __init__(self, payloads):
        self.payloads = payloads

    def fetch_departments(self):
        return [PegaseDepartment(payload=payload) for payload in self.payloads]


@pytest.mark.django_db
class TestPegaseDepartmentSync:
    def test_sync_creates_departments(self):
        result = sync_pegase_departments(FakeClient([department_payload()]))

        assert result.total == 1
        assert result.created == 1
        assert Department.objects.filter(pegase_id="101").exists()
        assert DepartmentRawImport.objects.filter(
            status=DepartmentRawImportStatus.IMPORTED,
        ).exists()

    def test_sync_updates_existing_department(self):
        sync_pegase_departments(FakeClient([department_payload()]))
        payload = department_payload(name="Sciences du Numerique Updated")

        result = sync_pegase_departments(FakeClient([payload]))

        department = Department.objects.get(pegase_id="101")
        assert result.created == 0
        assert result.updated == 1
        assert department.name == "Sciences du Numerique Updated"

    def test_sync_marks_invalid_payload_as_failed(self):
        payload = department_payload()
        payload.pop("code")

        result = sync_pegase_departments(FakeClient([payload]))

        assert result.failed == 1
        assert not Department.objects.exists()
        assert DepartmentRawImport.objects.filter(
            status=DepartmentRawImportStatus.FAILED,
            error_message__contains="code is required",
        ).exists()


def department_payload(**overrides):
    payload = {
        "pegase_id": 101,
        "code": "SN",
        "name": "Sciences du Numerique",
    }
    payload.update(overrides)
    return payload
