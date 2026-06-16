"""
Transformation des données brutes Pegase en données métier normalisées.

Cette couche est responsable de :
- normaliser les champs
- gérer les encodages
- extraire les données pertinentes

Si le format des données Pegase change (ex: nouveau nom de champ),
on ajuste seulement ici.
"""

from datetime import date, datetime
from typing import Any

from .pegase_schema import validate_raw_payload


def _optional_date(value: Any) -> date | None:
    """Parse date from ISO or DD/MM/YYYY formats."""
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


class TransformedDepartment:
    """Données normalisées et prêtes pour l'upsert."""

    def __init__(
        self,
        pegase_id: str,
        code: str,
        name: str,
        source_updated_at: date | None = None,
    ):
        self.pegase_id = pegase_id
        self.code = code
        self.name = name
        self.source_updated_at = source_updated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "pegase_id": self.pegase_id,
            "code": self.code,
            "name": self.name,
        }


def transform_department(payload: dict[str, Any]) -> TransformedDepartment:
    """
    Transforme un payload brut en données normalisées.

    Élève ValueError si le payload ne peut pas être transformé.
    """
    raw = validate_raw_payload(payload)

    pegase_id = str(raw.get("pegase_id") or "").strip()
    code = str(raw.get("code") or "").strip()
    name = str(raw.get("name") or "").strip()

    return TransformedDepartment(
        pegase_id=pegase_id,
        code=code,
        name=name,
        source_updated_at=_optional_date(
            raw.get("updated_at") or raw.get("date_modification")
        ),
    )
