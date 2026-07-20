from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Max, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.utils import timezone
from ninja import File, Query, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from app.academic.models import AcademicYear
from app.audit.logger import log_action
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.institutions.models import PartnerUniversity
from app.reference.models import Level
from app.shared.api_helpers import (
    PagedResponse,
    PaginationQuery,
    SelectOption,
    get_or_404,
    paginate,
    save_validated,
)
from app.shared.excel_utils import (
    build_filename,
    format_university_label,
    workbook_response,
    write_header_row,
)

from .models import (
    Agreement,
    AgreementDepartment,
    AgreementYear,
    AgreementYearDepartment,
    MobilityCategory,
)
from .schemas import (
    AGREEMENT_READONLY_FIELDS,
    AgreementDepartmentIn,
    AgreementDepartmentOut,
    AgreementIn,
    AgreementOut,
    AgreementYearAdjustInpIn,
    AgreementYearDepartmentIn,
    AgreementYearDepartmentOut,
    AgreementYearIn,
    AgreementYearOut,
    AgreementYearValidateIn,
    MobilityCategoryIn,
    MobilityCategoryOut,
    RawImportOut,
    RawImportRetryIn,
)
from .services.moveon_transformer import transform_agreement
from .services.moveon_validator import ValidationError as MoveOnValidationError
from .services.moveon_validator import validate_agreement
from .services.quota_estimator import (
    ensure_dept_quotas_on_activation,
    estimate_n7_from_inp,
    initialize_new_year_mobility,
    redistribute_department_quotas,
)
from .services.sync_moveon import upsert_agreement
from .tasks import (
    enqueue_sync_excel_agreements,
    enqueue_sync_moveon_agreements_only,
    enqueue_sync_moveon_mobility_categories,
)

router = Router()

PROTECTED_DELETE_MSG = (
    "Impossible de supprimer cet element : des donnees y sont rattachees. "
    "Supprimez d'abord les elements dependants."
)


def safe_delete(instance) -> None:
    try:
        instance.delete()
    except ProtectedError as exc:
        raise HttpError(409, PROTECTED_DELETE_MSG) from exc


def validate_year_consistency(agreement_year: AgreementYear) -> None:
    if agreement_year.n7_places > agreement_year.agreement.inp_total_places:
        raise HttpError(
            400, "Le quota N7 ne peut pas être supérieur au quota INP de l'accord."
        )

    dept_quotas = [
        dq.get_effective_quota() for dq in agreement_year.department_quotas.all()
    ]
    if not dept_quotas:
        return

    dept_total = sum(dept_quotas)
    if dept_total != agreement_year.n7_places:
        raise HttpError(
            400,
            f"La somme des quotas départements ({dept_total}) doit être égale au quota N7 ({agreement_year.n7_places}).",
        )


# ──────────────────────────────────────────────
# Accords
# ──────────────────────────────────────────────


@router.get("/agreements/export-excel/", summary="Exporter les accords en Excel")
def export_agreements_excel(
    request,
    year_label: str | None = None,
    country: str | None = None,
    category: str | None = None,
    activity: str | None = None,
):
    import openpyxl

    qs = (
        Agreement.objects.select_related(
            "partner_university",
            "partner_university__country",
            "category",
        )
        .prefetch_related("levels", "year_instances", "year_instances__academic_year")
        .order_by("partner_university__name", "name")
    )
    if country and country != "all":
        qs = qs.filter(partner_university__country__name_fr=country)
    if category and category != "all":
        qs = qs.filter(category__name=category)

    year_map: dict[int, AgreementYear] = {}
    if year_label:
        for ay in AgreementYear.objects.filter(
            academic_year__label=year_label
        ).select_related("academic_year"):
            year_map[ay.agreement_id] = ay
        if activity == "active":
            qs = qs.filter(
                year_instances__academic_year__label=year_label,
                year_instances__is_active=True,
            )
        elif activity == "inactive":
            qs = qs.filter(
                year_instances__academic_year__label=year_label,
                year_instances__is_active=False,
            )

    year_slug = year_label.replace("/", "-") if year_label else ""
    filename = build_filename("accords", year_slug)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Accords"

    headers = [
        "Accord",
        "Université",
        "Pays",
        "Cadre",
        "Direction",
        "Places INP",
        "Places N7",
        "Niveaux",
        "Valide de",
        "Valide jusqu'à",
    ]
    widths = [45, 40, 20, 22, 12, 12, 10, 22, 14, 14]
    if year_label:
        headers += ["Actif", "Validé"]
        widths += [8, 8]
    write_header_row(ws, headers, widths)

    for agr in qs.distinct():
        ay = year_map.get(agr.pk)
        levels = ", ".join(lvl.code for lvl in agr.levels.all())
        row = [
            agr.name,
            agr.partner_university.name if agr.partner_university_id else "",
            agr.partner_university.country.name_fr
            if agr.partner_university_id and agr.partner_university.country_id
            else "",
            agr.category.name if agr.category_id else "",
            agr.direction,
            agr.inp_total_places,
            ay.n7_places if ay else "",
            levels,
            agr.valid_from.isoformat() if agr.valid_from else "",
            agr.valid_until.isoformat() if agr.valid_until else "",
        ]
        if year_label:
            row += [
                "Oui" if (ay and ay.is_active) else "Non",
                "Oui" if (ay and ay.is_validated) else "Non",
            ]
        ws.append(row)

    return workbook_response(wb, filename)


