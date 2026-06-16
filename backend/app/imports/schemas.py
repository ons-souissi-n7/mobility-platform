from datetime import datetime

from ninja import Schema


class ImportErrorItem(Schema):
    """Un enregistrement rejeté dans un rapport d'import."""

    external_id: str
    reason: str
    raw_import_id: int | None = None
    is_conflict: bool = False


class ImportReportOut(Schema):
    id: int
    source: str
    source_display: str
    academic_year_id: int | None
    academic_year_label: str | None
    total: int
    success_count: int
    error_count: int
    duplicate_count: int
    errors: list[ImportErrorItem]
    triggered_by: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_source_display(obj) -> str:
        return obj.get_source_display()

    @staticmethod
    def resolve_academic_year_label(obj) -> str | None:
        if obj.academic_year_id:
            return obj.academic_year.label
        return None


class ImportReportListOut(Schema):
    """Version allégée pour la liste (sans le détail des erreurs)."""

    id: int
    source: str
    source_display: str
    academic_year_id: int | None
    academic_year_label: str | None
    total: int
    success_count: int
    error_count: int
    duplicate_count: int
    triggered_by: str
    created_at: datetime

    @staticmethod
    def resolve_source_display(obj) -> str:
        return obj.get_source_display()

    @staticmethod
    def resolve_academic_year_label(obj) -> str | None:
        if obj.academic_year_id:
            return obj.academic_year.label
        return None
