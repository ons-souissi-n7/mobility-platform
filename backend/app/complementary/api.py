import datetime

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from ninja import File, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile
from pydantic import field_validator

from app.academic.models import AcademicYear
from app.alerts.models import AlertLevel, SystemAlert
from app.audit.logger import log_action
from app.reference.models import Country
from app.students.models import Student

from .models import ComplementaryMobility, MobilityStatus
from .services.minio_service import delete_document, get_presigned_url, upload_document

router = Router()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Schemas ─────────────────────────────────────────────────────────────────


class CountryOut(Schema):
    id: int
    iso2: str
    name_fr: str


class ComplementaryMobilityOut(Schema):
    id: int
    student_ine: str
    student_first_name: str
    student_last_name: str
    academic_year_id: int
    academic_year_label: str
    experience_type: str
    destination_country_id: int
    destination_country_name: str
    destination_institution: str
    start_date: datetime.date
    end_date: datetime.date
    document_name: str
    document_url: str | None
    status: str
    status_label: str
    rejection_reason: str
    created_at: datetime.datetime

    @staticmethod
    def from_obj(obj: ComplementaryMobility) -> "ComplementaryMobilityOut":
        doc_url = None
        if obj.document_key:
            try:
                doc_url = get_presigned_url(obj.document_key)
            except Exception:
                pass
        return ComplementaryMobilityOut(
            id=obj.id,
            student_ine=obj.student.ine,
            student_first_name=obj.student.first_name,
            student_last_name=obj.student.last_name,
            academic_year_id=obj.academic_year_id,
            academic_year_label=obj.academic_year.label,
            experience_type=obj.experience_type,
            destination_country_id=obj.destination_country_id,
            destination_country_name=obj.destination_country.name_fr,
            destination_institution=obj.destination_institution,
            start_date=obj.start_date,
            end_date=obj.end_date,
            document_name=obj.document_name,
            document_url=doc_url,
            status=obj.status,
            status_label=obj.get_status_display(),
            rejection_reason=obj.rejection_reason,
            created_at=obj.created_at,
        )


class RejectIn(Schema):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Le motif de rejet est obligatoire.")
        return stripped


class MobilityEditIn(Schema):
    status: str
    rejection_reason: str = ""


class PagedOut(Schema):
    count: int
    page: int
    page_size: int
    results: list[ComplementaryMobilityOut]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_student(ine: str) -> Student:
    try:
        return Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, "Étudiant introuvable.") from exc


def _resolve_mobility_alert(mob: "ComplementaryMobility") -> None:
    """Marque comme lue l'alerte liée à cette mobilité complémentaire."""
    SystemAlert.objects.filter(
        is_read=False,
        academic_year=mob.academic_year,
        title="Nouvelle mobilité complémentaire déclarée",
        message__icontains=f"INE : {mob.student.ine}",
    ).update(is_read=True, read_at=timezone.now())


# ── Reference data ───────────────────────────────────────────────────────────


@router.get(
    "/countries/",
    response=list[CountryOut],
    summary="Liste des pays (référentiel)",
)
def list_countries(request):
    return [
        CountryOut(id=c.id, iso2=c.iso2, name_fr=c.name_fr)
        for c in Country.objects.order_by("name_fr")
    ]


# ── Student-facing routes ────────────────────────────────────────────────────


@router.get(
    "/student/{ine}/",
    response=list[ComplementaryMobilityOut],
    summary="Lister les mobilités complémentaires d'un étudiant",
)
def list_student_mobilities(request, ine: str, year_id: int | None = None):
    student = _get_student(ine)
    qs = ComplementaryMobility.objects.filter(student=student).select_related(
        "student", "academic_year", "destination_country"
    )
    if year_id is not None:
        qs = qs.filter(academic_year_id=year_id)
    return [ComplementaryMobilityOut.from_obj(m) for m in qs.order_by("-created_at")]