@router.get(
    "/agreements/", response=PagedResponse[AgreementOut], summary="Liste des accords"
)
def list_agreements(
    request,
    search: str | None = None,
    country_id: int | None = None,
    is_active: bool | None = None,
    valid_only: bool = False,
    pagination: PaginationQuery = Query(),
):
    qs = (
        Agreement.objects.select_related(
            "partner_university", "category", "partner_university__country"
        )
        .prefetch_related("levels", "agreement_departments")
        .all()
    )
    if search:
        qs = qs.filter(
            Q(name__icontains=search) | Q(partner_university__name__icontains=search)
        )
    if country_id:
        qs = qs.filter(partner_university__country_id=country_id)
    if is_active is not None:
        qs = qs.filter(year_instances__is_active=is_active).distinct()
    if valid_only:
        today = date.today()
        qs = qs.filter(
            Q(valid_from__isnull=True) | Q(valid_from__lte=today),
            Q(valid_until__isnull=True) | Q(valid_until__gte=today),
        )
    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.get(
    "/agreements/expiring-soon/",
    response=list[AgreementOut],
    summary="Accords expirant dans les prochains mois",
)
def list_expiring_agreements(request, months: int = 4):
    today = date.today()
    cutoff = today + timedelta(days=30 * months)
    qs = (
        Agreement.objects.select_related(
            "partner_university", "category", "partner_university__country"
        )
        .prefetch_related("levels", "agreement_departments")
        .filter(valid_until__gte=today, valid_until__lte=cutoff)
        .order_by("valid_until")
    )
    return qs


@router.get(
    "/agreements/select-options/",
    response=list[SelectOption],
    summary="Options accords pour dropdown",
)
def list_agreements_select(request):
    qs = Agreement.objects.select_related(
        "partner_university", "partner_university__country"
    ).order_by("name")
    options = []
    for a in qs:
        univ = a.partner_university.name if a.partner_university_id else ""
        country = (
            f" – {a.partner_university.country.name_fr}"
            if a.partner_university_id and a.partner_university.country_id
            else ""
        )
        options.append(SelectOption(id=a.id, label=f"{a.name} – {univ}{country}"))
    return options


@router.post("/agreements/", response={201: AgreementOut}, summary="Créer un accord")
def create_agreement(request, payload: AgreementIn):
    data = {
        k: v
        for k, v in payload.model_dump().items()
        if k not in AGREEMENT_READONLY_FIELDS and k not in ("level_ids",)
    }
    agreement = Agreement(**data)
    save_validated(agreement)
    agreement.levels.set(payload.level_ids)
    return 201, Agreement.objects.prefetch_related(
        "levels", "agreement_departments"
    ).get(pk=agreement.pk)


