from app.shared.validators import DomainValidationError

from .pegase_transformer import TransformedDepartment


def validate_department(data: TransformedDepartment) -> None:
    if not data.code:
        raise DomainValidationError("code is required")
    if not data.name:
        raise DomainValidationError("name is required")
