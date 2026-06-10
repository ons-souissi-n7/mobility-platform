from app.shared.validators import ValidationError

from .pegase_transformer import TransformedDepartment


def validate_department(data: TransformedDepartment) -> None:
    if not data.code:
        raise ValidationError("code is required")
    if not data.name:
        raise ValidationError("name is required")
