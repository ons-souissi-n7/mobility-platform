"""
Transformation des données brutes MoveON en données métier normalisées.

Cette couche est responsable de :
- normaliser les champs
- gérer les encodages
- extraire les données pertinentes

Si le format des données MoveON change (ex: nouveau nom de champ),
on ajuste seulement ici.
"""

from datetime import date, datetime
from typing import Any

from .moveon_schema import validate_raw_payload


def _optional_date(value: Any) -> date | None:
    """Parse date from ISO or DD/MM/YYYY[HH:MM] formats."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


class TransformedInstitution:
    """Données normalisées et prêtes pour l'upsert."""

    def __init__(
        self,
        moveon_id: int,
        name: str,
        short_name: str,
        translated_name: str,
        erasmus_code: str,
        city: str,
        url: str,
        email: str,
        country_payload: dict[str, Any],
        source_updated_at: date | None = None,
    ):
        self.moveon_id = moveon_id
        self.name = name
        self.short_name = short_name
        self.translated_name = translated_name
        self.erasmus_code = erasmus_code
        self.city = city
        self.url = url
        self.email = email
        self.country_payload = country_payload
        self.source_updated_at = source_updated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "moveon_id": self.moveon_id,
            "name": self.name,
            "short_name": self.short_name,
            "translated_name": self.translated_name,
            "erasmus_code": self.erasmus_code,
            "city": self.city,
            "url": self.url,
            "email": self.email,
            "country_payload": self.country_payload,
        }


def transform_institution(payload: dict[str, Any]) -> TransformedInstitution:
    """
    Transforme un payload brut en données normalisées.

    Élève ValueError si le payload ne peut pas être transformé.
    """
    raw = validate_raw_payload(payload)

    moveon_id = raw.get("moveon_id")
    if moveon_id in (None, ""):
        raise ValueError("moveon_id is required")

    country_payload = raw.get("country")
    if isinstance(country_payload, dict):
        country_payload = country_payload
    else:
        country_payload = {"name": str(country_payload or "").strip()}

    return TransformedInstitution(
        moveon_id=int(moveon_id),
        name=str(raw.get("name") or "").strip(),
        short_name=str(raw.get("short_name") or "").strip(),
        translated_name=str(raw.get("translated_name") or "").strip(),
        erasmus_code=str(raw.get("erasmus_code") or "").strip(),
        city=str(raw.get("city") or "").strip(),
        url=str(raw.get("url") or "").strip(),
        email=str(raw.get("email") or "").strip(),
        country_payload=country_payload,
        source_updated_at=_optional_date(
            raw.get("updated_at") or raw.get("date_modification")
        ),
    )
