import pytest
from django.test import Client

from app.alerts.models import SystemAlert


def make_alert(**kwargs) -> SystemAlert:
    defaults = {
        "level": "warning",
        "title": "Vœux incompatibles avec le niveau",
        "message": "2 étudiant(s) ont des vœux incompatibles.",
    }
    defaults.update(kwargs)
    return SystemAlert.objects.create(**defaults)


@pytest.mark.django_db
class TestListAlerts:
    def setup_method(self):
        self.client = Client()

    def test_lists_unread_alerts_ordered_by_most_recent(self):
        a1 = make_alert(title="Alerte 1")
        a2 = make_alert(title="Alerte 2")

        response = self.client.get("/api/v1/alerts/")

        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert ids == [a2.id, a1.id]

    def test_excludes_read_alerts(self):
        make_alert(title="Lue", is_read=True)
        unread = make_alert(title="Non lue")

        response = self.client.get("/api/v1/alerts/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == unread.id

    def test_excludes_alerts_acknowledged_by_current_user(self, django_user_model):
        user = django_user_model.objects.create_user(username="ci-user", password="x")
        self.client.force_login(user)
        make_alert(title="Acquittée", acknowledged_usernames=["ci-user"])
        visible = make_alert(title="Visible")

        response = self.client.get("/api/v1/alerts/")

        assert response.status_code == 200
        ids = {item["id"] for item in response.json()}
        assert ids == {visible.id}

    def test_shows_alert_to_user_who_has_not_acknowledged_it(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="other-user", password="x"
        )
        self.client.force_login(user)
        alert = make_alert(
            title="Acquittée par un autre", acknowledged_usernames=["ci-user"]
        )

        response = self.client.get("/api/v1/alerts/")

        assert response.status_code == 200
        ids = {item["id"] for item in response.json()}
        assert alert.id in ids


@pytest.mark.django_db
class TestAcknowledgeAlert:
    def setup_method(self):
        self.client = Client()

    def test_acknowledge_marks_current_user(self):
        alert = make_alert()

        response = self.client.post(f"/api/v1/alerts/{alert.id}/acknowledge/")

        assert response.status_code == 204
        alert.refresh_from_db()
        assert alert.acknowledged_usernames == ["unknown"]
        assert alert.is_read is False

    def test_acknowledge_is_idempotent(self):
        alert = make_alert(acknowledged_usernames=["unknown"])

        response = self.client.post(f"/api/v1/alerts/{alert.id}/acknowledge/")

        assert response.status_code == 204
        alert.refresh_from_db()
        assert alert.acknowledged_usernames == ["unknown"]

    def test_returns_404_for_unknown_alert(self):
        response = self.client.post("/api/v1/alerts/99999/acknowledge/")
        assert response.status_code == 404

    def test_returns_404_when_already_read(self):
        alert = make_alert(is_read=True)
        response = self.client.post(f"/api/v1/alerts/{alert.id}/acknowledge/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestResolveAlert:
    def setup_method(self):
        self.client = Client()

    def test_resolve_marks_alert_as_read(self):
        alert = make_alert()

        response = self.client.post(f"/api/v1/alerts/{alert.id}/resolve/")

        assert response.status_code == 204
        alert.refresh_from_db()
        assert alert.is_read is True
        assert alert.read_at is not None

    def test_returns_404_for_unknown_alert(self):
        response = self.client.post("/api/v1/alerts/99999/resolve/")
        assert response.status_code == 404

    def test_returns_404_when_already_resolved(self):
        alert = make_alert(is_read=True)
        response = self.client.post(f"/api/v1/alerts/{alert.id}/resolve/")
        assert response.status_code == 404
