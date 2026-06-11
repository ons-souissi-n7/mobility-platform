from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ninja.errors import HttpError


def save_validated(instance):
    try:
        instance.full_clean()
        instance.save()
    except (IntegrityError, ValidationError) as exc:
        raise HttpError(400, str(exc)) from exc
    return instance


def get_or_404(model, pk: int, message: str):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist as exc:
        raise HttpError(404, message) from exc
