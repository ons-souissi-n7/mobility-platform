import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings


class PegaseClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class PegaseRecord:
    payload: dict[str, Any]


@dataclass(frozen=True)
class PegaseDepartment(PegaseRecord):
    @property
    def pegase_id(self) -> str | None:
        value = self.payload.get("pegase_id")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class PegaseLevel(PegaseRecord):
    @property
    def pegase_id(self) -> str | None:
        value = self.payload.get("pegase_id")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class PegaseStudent(PegaseRecord):
    @property
    def ine(self) -> str | None:
        value = self.payload.get("ine")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class PegaseEnrollment(PegaseRecord):
    @property
    def ine(self) -> str | None:
        value = self.payload.get("ine")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class PegaseGpaRecord(PegaseRecord):
    @property
    def ine(self) -> str | None:
        value = self.payload.get("ine")
        return str(value) if value not in (None, "") else None


class PegaseClient:
    """
    Centralise la connexion HTTP vers Pegase.

    Les pipelines metier restent isoles par domaine, mais partagent le transport,
    l'authentification, les timeouts et la convention d'endpoints.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.PEGASE_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.PEGASE_API_KEY

    def fetch_departments(self) -> list[PegaseDepartment]:
        return [
            PegaseDepartment(payload=item)
            for item in self._fetch_collection("departments")
        ]

    def fetch_levels(self) -> list[PegaseLevel]:
        return [PegaseLevel(payload=item) for item in self._fetch_collection("levels")]

    def fetch_students(self) -> list[PegaseStudent]:
        return [
            PegaseStudent(payload=item) for item in self._fetch_collection("students")
        ]

    def fetch_enrollments(self) -> list[PegaseEnrollment]:
        return [
            PegaseEnrollment(payload=item)
            for item in self._fetch_collection("enrollments")
        ]

    def fetch_gpa_records(self) -> list[PegaseGpaRecord]:
        return [
            PegaseGpaRecord(payload=item)
            for item in self._fetch_collection("gpa-records")
        ]

    def _fetch_collection(self, resource: str) -> list[dict[str, Any]]:
        response = self._get_json_with_fallbacks(
            f"/{resource}",
            f"/api/{resource}",
        )

        if not isinstance(response, list):
            raise PegaseClientError(f"Pegase {resource} endpoint must return a list.")

        return response

    def _get_json_with_fallbacks(self, *paths: str):
        last_error = None

        for path in paths:
            try:
                return self._get_json(path)
            except PegaseClientError as exc:
                last_error = exc

        raise last_error or PegaseClientError("Pegase request failed.")

    def _get_json(self, path: str):
        if not self.base_url:
            raise PegaseClientError("PEGASE_API_URL is not configured.")

        request = Request(
            f"{self.base_url}{path}",
            headers=self._headers(),
            method="GET",
        )

        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PegaseClientError(f"Pegase request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
