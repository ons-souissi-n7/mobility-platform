from __future__ import annotations

from datetime import date, datetime

from ninja import Schema


class InternshipOut(Schema):
    id: int
    student_id: int
    student_ine: str
    student_name: str
    academic_year_id: int | None
    academic_year_label: str | None
    company_name: str
    country_id: int | None
    country_name_fr: str | None
    city: str
    title: str
    internship_type: str
    status_code: str
    status_label: str
    start_date: date | None
    end_date: date | None
    weeks_in_company: int | None
    school_tutor: str
    company_tutor: str
    eudonet_label: str
    last_sync_eudonet: datetime | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_student_ine(obj) -> str:
        return obj.student.ine

    @staticmethod
    def resolve_student_name(obj) -> str:
        return str(obj.student)

    @staticmethod
    def resolve_academic_year_label(obj) -> str | None:
        return obj.academic_year.label if obj.academic_year_id else None

    @staticmethod
    def resolve_country_name_fr(obj) -> str | None:
        return obj.country.name_fr if obj.country_id else None


class InternshipIn(Schema):
    student_id: int
    company_name: str
    country_id: int | None = None
    city: str = ""
    title: str = ""
    internship_type: str = ""
    status_code: str = ""
    status_label: str = ""
    start_date: date | None = None
    end_date: date | None = None
    weeks_in_company: int | None = None
    school_tutor: str = ""
    company_tutor: str = ""
    academic_year_id: int | None = None


class InternshipImportErrorOut(Schema):
    id: int
    external_id: str
    payload: dict
    error_message: str
    status: str
    created_at: datetime
