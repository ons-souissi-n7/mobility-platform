"""
Définition de la structure attendue des données MoveON brutes.

Si l'API MoveON change sa structure JSON, c'est ici qu'on documente
la transformation entre le payload brut et les données normalisées.
"""

from typing import Any, TypedDict


class MoveOnInstitutionRaw(TypedDict, total=False):
    """Structure brute attendue d'une institution depuis MoveON."""

    moveon_id: int | str
    name: str
    short_name: str
    translated_name: str
    erasmus_code: str
    city: str
    url: str
    email: str
    country: dict[str, Any] | str


def validate_raw_payload(payload: dict[str, Any]) -> MoveOnInstitutionRaw:
    """
    Valide que le payload brut a la structure minimale attendue.

    Lève ValueError si la structure est invalide.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"Payload must be a dict, got {type(payload)}")

    return payload  # type: ignore
