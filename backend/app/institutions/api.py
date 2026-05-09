from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from ninja import Router
from ninja.errors import HttpError

from .models import PartnerUniversity
from .schemas import PartnerUniversityIn, PartnerUniversityOut

router = Router()


def save_validated(instance):
    try:
        instance.full_clean()
        instance.save()
    except (IntegrityError, ValidationError) as exc:
        raise HttpError(400, str(exc)) from exc

    return instance


@router.get(
    "/universities/",
    response=list[PartnerUniversityOut],
    summary="Liste des universites partenaires",
)
def list_universities(request):
    return PartnerUniversity.objects.select_related("country").all()


@router.post(
    "/universities/",
    response={201: PartnerUniversityOut},
    summary="Creer une universite partenaire",
)
def create_university(request, payload: PartnerUniversityIn):
    university = PartnerUniversity(**payload.model_dump())
    return 201, save_validated(university)


@router.put(
    "/universities/{university_id}/",
    response=PartnerUniversityOut,
    summary="Modifier une universite partenaire",
)
def update_university(request, university_id: int, payload: PartnerUniversityIn):
    try:
        university = PartnerUniversity.objects.get(pk=university_id)
    except PartnerUniversity.DoesNotExist as exc:
        raise HttpError(404, "Universite partenaire introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(university, field, value)

    return save_validated(university)


@router.delete(
    "/universities/{university_id}/",
    response={204: None},
    summary="Supprimer une universite partenaire",
)
def delete_university(request, university_id: int):
    try:
        university = PartnerUniversity.objects.get(pk=university_id)
        university.delete()
    except PartnerUniversity.DoesNotExist as exc:
        raise HttpError(404, "Universite partenaire introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(
            400,
            "Cette universite partenaire est utilisee par une autre entite.",
        ) from exc

    return 204, None
