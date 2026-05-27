from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils import timezone
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.reference.models import Level

from .models import (
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
from .schemas import (
    AGREEMENT_READONLY_FIELDS,
    AgreementDepartmentConstraintIn,
    AgreementDepartmentConstraintOut,
    AgreementLevelConstraintIn,
    AgreementLevelConstraintOut,
    AgreementQuotaIn,
    AgreementQuotaOut,
    AgreementQuotaValidateIn,
    AgreementSchema,
    AgreementYearAvailabilityIn,
    AgreementYearAvailabilityOut,
    DepartmentQuotaIn,
    DepartmentQuotaOut,
    DepartmentQuotaValidateIn,
    MobilityCategoryIn,
    MobilityCategoryOut,
    RawImportOut,
    RawImportRetryIn,
)
from .services.agreement_validity import is_agreement_valid_for_year
from .services.excel_importer import build_excel_template
from .services.moveon_transformer import transform_agreement
from .services.moveon_validator import (
    ValidationError as MoveOnValidationError,
)
from .services.moveon_validator import (
    validate_agreement,
)
from .services.quota_estimator import (
    create_estimated_department_quotas,
    estimate_current_year_missing_quotas,
)
from .services.sync_moveon import upsert_agreement
from .tasks import (
    enqueue_sync_excel_agreements,
    enqueue_sync_moveon_mobility,
    enqueue_sync_moveon_mobility_categories,
)

router = Router()


def save_validated(instance):
    try:
        instance.full_clean()
        instance.save()
    except (IntegrityError, ValidationError) as exc:
        raise HttpError(400, str(exc)) from exc

    return instance


def validate_quota_consistency(quota: AgreementQuota) -> None:
    if (
        quota.source_total_places is not None
        and quota.total_places > quota.source_total_places
    ):
        raise HttpError(400, "Le quota N7 ne peut pas etre superieur au quota INP.")

    department_total = sum(quota.department_quotas.values_list("places", flat=True))
    if department_total != quota.total_places:
        raise HttpError(
            400,
            "La somme des quotas departements doit etre egale au quota N7.",
        )


def get_or_404(model, pk: int, message: str):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist as exc:
        raise HttpError(404, message) from exc


@router.get("/agreements/", response=list[AgreementSchema], summary="Liste des accords")
def list_agreements(request):
    academic_year_label = request.GET.get("academic_year")
    partner_university_id = request.GET.get("partner_university_id")
    scope = request.GET.get("scope", "").strip().lower()

    queryset = Agreement.objects.select_related("partner_university").prefetch_related(
        "year_availabilities",
    )

    if partner_university_id:
        queryset = queryset.filter(partner_university_id=partner_university_id)

    if scope == "current":
        current_year = AcademicYear.get_current()
        if current_year is None:
            return []
        return [a for a in queryset if is_agreement_valid_for_year(a, current_year)]

    if academic_year_label:
        academic_year = AcademicYear.objects.filter(label=academic_year_label).first()
        if academic_year is None:
            return []
        return [a for a in queryset if is_agreement_valid_for_year(a, academic_year)]

    return queryset


@router.post("/agreements/", response={201: AgreementSchema}, summary="Creer un accord")
def create_agreement(request, payload: AgreementSchema):
    data = {
        k: v
        for k, v in payload.model_dump().items()
        if k not in AGREEMENT_READONLY_FIELDS
    }
    agreement = Agreement(**data)
    return 201, save_validated(agreement)


@router.put(
    "/agreements/{agreement_id}/",
    response=AgreementSchema,
    summary="Modifier un accord",
)
def update_agreement(request, agreement_id: int, payload: AgreementSchema):
    agreement = get_or_404(Agreement, agreement_id, "Accord introuvable.")

    for field, value in payload.model_dump().items():
        if field not in AGREEMENT_READONLY_FIELDS:
            setattr(agreement, field, value)

    return save_validated(agreement)


@router.delete(
    "/agreements/{agreement_id}/",
    response={204: None},
    summary="Supprimer un accord",
)
def delete_agreement(request, agreement_id: int):
    agreement = get_or_404(Agreement, agreement_id, "Accord introuvable.")
    agreement.delete()
    return 204, None


@router.get(
    "/agreement-frameworks/",
    response=list[MobilityCategoryOut],
    summary="Liste des cadres d'accords",
)
def list_agreement_frameworks(request):
    return MobilityCategory.objects.all()


@router.post(
    "/agreement-frameworks/",
    response={201: MobilityCategoryOut},
    summary="Creer un cadre d'accord",
)
def create_agreement_framework(request, payload: MobilityCategoryIn):
    import uuid

    framework = MobilityCategory(
        moveon_framework_id=f"manual-{uuid.uuid4().hex[:8]}",
        **payload.model_dump(),
    )
    return 201, save_validated(framework)


@router.put(
    "/agreement-frameworks/{framework_id}/",
    response=MobilityCategoryOut,
    summary="Modifier un cadre d'accord",
)
def update_agreement_framework(request, framework_id: int, payload: MobilityCategoryIn):
    framework = get_or_404(
        MobilityCategory, framework_id, "Cadre d'accord introuvable."
    )
    for field, value in payload.model_dump().items():
        setattr(framework, field, value)
    return save_validated(framework)


@router.delete(
    "/agreement-frameworks/{framework_id}/",
    response={204: None},
    summary="Supprimer un cadre d'accord",
)
def delete_agreement_framework(request, framework_id: int):
    framework = get_or_404(
        MobilityCategory, framework_id, "Cadre d'accord introuvable."
    )
    framework.delete()
    return 204, None


@router.post(
    "/agreement-frameworks/sync/",
    response=dict,
    summary="Synchroniser les cadres d'accords depuis MoveON",
)
def sync_agreement_frameworks_from_moveon(request):
    task_id = enqueue_sync_moveon_mobility_categories()
    return {
        "task_id": task_id,
        "message": "Synchronisation des cadres lancee.",
    }


@router.get(
    "/agreement-availabilities/",
    response=list[AgreementYearAvailabilityOut],
    summary="Liste des disponibilites annuelles d'accords",
)
def list_agreement_availabilities(request):
    academic_year_label = request.GET.get("academic_year")
    agreement_id = request.GET.get("agreement_id")
    queryset = AgreementYearAvailability.objects.select_related(
        "agreement",
        "academic_year",
    ).all()

    if agreement_id:
        queryset = queryset.filter(agreement_id=agreement_id)

    if academic_year_label:
        queryset = queryset.filter(academic_year_label=academic_year_label)

    return queryset


@router.post(
    "/agreement-availabilities/",
    response={201: AgreementYearAvailabilityOut},
    summary="Creer une disponibilite annuelle d'accord",
)
def create_agreement_availability(request, payload: AgreementYearAvailabilityIn):
    availability = AgreementYearAvailability(**payload.model_dump())
    return 201, save_validated(availability)


@router.put(
    "/agreement-availabilities/{availability_id}/",
    response=AgreementYearAvailabilityOut,
    summary="Modifier une disponibilite annuelle d'accord",
)
def update_agreement_availability(
    request,
    availability_id: int,
    payload: AgreementYearAvailabilityIn,
):
    availability = get_or_404(
        AgreementYearAvailability,
        availability_id,
        "Disponibilite annuelle introuvable.",
    )

    for field, value in payload.model_dump().items():
        setattr(availability, field, value)

    return save_validated(availability)


@router.delete(
    "/agreement-availabilities/{availability_id}/",
    response={204: None},
    summary="Supprimer une disponibilite annuelle d'accord",
)
def delete_agreement_availability(request, availability_id: int):
    availability = get_or_404(
        AgreementYearAvailability,
        availability_id,
        "Disponibilite annuelle introuvable.",
    )
    availability.delete()
    return 204, None


@router.get(
    "/agreement-departments/",
    response=list[AgreementDepartmentConstraintOut],
    summary="Liste des departements concernes par accord",
)
def list_agreement_departments(request):
    agreement_id = request.GET.get("agreement_id")
    department_id = request.GET.get("department_id")
    queryset = AgreementDepartmentConstraint.objects.select_related(
        "agreement",
        "department",
    ).all()

    if agreement_id:
        queryset = queryset.filter(agreement_id=agreement_id)

    if department_id:
        queryset = queryset.filter(department_id=department_id)

    return queryset


@router.post(
    "/agreement-departments/",
    response={201: AgreementDepartmentConstraintOut},
    summary="Ajouter un departement concerne a un accord",
)
def create_agreement_department(request, payload: AgreementDepartmentConstraintIn):
    constraint = AgreementDepartmentConstraint(**payload.model_dump())
    return 201, save_validated(constraint)


@router.put(
    "/agreement-departments/{constraint_id}/",
    response=AgreementDepartmentConstraintOut,
    summary="Modifier un departement concerne par accord",
)
def update_agreement_department(
    request,
    constraint_id: int,
    payload: AgreementDepartmentConstraintIn,
):
    constraint = get_or_404(
        AgreementDepartmentConstraint,
        constraint_id,
        "Contrainte departement introuvable.",
    )

    for field, value in payload.model_dump().items():
        setattr(constraint, field, value)

    return save_validated(constraint)


@router.delete(
    "/agreement-departments/{constraint_id}/",
    response={204: None},
    summary="Supprimer un departement concerne par accord",
)
def delete_agreement_department(request, constraint_id: int):
    constraint = get_or_404(
        AgreementDepartmentConstraint,
        constraint_id,
        "Contrainte departement introuvable.",
    )
    constraint.delete()
    return 204, None


@router.get(
    "/agreement-levels/",
    response=list[AgreementLevelConstraintOut],
    summary="Liste des niveaux concernes par accord",
)
def list_agreement_levels(request):
    agreement_id = request.GET.get("agreement_id")
    level_id = request.GET.get("level_id")
    queryset = AgreementLevelConstraint.objects.select_related(
        "agreement", "level"
    ).all()

    if agreement_id:
        queryset = queryset.filter(agreement_id=agreement_id)

    if level_id:
        queryset = queryset.filter(level_id=level_id)

    return queryset


@router.post(
    "/agreement-levels/",
    response={201: AgreementLevelConstraintOut},
    summary="Ajouter un niveau concerne a un accord",
)
def create_agreement_level(request, payload: AgreementLevelConstraintIn):
    constraint = AgreementLevelConstraint(**payload.model_dump())
    return 201, save_validated(constraint)


@router.put(
    "/agreement-levels/{constraint_id}/",
    response=AgreementLevelConstraintOut,
    summary="Modifier un niveau concerne par accord",
)
def update_agreement_level(
    request,
    constraint_id: int,
    payload: AgreementLevelConstraintIn,
):
    constraint = get_or_404(
        AgreementLevelConstraint,
        constraint_id,
        "Contrainte niveau introuvable.",
    )

    for field, value in payload.model_dump().items():
        setattr(constraint, field, value)

    return save_validated(constraint)


@router.delete(
    "/agreement-levels/{constraint_id}/",
    response={204: None},
    summary="Supprimer un niveau concerne par accord",
)
def delete_agreement_level(request, constraint_id: int):
    constraint = get_or_404(
        AgreementLevelConstraint,
        constraint_id,
        "Contrainte niveau introuvable.",
    )
    constraint.delete()
    return 204, None


@router.get(
    "/agreement-quotas/",
    response=list[AgreementQuotaOut],
    summary="Liste des quotas d'accords",
)
def list_agreement_quotas(request):
    academic_year_label = request.GET.get("academic_year")
    scope = request.GET.get("scope", "").strip().lower()

    queryset = AgreementQuota.objects.select_related("agreement", "academic_year").all()

    if scope == "current":
        current_year = AcademicYear.get_current()
        if current_year is None:
            return queryset.none()
        return queryset.filter(academic_year_label=current_year.label)

    if academic_year_label:
        return queryset.filter(academic_year_label=academic_year_label)

    return queryset


@router.post(
    "/agreement-quotas/",
    response={201: AgreementQuotaOut},
    summary="Creer un quota d'accord",
)
def create_agreement_quota(request, payload: AgreementQuotaIn):
    quota = AgreementQuota(**payload.model_dump())
    quota = save_validated(quota)
    year = AcademicYear.objects.filter(label=quota.academic_year_label).first()
    create_estimated_department_quotas(quota.agreement, quota, year)
    return 201, quota


@router.post(
    "/agreement-quotas/{quota_id}/validate/",
    response=AgreementQuotaOut,
    summary="Valider l'estimation d'un quota accord",
)
def validate_agreement_quota(
    request,
    quota_id: int,
    payload: AgreementQuotaValidateIn,
):
    quota = get_or_404(AgreementQuota, quota_id, "Quota d'accord introuvable.")
    validate_quota_consistency(quota)
    quota.is_validated = True
    quota.is_estimated = False
    quota.validated_by = payload.validated_by
    quota.validated_at = timezone.now()
    quota.save(
        update_fields=[
            "is_validated",
            "is_estimated",
            "validated_by",
            "validated_at",
            "updated_at",
        ]
    )
    return quota


@router.put(
    "/agreement-quotas/{quota_id}/",
    response=AgreementQuotaOut,
    summary="Modifier un quota d'accord",
)
def update_agreement_quota(request, quota_id: int, payload: AgreementQuotaIn):
    quota = get_or_404(AgreementQuota, quota_id, "Quota d'accord introuvable.")

    for field, value in payload.model_dump().items():
        setattr(quota, field, value)

    return save_validated(quota)


@router.post(
    "/agreement-quotas/{quota_id}/redistribute/",
    response=list[DepartmentQuotaOut],
    summary="Redistribuer egalitairement le quota par departement",
)
def redistribute_agreement_quota(request, quota_id: int):
    quota = get_or_404(AgreementQuota, quota_id, "Quota d'accord introuvable.")
    if quota.is_validated:
        raise HttpError(400, "Un quota valide ne peut pas etre redistribue.")
    DepartmentQuota.objects.filter(agreement_quota=quota).delete()
    year = quota.academic_year
    create_estimated_department_quotas(quota.agreement, quota, year)
    return DepartmentQuota.objects.filter(agreement_quota=quota)


@router.delete(
    "/agreement-quotas/{quota_id}/",
    response={204: None},
    summary="Supprimer un quota d'accord",
)
def delete_agreement_quota(request, quota_id: int):
    quota = get_or_404(AgreementQuota, quota_id, "Quota d'accord introuvable.")
    quota.delete()
    return 204, None


@router.get(
    "/department-quotas/",
    response=list[DepartmentQuotaOut],
    summary="Liste des quotas par departement",
)
def list_department_quotas(request):
    academic_year_label = request.GET.get("academic_year")
    scope = request.GET.get("scope", "").strip().lower()

    queryset = DepartmentQuota.objects.select_related(
        "agreement_quota",
        "agreement_quota__agreement",
        "department",
    ).all()

    if scope == "current":
        current_year = AcademicYear.get_current()
        if current_year is None:
            return queryset.none()
        return queryset.filter(agreement_quota__academic_year_label=current_year.label)

    if academic_year_label:
        return queryset.filter(agreement_quota__academic_year_label=academic_year_label)

    return queryset


@router.get(
    "/dashboard/",
    response=dict,
    summary="Indicateurs mobilite pour l'annee courante",
)
def mobility_dashboard(request):
    current_year = AcademicYear.get_current()
    if current_year is None:
        return {
            "current_year": None,
            "valid_agreements": 0,
            "current_year_quotas": 0,
            "estimated_quotas": 0,
            "missing_department_repartition": 0,
        }

    agreements = Agreement.objects.all()
    valid_agreements = [
        a for a in agreements if is_agreement_valid_for_year(a, current_year)
    ]
    quotas = AgreementQuota.objects.filter(academic_year_label=current_year.label)
    missing_department_repartition = quotas.filter(
        department_quotas__isnull=True
    ).count()

    return {
        "current_year": {"id": current_year.id, "label": current_year.label},
        "valid_agreements": len(valid_agreements),
        "current_year_quotas": quotas.count(),
        "estimated_quotas": quotas.filter(is_estimated=True).count(),
        "missing_department_repartition": missing_department_repartition,
    }


@router.post(
    "/department-quotas/",
    response={201: DepartmentQuotaOut},
    summary="Creer un quota par departement",
)
def create_department_quota(request, payload: DepartmentQuotaIn):
    quota = DepartmentQuota(**payload.model_dump())
    return 201, save_validated(quota)


@router.put(
    "/department-quotas/{department_quota_id}/",
    response=DepartmentQuotaOut,
    summary="Modifier un quota par departement",
)
def update_department_quota(
    request,
    department_quota_id: int,
    payload: DepartmentQuotaIn,
):
    quota = get_or_404(
        DepartmentQuota,
        department_quota_id,
        "Quota departement introuvable.",
    )

    for field, value in payload.model_dump().items():
        setattr(quota, field, value)

    return save_validated(quota)


@router.post(
    "/department-quotas/{department_quota_id}/validate/",
    response=DepartmentQuotaOut,
    summary="Valider l'estimation d'un quota departement",
)
def validate_department_quota(
    request,
    department_quota_id: int,
    payload: DepartmentQuotaValidateIn,
):
    quota = get_or_404(
        DepartmentQuota,
        department_quota_id,
        "Quota departement introuvable.",
    )
    validate_quota_consistency(quota.agreement_quota)
    quota.is_validated = True
    quota.is_estimated = False
    quota.validated_by = payload.validated_by
    quota.validated_at = timezone.now()
    quota.save(
        update_fields=[
            "is_validated",
            "is_estimated",
            "validated_by",
            "validated_at",
            "updated_at",
        ]
    )
    return quota


@router.delete(
    "/department-quotas/{department_quota_id}/",
    response={204: None},
    summary="Supprimer un quota par departement",
)
def delete_department_quota(request, department_quota_id: int):
    quota = get_or_404(
        DepartmentQuota,
        department_quota_id,
        "Quota departement introuvable.",
    )
    quota.delete()
    return 204, None


@router.get(
    "/raw-imports/", response=list[RawImportOut], summary="Liste des imports bruts"
)
def list_raw_imports(request):
    return RawImport.objects.all()


@router.get(
    "/raw-imports/moveon-errors/",
    response=list[RawImportOut],
    summary="Liste des erreurs d'import MoveON",
)
def list_moveon_import_errors(request):
    raw_imports = RawImport.objects.filter(
        entity__in=[
            RawImportEntity.AGREEMENT,
            RawImportEntity.AGREEMENT_DEPARTMENT,
            RawImportEntity.AGREEMENT_FRAMEWORK,
            RawImportEntity.AGREEMENT_LEVEL,
            RawImportEntity.AGREEMENT_QUOTA,
        ],
    ).order_by("-created_at")
    latest_by_entity_and_external_id = {}

    for raw_import in raw_imports:
        key = (
            raw_import.entity,
            raw_import.external_id or f"raw-{raw_import.id}",
        )
        if key not in latest_by_entity_and_external_id:
            latest_by_entity_and_external_id[key] = raw_import

    return [
        raw_import
        for raw_import in latest_by_entity_and_external_id.values()
        if raw_import.status == RawImportStatus.FAILED
    ]


@router.put(
    "/raw-imports/{raw_import_id}/retry/",
    response=RawImportOut,
    summary="Corriger et relancer un import MoveON d'accord",
)
def retry_raw_import(request, raw_import_id: int, payload: RawImportRetryIn):
    raw_import = get_failed_raw_import(raw_import_id)
    corrected_payload = apply_retry_correction(
        dict(raw_import.payload),
        raw_import.entity,
        payload,
    )

    try:
        if raw_import.entity == RawImportEntity.AGREEMENT:
            transformed = transform_agreement(corrected_payload)
            validate_agreement(transformed)
            upsert_agreement(transformed)
        else:
            raise HttpError(400, "Type d'import MoveON non relancable.")
    except (
        IntegrityError,
        ValidationError,
        MoveOnValidationError,
        ValueError,
        KeyError,
        Agreement.DoesNotExist,
        PartnerUniversity.DoesNotExist,
    ) as exc:
        raw_import.payload = corrected_payload
        raw_import.error_message = str(exc)
        raw_import.save(update_fields=["payload", "error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    raw_import.payload = corrected_payload
    raw_import.status = RawImportStatus.IMPORTED
    raw_import.error_message = ""
    raw_import.imported_at = timezone.now()
    raw_import.save(
        update_fields=[
            "payload",
            "status",
            "error_message",
            "imported_at",
            "updated_at",
        ]
    )
    return raw_import


def get_failed_raw_import(raw_import_id: int) -> RawImport:
    try:
        return RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.FAILED,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import MoveON introuvable.") from exc


def apply_retry_correction(
    corrected_payload: dict,
    entity: str,
    retry_payload: RawImportRetryIn,
) -> dict:
    correction = retry_payload.model_dump(exclude_none=True)

    if entity == RawImportEntity.AGREEMENT:
        if partner_university_id := correction.get("partner_university_id"):
            corrected_payload["partner_university_id"] = partner_university_id

    return corrected_payload


@router.put(
    "/raw-imports/{raw_import_id}/ignore/",
    response=RawImportOut,
    summary="Marquer une erreur d'import comme traitee manuellement",
)
def ignore_raw_import(request, raw_import_id: int):
    raw_import = get_or_404(RawImport, raw_import_id, "Import brut introuvable.")
    raw_import.status = RawImportStatus.IGNORED
    raw_import.error_message = (
        f"{raw_import.error_message}\nTraite manuellement par l'administrateur."
    ).strip()
    raw_import.save(update_fields=["status", "error_message", "updated_at"])
    return raw_import


@router.post(
    "/sync-moveon/",
    response={202: dict},
    summary="Demander la synchronisation des cadres et accords depuis MoveON",
)
def sync_mobility_from_moveon(request):
    task_id = enqueue_sync_moveon_mobility()
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation MoveON des cadres et accords demandee.",
    }


@router.post(
    "/estimate-current-year/",
    response={200: dict},
    summary="Estimer les quotas manquants pour l'annee courante",
)
def estimate_current_year_quotas(request):
    result = estimate_current_year_missing_quotas()
    return {
        "eligible_agreements": result.eligible_agreements,
        "quota_created": result.quota_created,
        "department_quota_created": result.department_quota_created,
        "skipped_existing_quota": result.skipped_existing_quota,
        "skipped_no_current_year": result.skipped_no_current_year,
    }


@router.get(
    "/excel-template/",
    summary="Telecharger le template Excel pour import d'accords",
)
def download_excel_template(request):
    from app.institutions.models import PartnerUniversity as PartnerUniv
    from app.reference.models import Department as RefDepartment

    departments = list(
        RefDepartment.objects.values_list("code", flat=True).order_by("code")
    )
    universities = list(
        PartnerUniv.objects.values_list("name", flat=True).order_by("name")
    )
    frameworks = sorted(
        set(Agreement.objects.exclude(framework="").values_list("framework", flat=True))
    )
    levels = list(
        Level.objects.filter(is_active=True)
        .values_list("code", flat=True)
        .order_by("code")
    )
    file_bytes = build_excel_template(
        departments=departments,
        universities=universities,
        frameworks=frameworks,
        levels=levels,
    )
    response = HttpResponse(
        file_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        'attachment; filename="template_accords_mobilite.xlsx"'
    )
    return response


@router.post(
    "/import-excel/",
    response={202: dict},
    summary="Importer des accords depuis un fichier Excel (traitement en arriere-plan)",
)
def import_agreements_from_excel(request, file: UploadedFile = File(...)):  # noqa: B008
    if not file.name.endswith((".xlsx", ".xls")):
        raise HttpError(400, "Seuls les fichiers .xlsx et .xls sont acceptes.")

    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HttpError(400, "Fichier trop volumineux (max 5 Mo).")

    task_id = enqueue_sync_excel_agreements(file_bytes, file.name or "upload.xlsx")
    return 202, {
        "task_id": task_id,
        "message": "Import Excel lance en arriere-plan. Consultez le journal des erreurs pour le resultat.",
    }
