import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


def _parse_moveon_date(val: Any) -> date | None:
    """
    Parse a date value from a MoveOn export field.
    Handles French format (DD/MM/YYYY HH:MM), ISO format, and bare dates.
    Returns None if the value is absent or unparseable.
    """
    if val is None or str(val).strip() == "":
        return None
    raw = str(val).strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


class MoveOnClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class MoveOnRecord:
    payload: dict[str, Any]


@dataclass(frozen=True)
class MoveOnInstitution(MoveOnRecord):
    @property
    def moveon_id(self) -> int | None:
        value = self.payload.get("moveon_id")
        return int(value) if value not in (None, "") else None


@dataclass(frozen=True)
class MoveOnAgreement(MoveOnRecord):
    @property
    def relation_id(self) -> str | None:
        value = self.payload.get("moveon_id") or self.payload.get("relation_id")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class MoveOnAgreementFramework(MoveOnRecord):
    @property
    def framework_id(self) -> str | None:
        value = self.payload.get("moveon_framework_id") or self.payload.get("Cadre ID")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class MoveOnAgreementQuota(MoveOnRecord):
    @property
    def places_id(self) -> str | None:
        value = self.payload.get("places_id")
        return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class MoveOnStudentWish(MoveOnRecord):
    """
    Représente une ligne d'export MoveOn "Formulaire de candidature étudiants sortants".

    Colonnes réelles MoveOn utilisées :
      Individu          → identifiant étudiant (INE ou nom)
      No                → rang du vœu (1, 2, 3)
      Offre de séjour   → nom de l'accord MoveOn (pas de moveon_id ici)
      Période de début  → ex. "Semestre 2 - 2026/27" (année extraite)
      Statut Sélection  → filtre : "Candidat", "Sélectionné", etc.
    """

    @property
    def ine(self) -> str:
        return str(
            self.payload.get("Numéro étudiant")
            or self.payload.get("ine")
            or self.payload.get("INE", "")
        ).strip()

    @property
    def individu(self) -> str:
        return str(
            self.payload.get("Individu") or self.payload.get("individu", "")
        ).strip()

    @property
    def rank(self) -> int:
        val = (
            self.payload.get("No")
            or self.payload.get("no")
            or self.payload.get("rank", 0)
        )
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    @property
    def offre_de_sejour(self) -> str:
        return str(
            self.payload.get("Offre de séjour")
            or self.payload.get("offre_de_sejour")
            or self.payload.get("offre", "")
        ).strip()

    @property
    def periode_debut(self) -> str:
        return str(
            self.payload.get("Période de début")
            or self.payload.get("periode_debut", "")
        ).strip()

    @property
    def statut_selection(self) -> str:
        return str(
            self.payload.get("Statut Sélection")
            or self.payload.get("statut_selection", "")
        ).strip()

    @property
    def date_creation(self) -> date | None:
        return _parse_moveon_date(
            self.payload.get("Crée le")
            or self.payload.get("cree_le")
            or self.payload.get("created_at")
        )

    @property
    def date_modification(self) -> date | None:
        return _parse_moveon_date(
            self.payload.get("Dernière modification le")
            or self.payload.get("derniere_modification")
            or self.payload.get("updated_at")
        )


class MoveOnClient:
    """
    Centralise la connexion HTTP vers MoveON.

    Les domaines gardent leurs pipelines ETL, mais partagent le transport,
    l'authentification, les timeouts et les conventions d'endpoints.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.MOVEON_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.MOVEON_API_KEY

    def fetch_institutions(self) -> list[MoveOnInstitution]:
        return [
            MoveOnInstitution(payload=item)
            for item in self._fetch_collection("institutions")
        ]

    def fetch_agreements(self) -> list[MoveOnAgreement]:
        return [
            MoveOnAgreement(payload=item)
            for item in self._fetch_collection("agreements")
        ]

    def fetch_agreement_frameworks(self) -> list[MoveOnAgreementFramework]:
        return [
            MoveOnAgreementFramework(payload=item)
            for item in self._fetch_collection("agreement-frameworks")
        ]

    def fetch_agreement_quotas(self) -> list[MoveOnAgreementQuota]:
        return [
            MoveOnAgreementQuota(payload=item)
            for item in self._fetch_collection("agreement-quotas")
        ]

    def fetch_student_wishes(self) -> list[MoveOnStudentWish]:
        return [
            MoveOnStudentWish(payload=item)
            for item in self._fetch_collection("student-wishes")
        ]

    def _fetch_collection(self, resource: str) -> list[dict[str, Any]]:
        response = self._get_json_with_fallbacks(
            f"/{resource}",
            f"/api/{resource}",
        )

        if not isinstance(response, list):
            raise MoveOnClientError(f"MoveON {resource} endpoint must return a list.")

        return response

    def _get_json_with_fallbacks(self, *paths: str):
        last_error = None

        for path in paths:
            try:
                return self._get_json(path)
            except MoveOnClientError as exc:
                last_error = exc

        raise last_error or MoveOnClientError("MoveON request failed.")

    def _get_json(self, path: str):
        if not self.base_url:
            raise MoveOnClientError("MOVEON_API_URL is not configured.")

        request = Request(
            f"{self.base_url}{path}",
            headers=self._headers(),
            method="GET",
        )

        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MoveOnClientError(f"MoveON request failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