@router.post(
    "/student/{ine}/",
    response={201: ComplementaryMobilityOut},
    summary="Déclarer une mobilité complémentaire",
)
def declare_mobility(
    request,
    ine: str,
    academic_year_id: int,
    experience_type: str,
    country_id: int,
    destination_institution: str,
    start_date: datetime.date,
    end_date: datetime.date,
    document: UploadedFile = File(...),
):
    student = _get_student(ine)
    exp_type = experience_type.strip()

    try:
        academic_year = AcademicYear.objects.get(pk=academic_year_id)
    except AcademicYear.DoesNotExist as exc:
        raise HttpError(404, "Année académique introuvable.") from exc

    try:
        country = Country.objects.get(pk=country_id)
    except Country.DoesNotExist as exc:
        raise HttpError(404, "Pays introuvable.") from exc

    if not exp_type:
        raise HttpError(400, "Le type d'expérience est obligatoire.")

    if start_date >= end_date:
        raise HttpError(400, "La date de fin doit être postérieure à la date de début.")

    content_type = document.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HttpError(
            400,
            "Format de fichier non accepté. Formats acceptés : PDF, JPEG, PNG, WEBP.",
        )

    file_bytes = document.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HttpError(400, "Fichier trop volumineux (max 10 Mo).")

    doc_name = document.name or "document"
    key = upload_document(file_bytes, doc_name, content_type)

    mobility = ComplementaryMobility.objects.create(
        student=student,
        academic_year=academic_year,
        experience_type=exp_type,
        destination_country=country,
        destination_institution=destination_institution,
        start_date=start_date,
        end_date=end_date,
        document_key=key,
        document_name=doc_name,
    )

    SystemAlert.objects.create(
        level=AlertLevel.WARNING,
        title="Nouvelle mobilité complémentaire déclarée",
        message=(
            f"L'étudiant {student.first_name} {student.last_name} (INE : {ine}) "
            f"a déclaré une mobilité complémentaire "
            f"({exp_type}, {country.name_fr}, {academic_year.label})."
        ),
        academic_year=academic_year,
    )

    return 201, ComplementaryMobilityOut.from_obj(mobility)


# ── Admin routes ─────────────────────────────────────────────────────────────


def _get_pending_mobility(mobility_id: int) -> ComplementaryMobility:
    try:
        mob = ComplementaryMobility.objects.select_related(
            "student", "academic_year", "destination_country"
        ).get(pk=mobility_id)
    except ComplementaryMobility.DoesNotExist as exc:
        raise HttpError(404, "Mobilité introuvable.") from exc
    if mob.status != MobilityStatus.PENDING:
        raise HttpError(409, "La mobilité n'est pas en attente de validation.")
    return mob


@router.get(
    "/",
    response=PagedOut,
    summary="Lister toutes les mobilités complémentaires (admin)",
)
def list_all_mobilities(
    request,
    status: str | None = None,
    student_search: str | None = None,
    experience_type: str | None = None,
    year_id: int | None = None,
    page: int = 1,
    page_size: int = 25,
):
    qs = ComplementaryMobility.objects.select_related(
        "student", "academic_year", "destination_country"
    ).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    if student_search:
        qs = qs.filter(
            Q(student__ine__icontains=student_search)
            | Q(student__last_name__icontains=student_search)
            | Q(student__first_name__icontains=student_search)
        )
    if experience_type:
        qs = qs.filter(experience_type__icontains=experience_type)
    if year_id:
        qs = qs.filter(academic_year_id=year_id)
    count = qs.count()
    offset = (page - 1) * page_size
    results = [
        ComplementaryMobilityOut.from_obj(m) for m in qs[offset : offset + page_size]
    ]
    return PagedOut(count=count, page=page, page_size=page_size, results=results)


@router.post(
    "/{mobility_id}/validate/",
    response={200: ComplementaryMobilityOut},
    summary="Valider une mobilité complémentaire (admin)",
)
def validate_mobility(request, mobility_id: int):
    mob = _get_pending_mobility(mobility_id)
    mob.validate()
    retention_days = getattr(settings, "DOCUMENT_RETENTION_DAYS", 5 * 365)
    mob.document_retention_until = datetime.date.today() + datetime.timedelta(
        days=retention_days
    )
    mob.save()
    _resolve_mobility_alert(mob)
    log_action(
        request,
        action="validate_complementary_mobility",
        detail=(
            f"Mobilité #{mob.id} validée — "
            f"{mob.student.last_name} {mob.student.first_name} ({mob.student.ine})"
        ),
    )
    return ComplementaryMobilityOut.from_obj(mob)


