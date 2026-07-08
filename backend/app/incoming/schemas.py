from __future__ import annotations

from datetime import date, datetime

from ninja import Schema


class IncomingStudentOut(Schema):
    id: int
    academic_year_id: int
    academic_year_label: str
    department_id: int | None
    department_code: str | None
    department_name: str | None
    civility: str
    last_name: str
    first_name: str
    country_id: int | None
    country_name_fr: str | None
    origin_university_id: int | None
    origin_university_name: str
    birth_date: date | None
    mobility_category_id: int | None
    mobility_category_name: str | None
    personal_email: str
    n7_email: str
    duration: str
    level_id: int | None
    level_code: str | None
    level_name: str | None
    parcours_id: int | None
    parcours_code: str | None
    remarks: str
    internship_info: str
    diploma_info: str
    doctoral_continuation: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_academic_year_label(obj) -> str:
        return obj.academic_year.label

    @staticmethod
    def resolve_department_code(obj) -> str | None:
        return obj.department.code if obj.department_id else None

    @staticmethod
    def resolve_department_name(obj) -> str | None:
        return obj.department.name if obj.department_id else None

    @staticmethod
    def resolve_country_name_fr(obj) -> str | None:
        return obj.country.name_fr if obj.country_id else None

    @staticmethod
    def resolve_mobility_category_name(obj) -> str | None:
        return obj.mobility_category.name if obj.mobility_category_id else None

    @staticmethod
    def resolve_level_code(obj) -> str | None:
        return obj.level.code if obj.level_id else None

    @staticmethod
    def resolve_level_name(obj) -> str | None:
        return obj.level.name if obj.level_id else None

    @staticmethod
    def resolve_parcours_code(obj) -> str | None:
        return obj.parcours.code if obj.parcours_id else None


class IncomingStudentIn(Schema):
    academic_year_id: int
    department_id: int | None = None
    civility: str = ""
    last_name: str
    first_name: str
    country_id: int | None = None
    origin_university_id: int | None = None
    origin_university_name: str = ""
    birth_date: date | None = None
    mobility_category_id: int | None = None
    personal_email: str = ""
    n7_email: str = ""
    duration: str = ""
    level_id: int | None = None
    parcours_id: int | None = None
    remarks: str = ""
    internship_info: str = ""
    diploma_info: str = ""
    doctoral_continuation: bool = False


class IncomingImportErrorOut(Schema):
    id: int
    external_id: str
    payload: dict
    error_message: str
    status: str
    created_at: datetime


class IncomingStatsRow(Schema):
    dimension: str
    department_code: str | None
    department_name: str | None
    academic_year_label: str
    count: int
