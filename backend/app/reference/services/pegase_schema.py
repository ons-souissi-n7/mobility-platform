"""
Définition de la structure attendue des données Pegase brutes.

Si l'API Pegase change sa structure JSON, c'est ici qu'on documente
la transformation entre le payload brut et les données normalisées.
"""

from typing import Any, TypedDict


class PegaseDepartmentRaw(TypedDict, total=False):
    """Structure brute attendue d'un département depuis l'API Pegase."""

    pegase_id: str
    code: str
    name: str


def validate_raw_payload(payload: dict[str, Any]) -> PegaseDepartmentRaw:
    """
    Valide que le payload brut a la structure minimale attendue.

    Lève ValueError si la structure est invalide.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"Payload must be a dict, got {type(payload)}")

    return payload  # type: ignore
