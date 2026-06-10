"""Validation des règles métier pour MoveON.

Cette couche valide que les données transformées respectent les contraintes métier.
Séparé de la transformation car les règles sont métier, pas structurelles.
"""

from app.shared.validators import ValidationError

from .moveon_transformer import TransformedInstitution


def validate_institution(data: TransformedInstitution) -> None:
    """
    Valide qu'une institution respecte les règles métier.

    Lève ValidationError si une règle est violée.
    """
    if not data.moveon_id:
        raise ValidationError("moveon_id is required")

    if not data.name:
        raise ValidationError("name is required")

    if not data.country_payload:
        raise ValidationError("country payload is required")
