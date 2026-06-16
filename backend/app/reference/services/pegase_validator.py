from app.shared.validators import DomainValidationError

from .pegase_transformer import TransformedDepartment


def validate_department(data: TransformedDepartment) -> None:
    if not data.pegase_id:
        raise DomainValidationError("Identifiant Pégase manquant — champ obligatoire.")
    if not data.code:
        raise DomainValidationError("Code du département manquant — champ obligatoire.")
    if not data.name:
        raise DomainValidationError("Nom du département manquant — champ obligatoire.")
