from datetime import date

import pytest
from django.test import RequestFactory

from app.academic.models import AcademicYear
from app.imports.models import RawImport, RawImportStatus
from app.institutions.models import PartnerUniversity
from app.integrations.moveon import MoveOnAgreement, MoveOnAgreementFramework
from app.mobility.api import list_agreements
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    AgreementYear,
    AgreementYearDepartment,
    MobilityCategory,
)
from app.mobility.services.quota_estimator import initialize_new_year_mobility
from app.mobility.services.sync_moveon import (
    sync_moveon_agreements,
    sync_moveon_mobility,
    sync_moveon_mobility_categories,
)
from app.reference.models import Country, CTIRegion, Department


class FakeClient:
    def __init__(self, agreements=None, frameworks=None, quotas=None):
        self.agreements = agreements or []
        self.frameworks = frameworks or []
        self.quotas = quotas or []

    def fetch_agreements(self):
        return [MoveOnAgreement(payload=payload) for payload in self.agreements]

    def fetch_agreement_frameworks(self):
        return [
            MoveOnAgreementFramework(payload=payload) for payload in self.frameworks
        ]

    def fetch_agreement_quotas(self):
        return [MoveOnAgreement(payload=payload) for payload in self.quotas]


@pytest.mark.django_db
class TestMoveOnMobilitySync:
    def test_sync_creates_agreements(self):
        create_university()
        Department.objects.create(code="SN", name="Sciences du Numerique")

        result = sync_moveon_agreements(FakeClient(agreements=[agreement_payload()]))

        assert result.total == 1
        assert result.created == 1
        agreement = Agreement.objects.get(moveon_id="REL-001")
        assert AgreementDepartment.objects.filter(
            agreement=agreement, department__code="SN"
        ).exists()
        assert agreement.levels.filter(code="MASTER").exists()
        assert RawImport.objects.filter(status=RawImportStatus.IMPORTED).exists()

    def test_sync_updates_existing_agreement(self):
        create_university()
        sync_moveon_agreements(FakeClient(agreements=[agreement_payload()]))
        payload = agreement_payload(name="Updated Erasmus agreement")

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        agreement = Agreement.objects.get(moveon_id="REL-001")
        assert result.created == 0
        assert result.updated == 1
        assert agreement.name == "Updated Erasmus agreement"

    def test_sync_marks_invalid_agreement_as_failed(self):
        payload = agreement_payload()
        payload.pop("partner_university_moveon_id")

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        assert result.failed == 1
        assert not Agreement.objects.exists()
        assert RawImport.objects.filter(
            status=RawImportStatus.FAILED,
            error_message__icontains="université partenaire",
        ).exists()

    def test_sync_marks_invalid_agreement_as_failed_when_partner_university_is_missing(
        self,
    ):
        payload = agreement_payload(partner_university_moveon_id=9999)

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        assert result.failed == 1
        assert not Agreement.objects.exists()
        assert RawImport.objects.filter(
            status=RawImportStatus.FAILED,
            error_message__icontains="université partenaire",
        ).exists()

    def test_sync_links_agreement_by_erasmus_code_when_moveon_id_is_missing(self):
        university = create_university()
        university.moveon_id = None
        university.erasmus_code = "I  NAPOLI01"
        university.save()
        payload = agreement_payload(partner_university_moveon_id=None)
        payload["Code Erasmus"] = "I NAPOLI01"

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        agreement = Agreement.objects.get(moveon_id="REL-001")
        assert result.created == 1
        assert agreement.partner_university == university

    def test_sync_creates_agreement_frameworks(self):
        result = sync_moveon_mobility_categories(
            FakeClient(frameworks=[framework_payload()])
        )

        framework = MobilityCategory.objects.get(moveon_id="97")
        assert result.created == 1
        assert framework.name == "Job Shadowing - Echange de bonnes pratiques"

    def test_sync_mobility_updates_inp_total_places_from_quotas(self):
        create_university()
        Department.objects.create(code="SN", name="Sciences du Numerique")
        client = FakeClient(
            agreements=[agreement_payload()],
            frameworks=[
                framework_payload(moveon_framework_id="1", name="Erasmus Enseignement")
            ],
            quotas=[quota_payload()],
        )

        result = sync_moveon_mobility(client)

        agreement = Agreement.objects.get(moveon_id="REL-001")
        assert result.frameworks.created == 1
        assert result.agreements.created == 1
        assert result.quotas.updated == 1
        agreement.refresh_from_db()
        assert agreement.inp_total_places == 4

    def test_list_agreements_returns_all(self):
        university = create_university()
        another_university = PartnerUniversity.objects.create(
            moveon_id=2002,
            name="Universidad Otra",
            country=create_country(),
        )
        Agreement.objects.create(
            moveon_id="REL-001",
            name="Erasmus agreement A",
            partner_university=university,
        )
        Agreement.objects.create(
            moveon_id="REL-002",
            name="Erasmus agreement B",
            partner_university=another_university,
        )

        request = RequestFactory().get("/agreements/")
        agreements = list_agreements(request)

        assert len(agreements) == 2

    def test_initialize_new_year_creates_agreement_years(self):
        university = create_university()
        agreement = Agreement.objects.create(
            moveon_id="REL-001",
            name="Erasmus outgoing agreement",
            partner_university=university,
            inp_total_places=6,
        )
        dept = Department.objects.create(code="SN", name="Sciences du Numerique")
        AgreementDepartment.objects.create(agreement=agreement, department=dept)

        past_year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
            status=AcademicYear.CampaignStatus.CLOSED,
        )
        AgreementYear.objects.create(
            agreement=agreement,
            academic_year=past_year,
            is_active=True,
            n7_places=3,
        )

        new_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
        )

        result = initialize_new_year_mobility(new_year)

        assert result.year_instances_created == 1
        year_instance = AgreementYear.objects.get(
            agreement=agreement, academic_year=new_year
        )
        assert year_instance.n7_places == 3
        assert AgreementYearDepartment.objects.filter(
            agreement_year=year_instance
        ).exists()


