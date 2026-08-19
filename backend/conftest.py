import pytest


@pytest.fixture(autouse=True)
def inject_admin_jwt(monkeypatch):
    """
    Auto-inject an admin JWT into all django.test.Client instances.

    Tests written before JWT auth was added expected 200 responses; this fixture
    preserves that behaviour without modifying every test file.
    Tests that need a different role can still pass HTTP_AUTHORIZATION explicitly:
        client = Client(HTTP_AUTHORIZATION="Bearer <student_token>")
    """
    from django.test import Client as DjangoClient

    from app.auth.test_utils import make_test_jwt

    token = make_test_jwt(role="admin")
    bearer = f"Bearer {token}"
    original_init = DjangoClient.__init__

    def patched_init(
        self,
        enforce_csrf_checks: bool = False,
        raise_request_exception: bool = True,
        **defaults,
    ) -> None:
        defaults.setdefault("HTTP_AUTHORIZATION", bearer)
        original_init(
            self,
            enforce_csrf_checks=enforce_csrf_checks,
            raise_request_exception=raise_request_exception,
            **defaults,
        )

    monkeypatch.setattr(DjangoClient, "__init__", patched_init)


@pytest.fixture
def api_client():
    """Authenticated admin client (inherits JWT from inject_admin_jwt)."""
    from django.test import Client

    return Client()


@pytest.fixture
def admin_jwt():
    """Raw admin JWT string for explicit header construction."""
    from app.auth.test_utils import make_test_jwt

    return make_test_jwt(role="admin")


@pytest.fixture
def student_jwt():
    """Raw student JWT string (INE 1234567890A)."""
    from app.auth.test_utils import make_test_jwt

    return make_test_jwt(
        email="etudiant@etud.n7.fr",
        role="student",
        ine="1234567890A",
    )