@router.put(
    "/agreements/{agreement_id}/", response=AgreementOut, summary="Modifier un accord"
)
def update_agreement(request, agreement_id: int, payload: AgreementIn):
    agreement = get_or_404(Agreement, agreement_id, "Accord introuvable.")
    if agreement.year_instances.filter(is_validated=True).exists():
        raise HttpError(
            400,
            "Cet accord ne peut plus être modifié : une ou plusieurs années ont été validées. "
            "Modifiez uniquement les quotas de l'année en cours.",
        )
    for field, value in payload.model_dump().items():
        if field not in AGREEMENT_READONLY_FIELDS and field not in ("level_ids",):
            setattr(agreement, field, value)
    save_validated(agreement)
    agreement.levels.set(payload.level_ids)
    return Agreement.objects.prefetch_related("levels", "agreement_departments").get(
        pk=agreement.pk
    )


@router.delete(
    "/agreements/{agreement_id}/", response={204: None}, summary="Supprimer un accord"
)
def delete_agreement(request, agreement_id: int):
    agreement = get_or_404(Agreement, agreement_id, "Accord introuvable.")
    safe_delete(agreement)
    return 204, None


# ──────────────────────────────────────────────
# Départements d'accord (AgreementDepartment)
# ──────────────────────────────────────────────


@router.get(
    "/agreement-departments/",
    response=list[AgreementDepartmentOut],
    summary="Liste des départements d'un accord",
)
def list_agreement_departments(request):
    agreement_id = request.GET.get("agreement_id")
    qs = AgreementDepartment.objects.select_related("agreement", "department").all()
    if agreement_id:
        qs = qs.filter(agreement_id=agreement_id)
    return qs


@router.post(
    "/agreement-departments/",
    response={201: AgreementDepartmentOut},
    summary="Ajouter un département à un accord",
)
def create_agreement_department(request, payload: AgreementDepartmentIn):
    dept = AgreementDepartment(**payload.model_dump())
    return 201, save_validated(dept)


@router.put(
    "/agreement-departments/{dept_id}/",
    response=AgreementDepartmentOut,
    summary="Modifier un département d'accord",
)
def update_agreement_department(request, dept_id: int, payload: AgreementDepartmentIn):
    dept = get_or_404(AgreementDepartment, dept_id, "Département d'accord introuvable.")
    for field, value in payload.model_dump().items():
        if field not in ("id", "created_at", "updated_at"):
            setattr(dept, field, value)
    return save_validated(dept)


@router.delete(
    "/agreement-departments/{dept_id}/",
    response={204: None},
    summary="Retirer un département d'un accord",
)
def delete_agreement_department(request, dept_id: int):
    dept = get_or_404(AgreementDepartment, dept_id, "Département d'accord introuvable.")
    safe_delete(dept)
    return 204, None


# ──────────────────────────────────────────────
# Instances annuelles (AgreementYear)
# ──────────────────────────────────────────────


@router.get(
    "/agreement-years/",
    response=PagedResponse[AgreementYearOut],
    summary="Liste des instances annuelles",
)
def list_agreement_years(
    request,
    academic_year: str | None = None,
    agreement_id: int | None = None,
    pagination: PaginationQuery = Query(),
):
    qs = AgreementYear.objects.select_related("agreement", "academic_year").all()

    if academic_year:
        qs = qs.filter(academic_year__label=academic_year)
    if agreement_id:
        qs = qs.filter(agreement_id=agreement_id)

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.post(
    "/agreement-years/",
    response={201: AgreementYearOut},
    summary="Créer une instance annuelle",
)
def create_agreement_year(request, payload: AgreementYearIn):
    instance = AgreementYear(**payload.model_dump())
    saved = save_validated(instance)
    if saved.is_active:
        ensure_dept_quotas_on_activation(saved)
    return 201, saved


@router.put(
    "/agreement-years/{year_id}/",
    response=AgreementYearOut,
    summary="Modifier une instance annuelle (quotas, activation)",
)
def update_agreement_year(request, year_id: int, payload: AgreementYearIn):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    if instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    old_n7 = instance.n7_places
    for field, value in payload.model_dump().items():
        if field not in (
            "id",
            "created_at",
            "updated_at",
            "is_validated",
            "validated_by",
            "validated_at",
        ):
            setattr(instance, field, value)
    saved = save_validated(instance)
    if saved.is_active:
        if saved.n7_places != old_n7:
            # N7 a changé : redistribuer les quotas dept en conservant les proportions
            redistribute_department_quotas(saved)
        else:
            ensure_dept_quotas_on_activation(saved)
    return saved


