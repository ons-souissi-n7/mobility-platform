from typing import Any, TypedDict


class MoveOnAgreementRaw(TypedDict, total=False):
    moveon_id: str | int
    relation_id: str | int
    reference: str
    name: str
    partner_university_moveon_id: int | str
    partner_moveon_id: int | str
    partner_university_id: int | str
    relation_type: str
    framework: str
    direction: str
    status: str
    is_active: bool
    start_date: str
    end_date: str
    start_academic_year: str
    end_academic_year: str
    discipline: str
    isced: str
    level: str
    formation: str
    url: str
    restrictions: str
    remarks: str


class MoveOnAgreementQuotaRaw(TypedDict, total=False):
    moveon_id: str | int
    agreement_id: int | str
    academic_year_id: int | str
    academic_year_label: str
    period: str
    places_id: str | int
    total_places: int | str
    remaining_places: int | str
    total_duration: int | str
    duration_unit: str
    is_effective: bool
    remarks: str


def validate_raw_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"Payload must be a dict, got {type(payload)}")

    return payload
