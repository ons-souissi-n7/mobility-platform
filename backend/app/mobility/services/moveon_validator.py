from .moveon_transformer import (
    TransformedAgreement,
    TransformedAgreementQuota,
    TransformedMobilityCategory,
)


class ValidationError(ValueError):
    pass


def validate_mobility_category(category: TransformedMobilityCategory) -> None:
    if not category.moveon_framework_id:
        raise ValidationError("moveon_framework_id is required")
    if not category.name:
        raise ValidationError("name is required")


def validate_agreement(agreement: TransformedAgreement) -> None:
    if not agreement.moveon_relation_id:
        raise ValidationError("moveon_relation_id is required")
    if not agreement.name:
        raise ValidationError("name is required")
    if not any(
        [
            agreement.partner_university_moveon_id,
            agreement.partner_university_id,
            agreement.partner_university_erasmus_code,
            agreement.partner_university_name,
        ]
    ):
        raise ValidationError(
            "partner_university reference is required "
            "(MoveON id, Erasmus code or university name)"
        )
    if (
        agreement.start_date
        and agreement.end_date
        and agreement.start_date > agreement.end_date
    ):
        raise ValidationError("start_date must be before end_date")


def validate_agreement_quota(quota: TransformedAgreementQuota) -> None:
    if not quota.moveon_relation_id and not quota.agreement_id:
        raise ValidationError("moveon_relation_id is required")
    if not quota.academic_year_label:
        raise ValidationError("academic_year_label is required")
    if quota.total_places < 0:
        raise ValidationError("total_places cannot be negative")
    if quota.remaining_places < 0:
        raise ValidationError("remaining_places cannot be negative")
    if quota.remaining_places > quota.total_places:
        raise ValidationError("remaining_places cannot exceed total_places")
    if quota.total_duration is not None and quota.total_duration < 0:
        raise ValidationError("total_duration cannot be negative")
