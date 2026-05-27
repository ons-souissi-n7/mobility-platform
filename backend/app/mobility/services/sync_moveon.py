from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.integrations.moveon import MoveOnClient
from app.mobility.models import (
    Agreement,
    AgreementDepartmentConstraint,
    AgreementLevelConstraint,
    AgreementQuota,
    AgreementYearAvailability,
    DepartmentQuota,
    MobilityCategory,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Department, Level

from .moveon_transformer import (
    TransformedAgreement,
    TransformedAgreementAvailability,
    TransformedAgreementQuota,
    TransformedMobilityCategory,
    transform_agreement,
    transform_agreement_quota,
    transform_mobility_category,
)
from .moveon_validator import ValidationError as MoveOnValidationError
from .moveon_validator import (
    validate_agreement,
    validate_agreement_quota,
    validate_mobility_category,
)
from .quota_estimator import (
    create_estimated_department_quotas,
    estimate_n7_places_from_inp_quota,
)


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    total: int = 0


@dataclass
class MobilitySyncResult:
    frameworks: SyncResult
    agreements: SyncResult
    quotas: SyncResult


def sync_moveon_mobility(client: MoveOnClient | None = None) -> MobilitySyncResult:
    client = client or MoveOnClient()
    frameworks = sync_moveon_mobility_categories(client)
    agreements = sync_moveon_agreements(client)
    quotas = sync_moveon_agreement_quotas(client)
    return MobilitySyncResult(
        frameworks=frameworks, agreements=agreements, quotas=quotas
    )


def sync_moveon_mobility_categories(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    for framework in client.fetch_agreement_frameworks():
        result.total += 1
        payload = framework.payload
        raw_import = create_raw_import(payload, RawImportEntity.AGREEMENT_FRAMEWORK)

        try:
            transformed = transform_mobility_category(payload)
            validate_mobility_category(transformed)
            created = upsert_mobility_category(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    return result


def sync_moveon_agreements(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    for agreement in client.fetch_agreements():
        result.total += 1
        payload = agreement.payload
        raw_import = create_raw_import(payload, RawImportEntity.AGREEMENT)

        try:
            transformed = transform_agreement(payload)
            validate_agreement(transformed)
            created = upsert_agreement(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    return result


def sync_moveon_agreement_quotas(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    for quota in client.fetch_agreement_quotas():
        result.total += 1
        payload = quota.payload
        raw_import = create_raw_import(payload, RawImportEntity.AGREEMENT_QUOTA)

        try:
            transformed = transform_agreement_quota(payload)
            validate_agreement_quota(transformed)
            created = upsert_agreement_quota(transformed)
        except (
            Agreement.DoesNotExist,
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    return result


def create_raw_import(payload: dict[str, Any], entity: RawImportEntity) -> RawImport:
    return RawImport.objects.create(
        source=f"moveon_fake_{entity.value}",
        source_file="",
        entity=entity,
        external_id=get_external_id(payload, entity),
        payload=payload,
    )


def get_external_id(payload: dict[str, Any], entity: RawImportEntity) -> str:
    if entity == RawImportEntity.AGREEMENT_FRAMEWORK:
        return str(payload.get("moveon_framework_id") or payload.get("Cadre ID") or "")
    if entity == RawImportEntity.AGREEMENT:
        return str(
            payload.get("moveon_relation_id") or payload.get("relation_id") or ""
        )
    if entity == RawImportEntity.AGREEMENT_QUOTA:
        return str(payload.get("places_id") or payload.get("Places: ID") or "")
    return ""


def mark_raw_import(
    raw_import: RawImport,
    status: RawImportStatus,
    error_message: str = "",
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == RawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )


@transaction.atomic
def upsert_agreement(transformed_data: TransformedAgreement | dict[str, Any]) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_agreement(transformed_data)
        validate_agreement(transformed_data)

    try:
        partner_university = resolve_partner_university(transformed_data)
    except PartnerUniversity.DoesNotExist as exc:
        raise ValueError("Missing partner university reference") from exc

    framework_ref = resolve_mobility_category(transformed_data.framework)
    defaults = {
        "reference": transformed_data.reference,
        "name": transformed_data.name,
        "partner_university": partner_university,
        "relation_type": transformed_data.relation_type,
        "framework": transformed_data.framework,
        "framework_ref": framework_ref,
        "direction": transformed_data.direction,
        "status": transformed_data.status,
        "is_active": transformed_data.is_active,
        "start_date": transformed_data.start_date,
        "end_date": transformed_data.end_date,
        "start_academic_year": transformed_data.start_academic_year,
        "end_academic_year": transformed_data.end_academic_year,
        "discipline": transformed_data.discipline,
        "isced": transformed_data.isced,
        "level": transformed_data.level,
        "formation": transformed_data.formation,
        "url": transformed_data.url,
        "restrictions": transformed_data.restrictions,
        "remarks": transformed_data.remarks,
        "last_sync_moveon": timezone.now(),
    }

    agreement, created = Agreement.objects.update_or_create(
        moveon_relation_id=transformed_data.moveon_relation_id,
        defaults=defaults,
    )
    agreement.full_clean()
    agreement.save()
    sync_agreement_constraints(agreement, transformed_data)
    return created


@transaction.atomic
def upsert_agreement_quota(
    transformed_data: TransformedAgreementQuota | dict[str, Any],
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_agreement_quota(transformed_data)
        validate_agreement_quota(transformed_data)

    agreement = resolve_agreement(transformed_data)
    academic_year = resolve_academic_year(transformed_data.academic_year_label)
    total_places, estimation_basis = estimate_n7_places_from_inp_quota(
        agreement,
        academic_year,
        transformed_data.total_places,
    )
    remaining_places = total_places

    quota, created = AgreementQuota.objects.update_or_create(
        agreement=agreement,
        academic_year_label=transformed_data.academic_year_label,
        period=transformed_data.period,
        defaults={
            "academic_year": academic_year,
            "places_id": transformed_data.places_id,
            "source_total_places": transformed_data.total_places,
            "source_remaining_places": transformed_data.remaining_places,
            "source_scope": "moveon_inp",
            "total_places": total_places,
            "remaining_places": remaining_places,
            "total_duration": transformed_data.total_duration,
            "duration_unit": transformed_data.duration_unit,
            "is_effective": transformed_data.is_effective,
            "is_estimated": True,
            "estimation_basis": estimation_basis,
            "remarks": transformed_data.remarks,
        },
    )
    quota.full_clean()
    quota.save()

    if not DepartmentQuota.objects.filter(agreement_quota=quota).exists():
        create_estimated_department_quotas(agreement, quota, academic_year)

    return created


@transaction.atomic
def upsert_mobility_category(
    transformed_data: TransformedMobilityCategory | dict[str, Any],
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_mobility_category(transformed_data)
        validate_mobility_category(transformed_data)

    framework, created = MobilityCategory.objects.update_or_create(
        moveon_framework_id=transformed_data.moveon_framework_id,
        defaults={
            "external_id": transformed_data.external_id,
            "name": transformed_data.name,
            "relation_types": transformed_data.relation_types,
            "is_active": transformed_data.is_active,
            "last_sync_moveon": timezone.now(),
        },
    )
    framework.full_clean()
    framework.save()
    return created


def resolve_partner_university(
    transformed_data: TransformedAgreement,
) -> PartnerUniversity:
    if transformed_data.partner_university_id:
        try:
            return PartnerUniversity.objects.get(
                pk=transformed_data.partner_university_id
            )
        except PartnerUniversity.DoesNotExist:
            pass

    if transformed_data.partner_university_moveon_id:
        try:
            return PartnerUniversity.objects.get(
                moveon_id=transformed_data.partner_university_moveon_id,
            )
        except PartnerUniversity.DoesNotExist:
            pass

    if transformed_data.partner_university_erasmus_code:
        erasmus_code = normalize_match_text(
            transformed_data.partner_university_erasmus_code
        )
        for university in PartnerUniversity.objects.exclude(erasmus_code=""):
            if normalize_match_text(university.erasmus_code) == erasmus_code:
                return university

    if transformed_data.partner_university_name:
        partner_name = normalize_match_text(transformed_data.partner_university_name)
        for university in PartnerUniversity.objects.all():
            candidate_names = [
                university.name,
                university.short_name,
                university.translated_name,
            ]
            if any(
                normalize_match_text(name) == partner_name for name in candidate_names
            ):
                return university

    raise ValueError("Missing partner university reference")


def resolve_mobility_category(framework_name: str) -> MobilityCategory | None:
    if not framework_name:
        return None

    normalized_name = normalize_match_text(framework_name)
    for category in MobilityCategory.objects.all():
        if normalize_match_text(category.name) == normalized_name:
            return category

    return None


def resolve_agreement(transformed_data: TransformedAgreementQuota) -> Agreement:
    if transformed_data.agreement_id:
        return Agreement.objects.get(pk=transformed_data.agreement_id)

    return Agreement.objects.get(moveon_relation_id=transformed_data.moveon_relation_id)


def resolve_academic_year(label: str) -> AcademicYear | None:
    return AcademicYear.objects.filter(label=label).first()


def sync_agreement_constraints(
    agreement: Agreement,
    transformed_data: TransformedAgreement,
) -> None:
    sync_agreement_department_constraints(agreement, transformed_data.department_tokens)
    sync_agreement_level_constraints(agreement, transformed_data.level_tokens)
    sync_agreement_year_availabilities(agreement, transformed_data.availabilities)


def sync_agreement_department_constraints(
    agreement: Agreement,
    department_tokens: tuple[str, ...],
) -> None:
    if not department_tokens:
        return

    departments = resolve_departments(department_tokens)
    active_ids = {department.id for department in departments}

    for department in departments:
        AgreementDepartmentConstraint.objects.update_or_create(
            agreement=agreement,
            department=department,
            defaults={
                "is_active": True,
                "source": "moveon",
                "remarks": "Departement concerne importe depuis MoveON.",
            },
        )

    AgreementDepartmentConstraint.objects.filter(
        agreement=agreement,
        source="moveon",
    ).exclude(department_id__in=active_ids).update(is_active=False)

    missing_tokens = [
        token
        for token in department_tokens
        if token not in {department.code for department in departments}
    ]
    for token in missing_tokens:
        if resolve_department(token) is None:
            create_constraint_failure_raw_import(
                RawImportEntity.AGREEMENT_DEPARTMENT,
                agreement,
                token,
                "Departement MoveON introuvable dans le referentiel.",
            )


def sync_agreement_level_constraints(
    agreement: Agreement,
    level_tokens: tuple[str, ...],
) -> None:
    if not level_tokens:
        return

    levels = [get_or_create_level(token) for token in level_tokens]
    active_ids = {level.id for level in levels}

    for level in levels:
        AgreementLevelConstraint.objects.update_or_create(
            agreement=agreement,
            level=level,
            defaults={
                "is_active": True,
                "source": "moveon",
                "remarks": "Niveau concerne importe depuis MoveON.",
            },
        )

    AgreementLevelConstraint.objects.filter(
        agreement=agreement,
        source="moveon",
    ).exclude(level_id__in=active_ids).update(is_active=False)


def sync_agreement_year_availabilities(
    agreement: Agreement,
    availabilities: tuple[TransformedAgreementAvailability, ...],
) -> None:
    for availability in availabilities:
        academic_year = resolve_academic_year(availability.academic_year_label)
        AgreementYearAvailability.objects.update_or_create(
            agreement=agreement,
            academic_year_label=availability.academic_year_label,
            defaults={
                "academic_year": academic_year,
                "is_available": availability.is_available,
                "source": "moveon",
                "remarks": availability.remarks,
            },
        )


def resolve_departments(department_tokens: tuple[str, ...]) -> list[Department]:
    departments: list[Department] = []
    seen_ids: set[int] = set()

    for token in department_tokens:
        department = resolve_department(token)
        if department and department.id not in seen_ids:
            departments.append(department)
            seen_ids.add(department.id)

    return departments


def resolve_department(token: str) -> Department | None:
    normalized_token = normalize_match_text(token)
    for department in Department.objects.all():
        if normalize_match_text(department.code) == normalized_token:
            return department
        if normalize_match_text(department.name) == normalized_token:
            return department
    return None


def get_or_create_level(token: str) -> Level:
    code = normalize_level_code(token)
    level, _ = Level.objects.update_or_create(
        code=code,
        defaults={
            "name": token.strip(),
            "is_active": True,
        },
    )
    return level


def normalize_level_code(token: str) -> str:
    return "-".join(token.strip().upper().split())[:50]


def create_constraint_failure_raw_import(
    entity: RawImportEntity,
    agreement: Agreement,
    token: str,
    error_message: str,
) -> None:
    RawImport.objects.create(
        source=f"moveon_fake_{entity.value}",
        source_file="",
        entity=entity,
        external_id=f"{agreement.moveon_relation_id or agreement.id}:{token}",
        payload={
            "agreement_id": agreement.id,
            "moveon_relation_id": agreement.moveon_relation_id,
            "value": token,
        },
        status=RawImportStatus.FAILED,
        error_message=error_message,
    )


def normalize_match_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())
