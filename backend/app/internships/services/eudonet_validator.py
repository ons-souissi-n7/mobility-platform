from __future__ import annotations

from app.integrations.eudonet import EudonetInternship
from app.shared.validators import DomainValidationError


def validate_internship_row(row: EudonetInternship) -> None:
    if not row.ine:
        raise DomainValidationError("L'INE est requis.")
    if not row.company_name:
        raise DomainValidationError("La raison sociale est requise.")
    if row.start_date is None:
        raise DomainValidationError("La date de début est requise.")
