import datetime

from ninja import File, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile

from app.academic.models import AcademicYear
from app.alerts.models import AlertLevel, SystemAlert
from app.reference.models import Country
from app.students.models import Student

from .models import ComplementaryMobility, MobilityStatus
from .services.minio_service import get_presigned_url, upload_document

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
    reason: str = ""


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
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, "Étudiant introuvable.") from exc

    qs = ComplementaryMobility.objects.filter(student=student).select_related(
        "academic_year", "destination_country"
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
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, "Étudiant introuvable.") from exc

    try:
        academic_year = AcademicYear.objects.get(pk=academic_year_id)
    except AcademicYear.DoesNotExist as exc:
        raise HttpError(404, "Année académique introuvable.") from exc

    try:
        country = Country.objects.get(pk=country_id)
    except Country.DoesNotExist as exc:
        raise HttpError(404, "Pays introuvable.") from exc

    if not experience_type.strip():
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

    key = upload_document(file_bytes, document.name or "document", content_type)

    mobility = ComplementaryMobility.objects.create(
        student=student,
        academic_year=academic_year,
        experience_type=experience_type.strip(),
        destination_country=country,
        destination_institution=destination_institution,
        start_date=start_date,
        end_date=end_date,
        document_key=key,
        document_name=document.name or "document",
    )

    SystemAlert.objects.create(
        level=AlertLevel.WARNING,
        title="Nouvelle mobilité complémentaire déclarée",
        message=(
            f"L'étudiant {student.first_name} {student.last_name} (INE : {ine}) "
            f"a déclaré une mobilité complémentaire "
            f"({experience_type.strip()}, {country.name_fr}, {academic_year.label})."
        ),
    )

    return 201, ComplementaryMobilityOut.from_obj(mobility)


# ── Admin routes ─────────────────────────────────────────────────────────────


def _get_pending_mobility(mobility_id: int) -> ComplementaryMobility:
    try:
        mob = ComplementaryMobility.objects.select_related(
            "academic_year", "destination_country"
        ).get(pk=mobility_id)
    except ComplementaryMobility.DoesNotExist as exc:
        raise HttpError(404, "Mobilité introuvable.") from exc
    if mob.status != MobilityStatus.PENDING:
        raise HttpError(409, "La mobilité n'est pas en attente de validation.")
    return mob


@router.get(
    "/",
    response=list[ComplementaryMobilityOut],
    summary="Lister toutes les mobilités complémentaires (admin)",
)
def list_all_mobilities(request, status: str | None = None):
    qs = ComplementaryMobility.objects.select_related(
        "student", "academic_year", "destination_country"
    ).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    return [ComplementaryMobilityOut.from_obj(m) for m in qs]


@router.post(
    "/{mobility_id}/validate/",
    response={200: ComplementaryMobilityOut},
    summary="Valider une mobilité complémentaire (admin)",
)
def validate_mobility(request, mobility_id: int):
    mob = _get_pending_mobility(mobility_id)
    mob.validate()
    mob.save()
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
    return ComplementaryMobilityOut.from_obj(mob)
