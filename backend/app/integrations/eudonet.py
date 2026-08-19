from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings


def _parse_eudonet_date(val: Any) -> date | None:
    """
    Parse a date value from an Eudonet export field.
    Handles French format with seconds (DD/MM/YYYY HH:MM:SS), without seconds
    (DD/MM/YYYY HH:MM), bare date (DD/MM/YYYY), and ISO formats.
    Returns None if the value is absent or unparseable.
    """
    if val is None or str(val).strip() == "":
        return None
    raw = str(val).strip()
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_eudonet_datetime(val: Any) -> datetime | None:
    """
    Parse a datetime value from an Eudonet export field.
    Returns None if the value is absent or unparseable.
    """
    if val is None or str(val).strip() == "":
        return None
    raw = str(val).strip()
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


class EudonetClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class EudonetRecord:
    payload: dict[str, Any]


@dataclass(frozen=True)
class EudonetInternship(EudonetRecord):
    @property
    def ine(self) -> str:
        return str(self.payload.get("N°INE") or self.payload.get("ine") or "").strip()

    @property
    def libelle(self) -> str:
        return str(
            self.payload.get("Libellé") or self.payload.get("libelle") or ""
        ).strip()

    @property
    def company_name(self) -> str:
        return str(
            self.payload.get("Raison sociale") or self.payload.get("company_name") or ""
        ).strip()

    @property
    def country_name(self) -> str:
        return str(
            self.payload.get("Pays") or self.payload.get("country_name") or ""
        ).strip()

    @property
    def city(self) -> str:
        return str(self.payload.get("Ville") or self.payload.get("city") or "").strip()

    @property
    def internship_type(self) -> str:
        return str(
            self.payload.get("Type") or self.payload.get("internship_type") or ""
        ).strip()

    @property
    def status(self) -> str:
        return str(
            self.payload.get("Statut") or self.payload.get("status") or ""
        ).strip()

    @property
    def status_code(self) -> str:
        stored = str(self.payload.get("status_code") or "").strip()
        if stored.isdigit():
            return stored
        parts = self.status.split(" ", 1)
        code = parts[0] if parts else ""
        return code if code.isdigit() else ""

    @property
    def start_date(self) -> date | None:
        return _parse_eudonet_date(
            self.payload.get("Date de début") or self.payload.get("start_date")
        )

    @property
    def end_date(self) -> date | None:
        return _parse_eudonet_date(
            self.payload.get("Date de fin") or self.payload.get("end_date")
        )

    @property
    def weeks(self) -> int | None:
        val = self.payload.get("Nb semaines dans l'entreprise") or self.payload.get(
            "weeks"
        )
        if val is None or str(val).strip() == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    @property
    def school_tutor(self) -> str:
        return str(
            self.payload.get("Tuteur pédagogique Ecole")
            or self.payload.get("school_tutor")
            or ""
        ).strip()

    @property
    def company_tutor(self) -> str:
        return str(
            self.payload.get("Tuteur technique entreprise")
            or self.payload.get("company_tutor")
            or ""
        ).strip()

    @property
    def title(self) -> str:
        return str(self.payload.get("Titre") or self.payload.get("title") or "").strip()

    @property
    def modified_at(self) -> datetime | None:
        return _parse_eudonet_datetime(self.payload.get("Modifié le"))

    @property
    def is_international(self) -> bool:
        val = str(self.payload.get("Mobilité à l'international", "") or "").strip()
        return val.lower() == "oui"

    @property
    def composante(self) -> str:
        return str(self.payload.get("Composante", "") or "").strip()


class EudonetClient:
    """
    Centralise la connexion HTTP vers Eudonet.

    Fournit le transport, l'authentification, les timeouts et les conventions
    d'endpoints pour les données de stages.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.EUDONET_API_URL).rstrip("/")
        self.api_key = (
            api_key if api_key is not None else getattr(settings, "EUDONET_API_KEY", "")
        )

    def fetch_internships(self) -> list[EudonetInternship]:
        return [
            EudonetInternship(payload=item)
            for item in self._fetch_collection("internships")
        ]

    def _fetch_collection(self, resource: str) -> list[dict[str, Any]]:
        response = self._get_json_with_fallbacks(
            f"/{resource}",
            f"/api/{resource}",
        )

        if not isinstance(response, list):
            raise EudonetClientError(f"Eudonet {resource} endpoint must return a list.")

        return response

    def _get_json_with_fallbacks(self, *paths: str):
        last_error = None

        for path in paths:
            try:
                return self._get_json(path)
            except EudonetClientError as exc:
                last_error = exc

        raise last_error or EudonetClientError("Eudonet request failed.")

    def _get_json(self, path: str):
        if not self.base_url:
            raise EudonetClientError("EUDONET_API_URL is not configured.")

        request = Request(
            f"{self.base_url}{path}",
            headers=self._headers(),
            method="GET",
        )

        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EudonetClientError(f"Eudonet request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