@router.post(
    "/agreement-years/{year_id}/adjust-inp/",
    response=AgreementYearOut,
    summary="Modifier les places INP et recalculer le quota N7 + départements (Hamilton)",
)
def adjust_inp_places(request, year_id: int, payload: AgreementYearAdjustInpIn):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    if instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    if payload.inp_total_places < 0:
        raise HttpError(400, "inp_total_places ne peut pas être négatif.")
    instance.inp_total_places = payload.inp_total_places
    new_n7 = estimate_n7_from_inp(
        instance.agreement,
        inp_places=payload.inp_total_places,
        current_year=instance.academic_year,
    )
    instance.n7_places = new_n7
    instance.save(update_fields=["inp_total_places", "n7_places", "updated_at"])
    redistribute_department_quotas(instance)
    return instance


@router.post(
    "/agreement-years/{year_id}/toggle-active/",
    response=AgreementYearOut,
    summary="Activer / désactiver manuellement une instance annuelle",
)
def toggle_agreement_year_active(request, year_id: int):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    if instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    instance.is_active = not instance.is_active
    instance.save(update_fields=["is_active", "updated_at"])
    if instance.is_active:
        ensure_dept_quotas_on_activation(instance)
    return instance


@router.post(
    "/agreement-years/{year_id}/validate/",
    response=AgreementYearOut,
    summary="Valider une instance annuelle (verrouille les quotas)",
)
def validate_agreement_year(request, year_id: int, payload: AgreementYearValidateIn):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    validate_year_consistency(instance)
    instance.is_validated = True
    instance.validated_by = payload.validated_by
    instance.validated_at = timezone.now()
    instance.save(
        update_fields=["is_validated", "validated_by", "validated_at", "updated_at"]
    )
    return instance


@router.post(
    "/agreement-years/{year_id}/redistribute/",
    response=list[AgreementYearDepartmentOut],
    summary="Redistribuer les quotas par département via la méthode Hamilton (proportionnel à l'historique)",
)
def redistribute_year_departments(request, year_id: int):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    if instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être redistribuée.")
    redistribute_department_quotas(instance)
    return AgreementYearDepartment.objects.filter(agreement_year=instance)


@router.delete(
    "/agreement-years/{year_id}/",
    response={204: None},
    summary="Supprimer une instance annuelle",
)
def delete_agreement_year(request, year_id: int):
    instance = get_or_404(AgreementYear, year_id, "Instance annuelle introuvable.")
    if instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut pas être supprimée.")
    safe_delete(instance)
    return 204, None


# ──────────────────────────────────────────────
# Quotas par département (AgreementYearDepartment)
# ──────────────────────────────────────────────


@router.get(
    "/agreement-year-departments/",
    response=PagedResponse[AgreementYearDepartmentOut],
    summary="Liste des quotas par département",
)
def list_agreement_year_departments(
    request,
    academic_year: str | None = None,
    agreement_year_id: int | None = None,
    pagination: PaginationQuery = Query(),
):
    qs = AgreementYearDepartment.objects.select_related(
        "agreement_year__academic_year", "agreement_department__department"
    ).all()

    if academic_year:
        qs = qs.filter(agreement_year__academic_year__label=academic_year)
    if agreement_year_id:
        qs = qs.filter(agreement_year_id=agreement_year_id)

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.post(
    "/agreement-year-departments/",
    response={201: AgreementYearDepartmentOut},
    summary="Créer un quota département",
)
def create_agreement_year_department(request, payload: AgreementYearDepartmentIn):
    year_instance = get_or_404(
        AgreementYear, payload.agreement_year_id, "Instance annuelle introuvable."
    )
    if year_instance.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    try:
        agreement_dept = AgreementDepartment.objects.get(
            agreement=year_instance.agreement,
            department_id=payload.department_id,
        )
    except AgreementDepartment.DoesNotExist as exc:
        raise HttpError(
            400, f"Département {payload.department_id} non associé à cet accord."
        ) from exc
    dept = AgreementYearDepartment(
        agreement_year=year_instance,
        agreement_department=agreement_dept,
        estimated_places=payload.estimated_places,
    )
    return 201, save_validated(dept)


