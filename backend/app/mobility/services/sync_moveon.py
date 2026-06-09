from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.institutions.models import PartnerUniversity
from app.integrations.moveon import MoveOnClient
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    MobilityCategory,
)
from app.reference.models import Department, Level

from .moveon_transformer import (
    TransformedAgreement,
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


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    total: int = 0


_N7_TOKENS = frozenset({"n7", "enseeiht", "inp toulouse n7", "inp n7"})


def _n7_is_present(inp_institutions: str) -> bool:
    normalized = inp_institutions.strip().casefold()
    return any(token in normalized for token in _N7_TOKENS)


@dataclass
class MobilitySyncResult:
    frameworks: SyncResult
    agreements: SyncResult
    quotas: SyncResult


def sync_moveon_mobility(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> MobilitySyncResult:
    """Sync complet : cadres + accords + quotas."""
    client = client or MoveOnClient()
    frameworks = sync_moveon_mobility_categories(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    agreements = sync_moveon_agreements(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    quotas = sync_moveon_agreement_inp_quotas(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    return MobilitySyncResult(
        frameworks=frameworks, agreements=agreements, quotas=quotas
    )


def sync_moveon_agreements_only(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> MobilitySyncResult:
    """Sync accords + quotas uniquement, sans toucher aux cadres."""
    client = client or MoveOnClient()
    dummy = SyncResult()
    agreements = sync_moveon_agreements(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    quotas = sync_moveon_agreement_inp_quotas(
        client, academic_year=academic_year, triggered_by=triggered_by
    )
    return MobilitySyncResult(frameworks=dummy, agreements=agreements, quotas=quotas)


def sync_moveon_mobility_categories(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_CATEGORIES,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    for category in client.fetch_agreement_frameworks():
        payload = category.payload
        external_id = _extract_external_id(payload, RawImportEntity.AGREEMENT_CATEGORY)

        if RawImport.objects.filter(
            external_id=external_id,
            entity=RawImportEntity.AGREEMENT_CATEGORY,
            status=RawImportStatus.IGNORED,
        ).exists():
            continue

        raw_import = _create_raw_import(
            payload,
            RawImportEntity.AGREEMENT_CATEGORY,
            import_report=report,
            academic_year=academic_year,
        )

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
            _mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1
        report.record_success()
        _mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    result.total = result.created + result.updated + result.failed
    report.finalize()
    return result


def sync_moveon_agreements(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_ACCORDS,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    for agreement in client.fetch_agreements():
        payload = agreement.payload
        external_id = _extract_external_id(payload, RawImportEntity.AGREEMENT)

        if RawImport.objects.filter(
            external_id=external_id,
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.IGNORED,
        ).exists():
            continue

        raw_import = _create_raw_import(
            payload,
            RawImportEntity.AGREEMENT,
            import_report=report,
            academic_year=academic_year,
        )

        try:
            transformed = transform_agreement(payload)
            validate_agreement(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            _mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if not _n7_is_present(transformed.inp_institutions):
            result.ignored += 1
            _mark_raw_import(
                raw_import,
                RawImportStatus.IGNORED,
                "N7/ENSEEIHT absent des établissements INP de cet accord",
            )
            continue

        try:
            created = upsert_agreement(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            _mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1
        report.record_success()
        _mark_raw_import(raw_import, RawImportStatus.IMPORTED)

    result.total = result.created + result.updated + result.failed + result.ignored
    report.finalize()
    return result


def sync_moveon_agreement_inp_quotas(
    client: MoveOnClient | None = None,
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> SyncResult:
    """Syncs INP quotas from MoveOn and updates agreement.inp_total_places."""
    client = client or MoveOnClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.MOVEON_QUOTAS,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    for quota in client.fetch_agreement_quotas():
        payload = quota.payload
        external_id = str(
            payload.get("moveon_id") or payload.get("agreement_id") or "quota-unknown"
        )

        try:
            transformed = transform_agreement_quota(payload)
            validate_agreement_quota(transformed)
            _update_agreement_inp_quota(transformed)
        except (
            Agreement.DoesNotExist,
            IntegrityError,
            DjangoValidationError,
            MoveOnValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            report.record_error(external_id, str(exc))
            continue

        result.updated += 1
        report.record_success()

    result.total = result.updated + result.failed
    report.finalize()
    return result


@transaction.atomic
def upsert_agreement(transformed_data: TransformedAgreement | dict[str, Any]) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_agreement(transformed_data)
        validate_agreement(transformed_data)

    try:
        partner_university = _resolve_partner_university(transformed_data)
    except (PartnerUniversity.DoesNotExist, ValueError) as exc:
        raise ValueError(
            "Université partenaire introuvable dans le référentiel. "
            "Cliquez sur « Corriger » pour sélectionner l'université correspondante."
        ) from exc

    category = _resolve_mobility_category(transformed_data.category_name)

    defaults = {
        "name": transformed_data.name,
        "partner_university": partner_university,
        "category": category,
        "direction": transformed_data.direction,
        "valid_from": transformed_data.start_date,
        "valid_until": transformed_data.end_date,
        "inp_institutions": transformed_data.inp_institutions,
        "remarks": transformed_data.remarks,
        "last_sync_moveon": timezone.now(),
    }

    agreement, created = Agreement.objects.update_or_create(
        moveon_id=transformed_data.moveon_id,
        defaults=defaults,
    )
    agreement.full_clean()
    agreement.save()
    _sync_departments(agreement, transformed_data.department_tokens)
    _sync_levels(agreement, transformed_data.level_tokens)
    return created


def _update_agreement_inp_quota(transformed_data: TransformedAgreementQuota) -> None:
    if transformed_data.agreement_id:
        agreement = Agreement.objects.get(pk=transformed_data.agreement_id)
    elif transformed_data.moveon_id:
        agreement = Agreement.objects.get(moveon_id=transformed_data.moveon_id)
    else:
        return

    if transformed_data.total_places > 0:
        agreement.inp_total_places = transformed_data.total_places
        agreement.save(update_fields=["inp_total_places", "updated_at"])


@transaction.atomic
def upsert_mobility_category(
    transformed_data: TransformedMobilityCategory | dict[str, Any],
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_mobility_category(transformed_data)
        validate_mobility_category(transformed_data)

    category, created = MobilityCategory.objects.update_or_create(
        moveon_id=transformed_data.moveon_id,
        defaults={
            "name": transformed_data.name,
            "last_sync_moveon": timezone.now(),
        },
    )
    category.full_clean()
    category.save()
    return created


# ── private helpers ────────────────────────────────────────────────────────────


def _extract_external_id(payload: dict[str, Any], entity: RawImportEntity) -> str:
    return str(
        payload.get("moveon_id")
        or payload.get("relation_id")
        or payload.get("moveon_framework_id")
        or f"raw-{entity.value}"
    )


def _create_raw_import(
    payload: dict[str, Any],
    entity: RawImportEntity,
    import_report: ImportReport | None = None,
    academic_year: AcademicYear | None = None,
) -> RawImport:
    external_id = _extract_external_id(payload, entity)
    return RawImport.objects.create(
        source=f"moveon_{entity.value}",
        source_file="",
        entity=entity,
        external_id=external_id,
        payload=payload,
        import_report=import_report,
        academic_year=academic_year,
    )


def _mark_raw_import(
    raw_import: RawImport, status: RawImportStatus, error_message: str = ""
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == RawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )


def _resolve_partner_university(
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
                moveon_id=transformed_data.partner_university_moveon_id
            )
        except PartnerUniversity.DoesNotExist:
            pass

    if transformed_data.partner_university_erasmus_code:
        code = _normalize(transformed_data.partner_university_erasmus_code)
        for u in PartnerUniversity.objects.exclude(erasmus_code=""):
            if _normalize(u.erasmus_code) == code:
                return u

    if transformed_data.partner_university_name:
        name = _normalize(transformed_data.partner_university_name)
        for u in PartnerUniversity.objects.all():
            if any(
                _normalize(n) == name for n in [u.name, u.short_name, u.translated_name]
            ):
                return u

    # Fallback: if this agreement was already corrected and saved, reuse its university
    if transformed_data.moveon_id:
        try:
            return Agreement.objects.get(
                moveon_id=transformed_data.moveon_id
            ).partner_university
        except Agreement.DoesNotExist:
            pass

    raise ValueError(
        "Université partenaire introuvable dans le référentiel. "
        "Cliquez sur « Corriger » pour sélectionner l'université correspondante."
    )


def _resolve_mobility_category(category_name: str) -> MobilityCategory | None:
    if not category_name:
        return None
    normalized = _normalize(category_name)
    for c in MobilityCategory.objects.all():
        if _normalize(c.name) == normalized:
            return c
    return None


def _sync_departments(agreement: Agreement, tokens: tuple[str, ...]) -> None:
    if not tokens:
        return
    departments: list[Department] = []
    seen: set[int] = set()
    for token in tokens:
        dept = _resolve_department(token)
        if dept and dept.id not in seen:
            departments.append(dept)
            seen.add(dept.id)
            continue
        if dept is None:
            RawImport.objects.create(
                source="moveon_agreement",
                source_file="",
                entity=RawImportEntity.AGREEMENT,
                external_id=f"{agreement.moveon_id or agreement.id}:{token}",
                payload={"agreement_id": agreement.id, "value": token},
                status=RawImportStatus.FAILED,
                error_message=(
                    f"Département « {token} » introuvable dans le référentiel. "
                    "Ajoutez ce code département dans Référentiels > Départements, "
                    "puis relancez la synchronisation."
                ),
            )
    for dept in departments:
        AgreementDepartment.objects.get_or_create(agreement=agreement, department=dept)


def _sync_levels(agreement: Agreement, tokens: tuple[str, ...]) -> None:
    if not tokens:
        return
    levels = [_get_or_create_level(t) for t in tokens]
    agreement.levels.set(levels)


def _resolve_department(token: str) -> Department | None:
    norm = _normalize(token)
    for d in Department.objects.all():
        if _normalize(d.code) == norm or _normalize(d.name) == norm:
            return d
    return None


def _get_or_create_level(token: str) -> Level:
    code = "-".join(token.strip().upper().split())[:50]
    level, _ = Level.objects.update_or_create(
        code=code, defaults={"name": token.strip()}
    )
    return level


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())