@router.post(
    "/{mobility_id}/reject/",
    response={200: ComplementaryMobilityOut},
    summary="Rejeter une mobilité complémentaire (admin)",
)
def reject_mobility(request, mobility_id: int, payload: RejectIn):
    mob = _get_pending_mobility(mobility_id)
    mob.reject(reason=payload.reason)
    mob.save()
    # Justificatif rejeté : plus besoin de le conserver
    if mob.document_key:
        delete_document(mob.document_key)
        ComplementaryMobility.objects.filter(pk=mob.pk).update(document_key="")
        mob.document_key = ""
    _resolve_mobility_alert(mob)
    log_action(
        request,
        action="reject_complementary_mobility",
        detail=(
            f"Mobilité #{mob.id} rejetée — "
            f"{mob.student.last_name} {mob.student.first_name} ({mob.student.ine}) "
            f"— Motif : {payload.reason}"
        ),
    )
    return ComplementaryMobilityOut.from_obj(mob)


@router.patch(
    "/{mobility_id}/",
    response=ComplementaryMobilityOut,
    summary="Modifier le statut / motif d'une mobilité complémentaire (admin)",
)
def update_mobility(request, mobility_id: int, payload: MobilityEditIn):
    valid_statuses = {
        MobilityStatus.PENDING,
        MobilityStatus.VALIDATED,
        MobilityStatus.REJECTED,
    }
    if payload.status not in valid_statuses:
        raise HttpError(400, f"Statut invalide : {payload.status}.")
    if (
        payload.status == MobilityStatus.REJECTED
        and not payload.rejection_reason.strip()
    ):
        raise HttpError(400, "Le motif de rejet est obligatoire.")
    try:
        mob = ComplementaryMobility.objects.select_related(
            "student", "academic_year", "destination_country"
        ).get(pk=mobility_id)
    except ComplementaryMobility.DoesNotExist as exc:
        raise HttpError(404, "Mobilité introuvable.") from exc
    rejection_reason = (
        payload.rejection_reason.strip()
        if payload.status == MobilityStatus.REJECTED
        else ""
    )
    # FSMField has protected=True: direct assignment and refresh_from_db() both
    # go through the descriptor and raise AttributeError. QuerySet.update()
    # writes directly to SQL, and re-fetching via get() initializes a fresh
    # Python object (status not yet in __dict__), so the descriptor allows it.
    ComplementaryMobility.objects.filter(pk=mob.pk).update(
        status=payload.status,
        rejection_reason=rejection_reason,
        updated_at=timezone.now(),
    )
    mob = ComplementaryMobility.objects.select_related(
        "student", "academic_year", "destination_country"
    ).get(pk=mob.pk)
    if payload.status != MobilityStatus.PENDING:
        _resolve_mobility_alert(mob)
    log_action(
        request,
        action="update_complementary_mobility",
        detail=(
            f"Mobilité #{mob.id} → statut {payload.status} — "
            f"{mob.student.last_name} {mob.student.first_name} ({mob.student.ine})"
        ),
    )
    return ComplementaryMobilityOut.from_obj(mob)


@router.delete(
    "/{mobility_id}/",
    response={204: None},
    summary="Supprimer une mobilité complémentaire (admin)",
)
def delete_mobility(request, mobility_id: int):
    try:
        mob = ComplementaryMobility.objects.select_related(
            "student", "academic_year"
        ).get(pk=mobility_id)
    except ComplementaryMobility.DoesNotExist as exc:
        raise HttpError(404, "Mobilité introuvable.") from exc
    log_action(
        request,
        action="delete_complementary_mobility",
        detail=(
            f"Mobilité #{mob.id} supprimée — "
            f"{mob.student.last_name} {mob.student.first_name} ({mob.student.ine}), "
            f"{mob.academic_year.label}"
        ),
    )
    if mob.document_key:
        delete_document(mob.document_key)
    mob.delete()
    return 204, None
