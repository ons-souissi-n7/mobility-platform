from datetime import date

import pytest
from django.test import RequestFactory

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.integrations.moveon import MoveOnAgreement, MoveOnAgreementFramework
from app.mobility.api import list_agreements
from app.mobility.models import (
    Agreement,
    AgreementDepartmentConstraint,
    AgreementLevelConstraint,
    AgreementQuota,
    AgreementYearAvailability,
    DepartmentQuota,
    MobilityCategory,
    RawImport,
    RawImportStatus,
)
from app.mobility.services.quota_estimator import estimate_current_year_missing_quotas
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
        agreement = Agreement.objects.get(moveon_relation_id="REL-001")
        assert AgreementDepartmentConstraint.objects.filter(
            agreement=agreement,
            department__code="SN",
            is_active=True,
        ).exists()
        assert AgreementLevelConstraint.objects.filter(
            agreement=agreement,
            level__code="MASTER",
            is_active=True,
        ).exists()
        assert RawImport.objects.filter(status=RawImportStatus.IMPORTED).exists()

    def test_sync_creates_year_availability_override(self):
        create_university()

        sync_moveon_agreements(
            FakeClient(
                agreements=[
                    agreement_payload(
                        academic_year_label="2026-2027",
                        is_available_for_year=False,
                    )
                ]
            )
        )

        agreement = Agreement.objects.get(moveon_relation_id="REL-001")
        availability = AgreementYearAvailability.objects.get(agreement=agreement)
        assert availability.academic_year_label == "2026-2027"
        assert availability.is_available is False

    def test_sync_updates_existing_agreement(self):
        create_university()
        sync_moveon_agreements(FakeClient(agreements=[agreement_payload()]))
        payload = agreement_payload(name="Updated Erasmus agreement")

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        agreement = Agreement.objects.get(moveon_relation_id="REL-001")
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
            error_message__contains="partner_university reference",
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
            error_message__contains="partner university reference",
        ).exists()

    def test_sync_links_agreement_by_erasmus_code_when_moveon_id_is_missing(self):
        university = create_university()
        university.moveon_id = None
        university.erasmus_code = "I  NAPOLI01"
        university.save()
        payload = agreement_payload(partner_university_moveon_id=None)
        payload["Code Erasmus"] = "I NAPOLI01"

        result = sync_moveon_agreements(FakeClient(agreements=[payload]))

        agreement = Agreement.objects.get(moveon_relation_id="REL-001")
        assert result.created == 1
        assert agreement.partner_university == university

    def test_sync_creates_agreement_frameworks(self):
        result = sync_moveon_mobility_categories(
            FakeClient(frameworks=[framework_payload()])
        )

        framework = MobilityCategory.objects.get(moveon_framework_id="97")
        assert result.created == 1
        assert framework.name == "Job Shadowing - Echange de bonnes pratiques"

    def test_sync_mobility_imports_frameworks_and_agreements_only(self):
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

        agreement = Agreement.objects.get(moveon_relation_id="REL-001")
        assert result.frameworks.created == 1
        assert result.agreements.created == 1
        assert result.quotas.created == 1
        assert agreement.framework_ref is not None
        quota = AgreementQuota.objects.get(agreement=agreement)
        assert quota.source_total_places == 4
        assert quota.total_places >= 1
        assert DepartmentQuota.objects.filter(agreement_quota=quota).exists()

    def test_list_agreements_can_filter_by_partner_university(self):
        university = create_university()
        another_university = PartnerUniversity.objects.create(
            moveon_id=2002,
            name="Universidad Otra",
            country=create_country(),
        )
        Agreement.objects.create(
            moveon_relation_id="REL-001",
            name="Erasmus agreement A",
            partner_university=university,
        )
        Agreement.objects.create(
            moveon_relation_id="REL-002",
            name="Erasmus agreement B",
            partner_university=another_university,
        )

        request = RequestFactory().get(
            "/agreements/", {"partner_university_id": university.id}
        )
        agreements = list_agreements(request)

        assert len(agreements) == 1
        assert agreements[0].partner_university_id == university.id

    def test_estimates_current_year_missing_quota_from_last_five_years(self):
        agreement = create_agreement()
        department = Department.objects.create(code="SN", name="Sciences du Numerique")
        current_year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
        )
        past_year = AcademicYear.objects.create(
            label="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 8, 31),
        )
        past_quota = AgreementQuota.objects.create(
            agreement=agreement,
            academic_year=past_year,
            academic_year_label=past_year.label,
            period="S1",
            total_places=5,
            remaining_places=1,
        )
        DepartmentQuota.objects.create(
            agreement_quota=past_quota,
            department=department,
            places=3,
        )
        agreement.start_date = current_year.start_date
        agreement.end_date = current_year.end_date
        agreement.save()

        result = estimate_current_year_missing_quotas()

        estimated_quota = AgreementQuota.objects.get(
            agreement=agreement,
            academic_year_label=current_year.label,
        )
        assert result.quota_created == 1
        assert estimated_quota.is_estimated is True
        assert estimated_quota.total_places == 5
        assert (
            DepartmentQuota.objects.get(
                agreement_quota=estimated_quota,
                department=department,
            ).is_estimated
            is True
        )


def agreement_payload(**overrides):
    payload = {
        "moveon_relation_id": "REL-001",
        "reference": "REF-001",
        "name": "Erasmus outgoing agreement",
        "partner_university_moveon_id": 1001,
        "relation_type": "Erasmus",
        "framework": "Erasmus Enseignement",
        "direction": "outgoing",
        "status": "active",
        "is_active": True,
        "start_date": "2026-09-01",
        "end_date": "2027-08-31",
        "start_academic_year": "2026-2027",
        "end_academic_year": "2027-2028",
        "discipline": "Engineering",
        "isced": "071",
        "level": "Master",
        "departments": ["SN"],
        "formation": "SN",
    }
    payload.update(overrides)
    return payload


def quota_payload(**overrides):
    payload = {
        "moveon_relation_id": "REL-001",
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
        moveon_relation_id="REL-001",
        name="Erasmus outgoing agreement",
        partner_university=create_university(),
    )
