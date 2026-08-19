import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings


class PegaseClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class PegaseDepartment:
    payload: dict[str, Any]

    @property
    def pegase_id(self) -> str | None:
        value = self.payload.get("pegase_id")
        return str(value) if value not in (None, "") else None


class PegaseClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or settings.PEGASE_API_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.PEGASE_API_KEY

    def fetch_departments(self) -> list[PegaseDepartment]:
        response = self._get("/departments")
        if not isinstance(response, list):
            raise PegaseClientError("Pegase departments endpoint must return a list.")
        return [PegaseDepartment(payload=item) for item in response]

    def _get(self, path: str) -> Any:
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
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