@router.put(
    "/agreement-year-departments/{dept_id}/",
    response=AgreementYearDepartmentOut,
    summary="Modifier un quota département",
)
def update_agreement_year_department(
    request, dept_id: int, payload: AgreementYearDepartmentIn
):
    dept = get_or_404(
        AgreementYearDepartment, dept_id, "Quota département introuvable."
    )
    if dept.agreement_year.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    dept.estimated_places = payload.estimated_places
    return save_validated(dept)


@router.delete(
    "/agreement-year-departments/{dept_id}/",
    response={204: None},
    summary="Supprimer un quota département",
)
def delete_agreement_year_department(request, dept_id: int):
    dept = get_or_404(
        AgreementYearDepartment, dept_id, "Quota département introuvable."
    )
    if dept.agreement_year.is_validated:
        raise HttpError(400, "Une instance validée ne peut plus être modifiée.")
    safe_delete(dept)
    return 204, None


# ──────────────────────────────────────────────
# Catégories de mobilité
# ──────────────────────────────────────────────


@router.get("/agreement-categories/", response=list[MobilityCategoryOut])
def list_agreement_categories(request):
    return MobilityCategory.objects.all()


@router.post("/agreement-categories/", response={201: MobilityCategoryOut})
def create_agreement_category(request, payload: MobilityCategoryIn):
    category = MobilityCategory(**payload.model_dump())
    return 201, save_validated(category)


# Route littérale définie AVANT /{category_id}/ pour éviter le conflit de routing
@router.post("/agreement-categories/sync/", response=dict)
def sync_agreement_categories_from_moveon(request):
    task_id = enqueue_sync_moveon_mobility_categories()
    log_action(
        request, action="sync_moveon_categories", detail=f"Tâche {task_id} lancée"
    )
    return {"task_id": task_id, "message": "Synchronisation des cadres lancée."}


@router.put("/agreement-categories/{category_id}/", response=MobilityCategoryOut)
def update_agreement_category(request, category_id: int, payload: MobilityCategoryIn):
    category = get_or_404(MobilityCategory, category_id, "Catégorie introuvable.")
    for field, value in payload.model_dump().items():
        setattr(category, field, value)
    return save_validated(category)


@router.delete("/agreement-categories/{category_id}/", response={204: None})
def delete_agreement_category(request, category_id: int):
    category = get_or_404(MobilityCategory, category_id, "Catégorie introuvable.")
    safe_delete(category)
    return 204, None


# ──────────────────────────────────────────────
# Estimation & initialisation
# ──────────────────────────────────────────────


@router.post(
    "/initialize-year/",
    response={200: dict},
    summary="Initialiser les instances annuelles pour une année académique",
)
def initialize_year(request):
    current_year = AcademicYear.get_current()
    if current_year is None:
        raise HttpError(400, "Aucune année académique courante trouvée.")
    result = initialize_new_year_mobility(current_year)
    return {
        "eligible_agreements": result.agreements_processed,
        "year_instances_created": result.year_instances_created,
        "department_quotas_created": result.department_quotas_created,
        "skipped_existing": result.skipped_existing,
    }


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────


@router.get("/dashboard/", response=dict)
def mobility_dashboard(request):
    current_year = AcademicYear.get_current()
    if current_year is None:
        return {
            "current_year": None,
            "active_agreements": 0,
            "total_n7_places": 0,
            "validated_count": 0,
            "pending_validation": 0,
        }

    year_instances = AgreementYear.objects.filter(academic_year=current_year)
    active = year_instances.filter(is_active=True)

    return {
        "current_year": {"id": current_year.id, "label": current_year.label},
        "active_agreements": active.count(),
        "total_n7_places": active.aggregate(total=Sum("n7_places"))["total"] or 0,
        "validated_count": active.filter(is_validated=True).count(),
        "pending_validation": active.filter(is_validated=False).count(),
    }


# ──────────────────────────────────────────────
# Sync MoveON
# ──────────────────────────────────────────────


