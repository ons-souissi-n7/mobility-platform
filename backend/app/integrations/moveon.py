import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


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
