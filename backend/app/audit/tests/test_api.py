from datetime import timedelta

import pytest
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.utils import timezone

from app.academic.models import AcademicYear

User = get_user_model()


def make_academic_year(label="2026-2027"):
    today = timezone.now().date()
    return AcademicYear.objects.create(
        label=label,
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=335),
    )


def make_log_entry(model_instance, action=LogEntry.Action.CREATE, actor=None):
    ct = ContentType.objects.get_for_model(model_instance)
    return LogEntry.objects.create(
        content_type=ct,
        object_pk=str(model_instance.pk),
        object_id=model_instance.pk,
        object_repr=str(model_instance),
        action=action,
        actor=actor,
        changes={"label": ["old", "new"]} if action == LogEntry.Action.UPDATE else {},
    )


@pytest.mark.django_db
class TestAuditLogAPI:
    def setup_method(self):
        self.client = Client()
        self.year1 = make_academic_year("2026-2027")
        self.year2 = make_academic_year("2027-2028")
        self.log_create = make_log_entry(self.year1, LogEntry.Action.CREATE)
        self.log_update = make_log_entry(self.year2, LogEntry.Action.UPDATE)

    def test_list_audit_logs(self):
        response = self.client.get("/api/v1/audit/logs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_filter_by_entity_type(self):
        response = self.client.get("/api/v1/audit/logs/?entity_type=academicyear")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(entry["entity_type"] == "academicyear" for entry in data)

    def test_filter_by_action_create(self):
        response = self.client.get("/api/v1/audit/logs/?action=create")

        assert response.status_code == 200
        data = response.json()
        assert all(entry["action"] == "create" for entry in data)

    def test_filter_by_action_update(self):
        response = self.client.get("/api/v1/audit/logs/?action=update")

        assert response.status_code == 200
        data = response.json()
        assert all(entry["action"] == "update" for entry in data)

    def test_filter_by_invalid_action(self):
        response = self.client.get("/api/v1/audit/logs/?action=invalid")

        assert response.status_code == 400

    def test_filter_by_actor_username(self):
        user = User.objects.create_user(username="testuser", password="pass")
        make_log_entry(self.year1, actor=user)

        response = self.client.get("/api/v1/audit/logs/?actor_username=testuser")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["actor_username"] == "testuser"

    def test_filter_by_date_range(self):
        today = timezone.now().date()
        date_from = (today - timedelta(days=1)).isoformat()
        date_to = (today + timedelta(days=1)).isoformat()

        response = self.client.get(
            f"/api/v1/audit/logs/?date_from={date_from}&date_to={date_to}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_audit_log_detail(self):
        response = self.client.get(f"/api/v1/audit/logs/{self.log_create.id}/")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.log_create.id
        assert data["action"] == "create"
        assert data["entity_type"] == "academicyear"

    def test_get_audit_log_not_found(self):
        response = self.client.get("/api/v1/audit/logs/99999/")

        assert response.status_code == 404

    def test_log_entry_actor_null(self):
        response = self.client.get(f"/api/v1/audit/logs/{self.log_create.id}/")

        assert response.status_code == 200
        assert response.json()["actor_username"] is None

    def test_response_fields(self):
        response = self.client.get(f"/api/v1/audit/logs/{self.log_create.id}/")

        assert response.status_code == 200
        data = response.json()
        expected_fields = {
            "id",
            "timestamp",
            "actor_username",
            "action",
            "entity_type",
            "entity_id",
            "entity_repr",
            "changes",
        }
        assert expected_fields.issubset(data.keys())