@router.post("/sync-moveon/", response={202: dict})
def sync_mobility_from_moveon(request):
    task_id = enqueue_sync_moveon_agreements_only()
    log_action(
        request, action="sync_moveon_agreements", detail=f"Tâche {task_id} lancée"
    )
    return 202, {"task_id": task_id, "message": "Synchronisation des accords lancée."}


# ──────────────────────────────────────────────
# Raw imports / erreurs
# ──────────────────────────────────────────────


@router.get("/raw-imports/moveon-errors/", response=PagedResponse[RawImportOut])
def list_moveon_import_errors(request, pagination: PaginationQuery = Query(...)):
    latest_ids = (
        RawImport.objects.filter(
            entity__in=[RawImportEntity.AGREEMENT, RawImportEntity.AGREEMENT_CATEGORY]
        )
        .values("entity", "external_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    qs = RawImport.objects.filter(
        id__in=latest_ids,
        status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
    ).order_by("-created_at")
    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.put("/raw-imports/{raw_import_id}/retry/", response=RawImportOut)
def retry_raw_import(request, raw_import_id: int, payload: RawImportRetryIn):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.FAILED,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import MoveON introuvable.") from exc

    corrected = dict(raw_import.payload)
    correction = payload.model_dump(exclude_none=True)
    if partner_university_id := correction.get("partner_university_id"):
        corrected["partner_university_id"] = partner_university_id
    for field in ("name", "reference"):
        if correction.get(field) is not None:
            corrected[field] = correction[field]

    try:
        transformed = transform_agreement(corrected)
        validate_agreement(transformed)
        upsert_agreement(transformed)
    except (
        IntegrityError,
        ValidationError,
        MoveOnValidationError,
        ValueError,
        KeyError,
        Agreement.DoesNotExist,
        PartnerUniversity.DoesNotExist,
    ) as exc:
        raw_import.payload = corrected
        raw_import.error_message = str(exc)
        raw_import.save(update_fields=["payload", "error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    raw_import.payload = corrected
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


@router.put("/raw-imports/{raw_import_id}/ignore/", response=RawImportOut)
def ignore_raw_import(request, raw_import_id: int):
    raw_import = get_or_404(RawImport, raw_import_id, "Import brut introuvable.")
    now = timezone.now()
    RawImport.objects.filter(
        source=raw_import.source,
        external_id=raw_import.external_id,
    ).exclude(status=RawImportStatus.IGNORED).update(
        status=RawImportStatus.IGNORED,
        error_message="Traité manuellement",
        updated_at=now,
    )
    raw_import.refresh_from_db()
    return raw_import


# ──────────────────────────────────────────────
# Import Excel
# ──────────────────────────────────────────────


@router.get("/excel-template/")
def download_excel_template(request):
    from app.institutions.models import PartnerUniversity as PartnerUniv
    from app.reference.models import Department as RefDepartment

    from .services.excel_importer import build_excel_template

    departments = list(
        RefDepartment.objects.values_list("code", flat=True).order_by("code")
    )
    universities = [
        format_university_label(
            u.name,
            u.short_name,
            u.country.name_fr if u.country_id else "",
        )
        for u in PartnerUniv.objects.select_related("country").order_by("name")
    ]
    categories = list(
        MobilityCategory.objects.values_list("name", flat=True).order_by("name")
    )
    levels = list(Level.objects.values_list("code", flat=True).order_by("code"))

    file_bytes = build_excel_template(
        departments=departments,
        universities=universities,
        frameworks=categories,
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


@router.post("/import-excel/", response={202: dict})
def import_agreements_from_excel(request, file: UploadedFile = File(...)):
    if not file.name.endswith((".xlsx", ".xls")):
        raise HttpError(400, "Seuls les fichiers .xlsx et .xls sont acceptés.")

    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HttpError(400, "Fichier trop volumineux (max 5 Mo).")

    task_id = enqueue_sync_excel_agreements(file_bytes, file.name or "upload.xlsx")
    log_action(
        request,
        action="import_excel_agreements",
        detail=f"Fichier {file.name} — Tâche {task_id} lancée",
    )
    return 202, {
        "task_id": task_id,
        "message": "Import Excel lancé en arrière-plan.",
    }
