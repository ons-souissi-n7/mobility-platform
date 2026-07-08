from __future__ import annotations

from django.db.models import Max, Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from ninja import File, Query, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from app.academic.models import AcademicYear
from app.audit.logger import log_action
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.shared.api_helpers import (
    PagedResponse,
    PaginationQuery,
    get_or_404,
    paginate,
    save_validated,
)

from .models import Internship
from .schemas import InternshipImportErrorOut, InternshipIn, InternshipOut
from .tasks import enqueue_import_excel_internships, enqueue_sync_eudonet_internships

router = Router()

PROTECTED_DELETE_MSG = (
    "Impossible de supprimer ce stage : des données y sont rattachées. "
    "Supprimez d'abord les éléments dépendants."
)


def _safe_delete(instance) -> None:
    try:
        instance.delete()
    except ProtectedError as exc:
        raise HttpError(409, PROTECTED_DELETE_MSG) from exc


# ──────────────────────────────────────────────
# Collection endpoints (defined before /{id}/ to avoid catch-all conflict)
# ──────────────────────────────────────────────


@router.get("/", response=PagedResponse[InternshipOut], summary="Liste des stages")
def list_internships(
    request,
    year_id: int | None = None,
    country_id: int | None = None,
    student_id: int | None = None,
    search: str | None = None,
    pagination: PaginationQuery = Query(),
):
    qs = Internship.objects.select_related(
        "student", "academic_year", "country"
    ).order_by("-start_date", "student__last_name")

    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    if country_id:
        qs = qs.filter(country_id=country_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    if search:
        qs = qs.filter(
            Q(student__last_name__icontains=search)
            | Q(student__first_name__icontains=search)
            | Q(company_name__icontains=search)
            | Q(student__ine__icontains=search)
        )

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        results=items,
    )


@router.post("/", response={201: InternshipOut}, summary="Créer un stage")
def create_internship(request, payload: InternshipIn):
    internship = Internship(**payload.model_dump())
    saved = save_validated(internship)
    return 201, Internship.objects.select_related(
        "student", "academic_year", "country"
    ).get(pk=saved.pk)


# ──────────────────────────────────────────────
# Sync Eudonet
# ──────────────────────────────────────────────


@router.post("/sync/", response={202: dict}, summary="Déclencher la sync Eudonet")
def sync_internships_eudonet(request, year_id: int):
    academic_year = get_or_404(AcademicYear, year_id, "Année introuvable.")
    task_id = enqueue_sync_eudonet_internships(academic_year.pk)
    log_action(
        request,
        action="sync_eudonet_internships",
        detail=f"Tâche {task_id} lancée pour {academic_year}",
    )
    return 202, {"task_id": task_id, "message": "Synchronisation Eudonet lancée."}


# ──────────────────────────────────────────────
# Import Excel
# ──────────────────────────────────────────────


@router.post("/import/", response={202: dict}, summary="Importer depuis Excel")
def import_internships_excel(request, year_id: int, file: UploadedFile = File(...)):
    if not (file.name or "").endswith((".xlsx", ".xls")):
        raise HttpError(400, "Seuls les fichiers .xlsx et .xls sont acceptés.")
    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HttpError(400, "Fichier trop volumineux (max 5 Mo).")
    academic_year = get_or_404(AcademicYear, year_id, "Année introuvable.")
    task_id = enqueue_import_excel_internships(
        academic_year.pk, file_bytes, file.name or "upload.xlsx"
    )
    log_action(
        request,
        action="import_excel_internships",
        detail=f"Fichier {file.name} — Tâche {task_id} lancée",
    )
    return 202, {"task_id": task_id, "message": "Import Excel lancé en arrière-plan."}


# ──────────────────────────────────────────────
# Export & template
# ──────────────────────────────────────────────