def agreement_payload(**overrides):
    payload = {
        "moveon_id": "REL-001",
        "reference": "REF-001",
        "name": "Erasmus outgoing agreement",
        "partner_university_moveon_id": 1001,
        "relation_type": "Erasmus",
        "framework": "Erasmus Enseignement",
        "direction": "outgoing",
        "is_active": True,
        "start_date": "2026-09-01",
        "end_date": "2027-08-31",
        "departments": ["SN"],
        "level": "Master",
    }
    payload.update(overrides)
    return payload


def quota_payload(**overrides):
    payload = {
        "moveon_id": "REL-001",
        "academic_year_label": "2026-2027",
        "period": "S1",
        "places_id": "PLC-001",
        "total_places": 4,
        "remaining_places": 2,
        "total_duration": 12,
        "duration_unit": "months",
        "is_effective": True,
    }
    payload.update(overrides)
    return payload


def framework_payload(**overrides):
    payload = {
        "moveon_framework_id": "97",
        "name": "Job Shadowing - Echange de bonnes pratiques",
        "relation_types": "Offre de sejour",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def create_country():
    country, _ = Country.objects.get_or_create(
        iso2="ES",
        defaults={
            "name_fr": "Espagne",
            "name_en": "Spain",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        },
    )
    return country


def create_university():
    return PartnerUniversity.objects.create(
        moveon_id=1001,
        name="Universidad Test",
        country=create_country(),
    )


def create_academic_year():
    return AcademicYear.objects.create(
        label="2026-2027",
        start_date=date(2026, 9, 1),
        end_date=date(2027, 8, 31),
    )


def create_agreement():
    return Agreement.objects.create(
        moveon_id="REL-001",
        name="Erasmus outgoing agreement",
        partner_university=create_university(),
        inp_total_places=10,
    )
