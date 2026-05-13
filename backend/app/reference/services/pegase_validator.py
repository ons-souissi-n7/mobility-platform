"""
Validation des règles métier pour Pegase.

Cette couche valide que les données transformées respectent les contraintes métier.
Si les règles métier changent (ex: pegase_id obligatoire), on ajuste ici.

Séparé de la transformation car les règles sont métier, pas structurelles.
"""
from .pegase_transformer import TransformedDepartment


class ValidationError(Exception):
    """Levée quand les données ne respectent pas les règles métier."""
    pass


def validate_department(data: TransformedDepartment) -> None:
    """
    Valide qu'un département respecte les règles métier.
    
    Lève ValidationError si une règle est violée.
    """
    if not data.pegase_id:
        raise ValidationError("pegase_id is required")
    
    if not data.code:
        raise ValidationError("code is required")
    
    if not data.name:
        raise ValidationError("name is required")