@router.get("/export/", summary="Exporter les stages en Excel")
def export_internships(
    request,
    year_id: int | None = None,
    country_id: int | None = None,
):
    import openpyxl

    from app.shared.excel_utils import (
        build_filename,
        workbook_response,
        write_header_row,
    )

    qs = Internship.objects.select_related(
        "student", "academic_year", "country"
    ).order_by("-start_date", "student__last_name")
    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    if country_id:
        qs = qs.filter(country_id=country_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stages"

    headers = [
        "INE",
        "Étudiant",
        "Entreprise",
        "Pays",
        "Ville",
        "Type",
        "Titre",
        "Date début",
        "Date fin",
        "Nb semaines",
        "Tuteur école",
        "Tuteur entreprise",
        "Statut",
    ]
    widths = [14, 30, 35, 20, 20, 16, 40, 12, 12, 10, 28, 28, 20]
    write_header_row(ws, headers, widths)

    for internship in qs:
        ws.append(
            [
                internship.student.ine,
                str(internship.student),
                internship.company_name,
                internship.country.name_fr if internship.country_id else "",
                internship.city,
                internship.internship_type,
                internship.title,
                internship.start_date.isoformat() if internship.start_date else "",
                internship.end_date.isoformat() if internship.end_date else "",
                internship.weeks_in_company,
                internship.school_tutor,
                internship.company_tutor,
                internship.status_label,
            ]
        )

    year_obj = AcademicYear.objects.filter(pk=year_id).first() if year_id else None
    year_slug = year_obj.label.replace("/", "-") if year_obj else ""
    filename = build_filename("stages", year_slug)
    return workbook_response(wb, filename)


@router.get("/template/", summary="Télécharger le gabarit Excel")
def download_internship_template(request, year_id: int):
    from .services.excel_template import generate_internship_template

    academic_year = get_or_404(AcademicYear, year_id, "Année introuvable.")
    file_bytes = generate_internship_template(academic_year)
    label_slug = academic_year.label.replace("/", "-")
    response = HttpResponse(
        file_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="template_stages_{label_slug}.xlsx"'
    )
    return response


# ──────────────────────────────────────────────
# Erreurs d'import
# ──────────────────────────────────────────────


@router.get(
    "/import-errors/",
    response=PagedResponse[InternshipImportErrorOut],
    summary="Liste des erreurs d'import",
)
def list_import_errors(
    request,
    year_id: int | None = None,
    pagination: PaginationQuery = Query(),
):
    latest_ids = (
        RawImport.objects.filter(entity=RawImportEntity.INTERNSHIP)
        .values("external_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    qs = RawImport.objects.filter(
        id__in=latest_ids,
        status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
    ).order_by("-created_at")
    if year_id:
        qs = qs.filter(academic_year_id=year_id)

    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count,
        page=pagination.page,
        page_size=pagination.page_size,
        results=items,
    )


@router.post(
    "/import-errors/{raw_import_id}/retry/",
    response=InternshipImportErrorOut,
    summary="Relancer un import en erreur",
)
def retry_import_error(request, raw_import_id: int):
    try:
        raw = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.INTERNSHIP,
            status=RawImportStatus.FAILED,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import introuvable.") from exc

    from app.integrations.eudonet import EudonetInternship
    from app.shared.validators import DomainValidationError

    from .services.sync_eudonet import (
        _resolve_academic_year,
        _resolve_country,
        _resolve_student,
    )

    row = EudonetInternship(payload=raw.payload)
    academic_year = raw.academic_year

    try:
        from .services.eudonet_validator import validate_internship_row

        validate_internship_row(row)
    except DomainValidationError as exc:
        raw.error_message = str(exc)
        raw.save(update_fields=["error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    student = _resolve_student(row.ine, {})
    if student is None:
        msg = f"Étudiant introuvable (INE : {row.ine!r})."
        raw.error_message = msg
        raw.save(update_fields=["error_message", "updated_at"])
        raise HttpError(400, msg)

    country = _resolve_country(row.country_name, {})
    internship_year = _resolve_academic_year(row.start_date, academic_year)

    from django.utils import timezone

    Internship.objects.update_or_create(
        student=student,
        company_name=row.company_name,
        start_date=row.start_date,
        defaults={
            "academic_year": internship_year,
            "country": country,
            "city": row.city,
            "title": row.title,
            "internship_type": row.internship_type,
            "status_code": row.status_code,
            "status_label": row.status,
            "end_date": row.end_date,
            "weeks_in_company": row.weeks,
            "school_tutor": row.school_tutor,
            "company_tutor": row.company_tutor,
            "eudonet_label": row.libelle,
            "last_sync_eudonet": timezone.now(),
        },
    )

    raw.status = RawImportStatus.IMPORTED
    raw.error_message = ""
    raw.imported_at = timezone.now()
    raw.save(update_fields=["status", "error_message", "imported_at", "updated_at"])
    return raw


@router.post(
    "/import-errors/{raw_import_id}/ignore/",
    response=InternshipImportErrorOut,
    summary="Ignorer une erreur d'import",
)
def ignore_import_error(request, raw_import_id: int):
    raw = get_or_404(RawImport, raw_import_id, "Erreur d'import introuvable.")
    raw.status = RawImportStatus.IGNORED
    raw.error_message = (
        f"{raw.error_message}\nTraité manuellement par l'administrateur."
    ).strip()
    raw.save(update_fields=["status", "error_message", "updated_at"])
    return raw


@router.post(
    "/import-errors/{raw_import_id}/force/",
    response=InternshipImportErrorOut,
    summary="Forcer l'import avec payload corrigé",
)
def force_import_error(request, raw_import_id: int, corrected_payload: dict):
    raw = get_or_404(RawImport, raw_import_id, "Erreur d'import introuvable.")

    raw.payload = {**raw.payload, **corrected_payload}
    raw.save(update_fields=["payload", "updated_at"])

    from app.integrations.eudonet import EudonetInternship
    from app.shared.validators import DomainValidationError

    from .services.eudonet_validator import validate_internship_row
    from .services.sync_eudonet import (
        _resolve_academic_year,
        _resolve_country,
        _resolve_student,
    )

    row = EudonetInternship(payload=raw.payload)
    academic_year = raw.academic_year

    try:
        validate_internship_row(row)
    except DomainValidationError as exc:
        raw.error_message = str(exc)
        raw.save(update_fields=["error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    student = _resolve_student(row.ine, {})
    if student is None:
        msg = f"Étudiant introuvable (INE : {row.ine!r})."
        raw.error_message = msg
        raw.save(update_fields=["error_message", "updated_at"])
        raise HttpError(400, msg)

    country = _resolve_country(row.country_name, {})
    internship_year = _resolve_academic_year(row.start_date, academic_year)

    from django.utils import timezone

    Internship.objects.update_or_create(
        student=student,
        company_name=row.company_name,
        start_date=row.start_date,
        defaults={
            "academic_year": internship_year,
            "country": country,
            "city": row.city,
            "title": row.title,
            "internship_type": row.internship_type,
            "status_code": row.status_code,
            "status_label": row.status,
            "end_date": row.end_date,
            "weeks_in_company": row.weeks,
            "school_tutor": row.school_tutor,
            "company_tutor": row.company_tutor,
            "eudonet_label": row.libelle,
            "last_sync_eudonet": timezone.now(),
        },
    )

    raw.status = RawImportStatus.IMPORTED
    raw.error_message = ""
    raw.imported_at = timezone.now()
    raw.save(update_fields=["status", "error_message", "imported_at", "updated_at"])
    return raw


# ──────────────────────────────────────────────
# Detail CRUD — must be last: /{id}/ catches all paths not matched above
# ──────────────────────────────────────────────


@router.put("/{internship_id}/", response=InternshipOut, summary="Modifier un stage")
def update_internship(request, internship_id: int, payload: InternshipIn):
    internship = get_or_404(Internship, internship_id, "Stage introuvable.")
    for field, value in payload.model_dump().items():
        setattr(internship, field, value)
    save_validated(internship)
    return Internship.objects.select_related("student", "academic_year", "country").get(
        pk=internship.pk
    )


@router.delete("/{internship_id}/", response={204: None}, summary="Supprimer un stage")
def delete_internship(request, internship_id: int):
    internship = get_or_404(Internship, internship_id, "Stage introuvable.")
    _safe_delete(internship)
    return 204, None
