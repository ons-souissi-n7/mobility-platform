from typing import Generic, TypeVar

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ninja import Query, Schema
from ninja.errors import HttpError

T = TypeVar("T")


class SelectOption(Schema):
    id: int
    label: str


class PagedResponse(Schema, Generic[T]):  # noqa: UP046
    count: int
    page: int
    page_size: int
    results: list[T]


class PaginationQuery(Schema):
    page: int = Query(1, ge=1)
    page_size: int = Query(50, ge=1, le=500)


class LargePaginationQuery(Schema):
    """Pagination pour les endpoints qui peuvent retourner de grands volumes (ex: résultats d'affectation)."""

    page: int = Query(1, ge=1)
    page_size: int = Query(500, ge=1, le=5000)


def paginate(qs, page: int, page_size: int):
    offset = (page - 1) * page_size
    count = qs.count()
    items = list(qs[offset : offset + page_size])
    return count, items


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
