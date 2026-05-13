"""
Transformation des données brutes Pegase en données métier normalisées.

Cette couche est responsable de :
- normaliser les champs
- gérer les encodages
- extraire les données pertinentes

Si le format des données Pegase change (ex: nouveau nom de champ),
on ajuste seulement ici.
"""

from typing import Any

from .pegase_schema import PegaseDepartmentRaw, validate_raw_payload


class TransformedDepartment:
    """Données normalisées et prêtes pour l'upsert."""

    def __init__(
        self,
        pegase_id: str,
        code: str,
        name: str,
    ):
        self.pegase_id = pegase_id
        self.code = code
        self.name = name

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
    )
