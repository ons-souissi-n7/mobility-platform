from typing import Protocol

from app.shared.validators import ValidationError


class _StudentLike(Protocol):
    ine: str
    department_code: str
    level_code: str
    last_name: str


class _WishLike(Protocol):
    offre_de_sejour: str
    rank: int
    ine: str
    individu: str


def validate_student(data: _StudentLike) -> None:
    if not data.ine:
        raise ValidationError("L'INE est requis.")
    if not data.department_code:
        raise ValidationError("Le code département est requis.")
    if not data.level_code:
        raise ValidationError("Le code niveau est requis.")
    if not data.last_name:
        raise ValidationError("Le nom est requis.")


def validate_wish(data: _WishLike) -> None:
    if not data.offre_de_sejour:
        raise ValidationError("L'offre de séjour est requise.")
    if data.rank < 1:
        raise ValidationError("Le rang doit être >= 1.")
    if not data.ine and not data.individu:
        raise ValidationError("L'INE ou le nom de l'individu est requis.")
