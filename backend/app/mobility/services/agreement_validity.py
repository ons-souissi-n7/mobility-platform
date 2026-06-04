from __future__ import annotations

from app.academic.models import AcademicYear
from app.mobility.models import Agreement, AgreementYear


def is_agreement_active_for_year(
    agreement: Agreement, academic_year: AcademicYear
) -> bool:
    """
    Checks AgreementYear.is_active if an instance exists (manual override),
    otherwise falls back to date-based validity check.
    """
    try:
        instance = AgreementYear.objects.get(
            agreement=agreement, academic_year=academic_year
        )
        return instance.is_active
    except AgreementYear.DoesNotExist:
        return is_within_validity(agreement, academic_year)


def is_within_validity(agreement: Agreement, academic_year: AcademicYear) -> bool:
    """
    Returns True if the agreement's validity period overlaps with the academic year.
    - No valid_from set → not yet started restriction, assumed valid.
    - No valid_until set → open-ended, assumed valid.
    """
    if agreement.valid_from and agreement.valid_from > academic_year.end_date:
        return False
    if agreement.valid_until and agreement.valid_until < academic_year.start_date:
        return False
    return True
