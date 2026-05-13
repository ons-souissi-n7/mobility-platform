import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class MoveOnClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class MoveOnInstitution:
    payload: dict[str, Any]

    @property
    def moveon_id(self) -> int | None:
        value = self.payload.get("moveon_id")
        return int(value) if value not in (None, "") else None


class MoveOnClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.MOVEON_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.MOVEON_API_KEY

    def fetch_institutions(self) -> list[MoveOnInstitution]:
        try:
            response = self._get_json("/institutions")
        except MoveOnClientError:
            response = self._get_json("/api/institutions")

        if not isinstance(response, list):
            raise MoveOnClientError("MoveON institutions endpoint must return a list.")

        return [MoveOnInstitution(payload=item) for item in response]

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
