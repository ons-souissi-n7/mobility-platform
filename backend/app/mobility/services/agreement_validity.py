from __future__ import annotations

from datetime import date

from app.academic.models import AcademicYear
from app.mobility.models import Agreement, AgreementYearAvailability


def is_agreement_valid_for_year(
    agreement: Agreement, academic_year: AcademicYear
) -> bool:
    year_override = get_year_availability_override(agreement, academic_year)
    if year_override is not None:
        return year_override

    if not agreement.is_active:
        return False

    if agreement.status.lower() in {
        "closed",
        "archived",
        "inactive",
        "termine",
        "terminé",
    }:
        return False

    if agreement.start_date and agreement.start_date > academic_year.end_date:
        return False

    if agreement.end_date and agreement.end_date < academic_year.start_date:
        return False

    if not agreement.start_date and agreement.start_academic_year:
        if normalize_year_label(agreement.start_academic_year) > normalize_year_label(
            academic_year.label,
        ):
            return False

    if not agreement.end_date and agreement.end_academic_year:
        if normalize_year_label(agreement.end_academic_year) < normalize_year_label(
            academic_year.label,
        ):
            return False

    return True


def get_year_availability_override(
    agreement: Agreement,
    academic_year: AcademicYear,
) -> bool | None:
    try:
        availability = agreement.year_availabilities.get(
            academic_year_label=academic_year.label,
        )
    except AgreementYearAvailability.DoesNotExist:
        return None

    return availability.is_available


def is_agreement_valid_for_date(agreement: Agreement, day: date) -> bool:
    academic_year = AcademicYear.detect_by_date(day)
    if academic_year is None:
        return False
    return is_agreement_valid_for_year(agreement, academic_year)


def normalize_year_label(label: str) -> str:
    return label.replace("/", "-").strip()
