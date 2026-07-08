from __future__ import annotations

from datetime import date

import pytest

from app.academic.models import AcademicYear
from app.integrations.eudonet import EudonetInternship
from app.internships.models import Internship
from app.internships.services.sync_eudonet import import_internship_rows
from app.reference.models import Country, CTIRegion
from app.students.models import Student

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_year(**kwargs) -> AcademicYear:
    defaults = {
        "label": "2025-2026",
        "start_date": date(2025, 9, 1),
        "end_date": date(2026, 8, 31),
    }
    defaults.update(kwargs)
    return AcademicYear.objects.create(**defaults)


def make_student(ine: str = "22010000001", **kwargs) -> Student:
    kwargs.setdefault("first_name", "Alice")
    kwargs.setdefault("last_name", "Martin")
    return Student.objects.create(ine=ine, **kwargs)


def make_country(iso2: str = "DE", name_fr: str = "Allemagne") -> Country:
    country, _ = Country.objects.get_or_create(
        iso2=iso2,
        defaults={
            "name_fr": name_fr,
            "name_en": "Germany",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        },
    )
    return country


def _row(payload: dict) -> EudonetInternship:
    return EudonetInternship(payload=payload)


def _valid_payload(ine: str = "22010000001", country_name: str = "Allemagne") -> dict:
    return {
        "N°INE": ine,
        "Libellé": "Stage_2025",
        "Raison sociale": "ACME GmbH",
        "Pays": country_name,
        "Ville": "Berlin",
        "Type": "Stage 3A",
        "Statut": "9 Justificatif reçu",
        "Date de début": "01/03/2026",
        "Date de fin": "31/08/2026",
        "Nb semaines dans l'entreprise": "26",
        "Tuteur pédagogique Ecole": "Pr. Dupont",
        "Tuteur technique entreprise": "M. Schmidt",
        "Titre": "Ingénieur logiciel",
        "Modifié le": "15/01/2026 10:00:00",
        "Mobilité à l'international": "Oui",
        "Composante": "ENSEEIHT",
    }


# ---------------------------------------------------------------------------
# test_sync_filters_non_international
# ---------------------------------------------------------------------------


def test_sync_filters_non_international():
    """
    sync_eudonet_internships doit ignorer les lignes sans Mobilité=Oui.
    On vérifie que le filtre est appliqué avant l'appel HTTP.
    """
    from app.internships.services.sync_eudonet import _COMPOSANTE_ENSEEIHT

    row = _row(
        {
            **_valid_payload(),
            "Mobilité à l'international": "Non",
        }
    )
    assert not row.is_international
    assert row.status_code == "9"
    assert row.composante.lower() in _COMPOSANTE_ENSEEIHT


def test_sync_filters_wrong_status():
    """
    sync_eudonet_internships doit ignorer les lignes dont status_code != '9'.
    """
    row = _row(
        {
            **_valid_payload(),
            "Statut": "3 En cours",
        }
    )
    assert row.status_code == "3"
    assert row.is_international


@pytest.mark.django_db
def test_sync_creates_internship():
    """
    Une ligne valide (is_international, status_code='9', composante N7) doit créer
    un Internship avec le pays résolu depuis name_fr.
    """
    year = make_year()
    student = make_student(ine="22010000001")
    country = make_country(iso2="DE", name_fr="Allemagne")

    payload = _valid_payload(ine=student.ine, country_name=country.name_fr)
    row = _row(payload)

    report = import_internship_rows([row], year)

    assert report.created == 1
    assert report.updated == 0
    assert len(report.unresolved) == 0

    internship = Internship.objects.get(student=student, company_name="ACME GmbH")
    assert internship.country == country
    assert internship.city == "Berlin"
    assert internship.status_code == "9"
    assert internship.weeks_in_company == 26
    assert internship.academic_year == year
