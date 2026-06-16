import pytest

from app.institutions.models import (
    PartnerUniversity,
    PartnerUniversityRawImport,
    PartnerUniversityRawImportStatus,
)
from app.institutions.services.sync_moveon import sync_moveon_institutions
from app.integrations.moveon import MoveOnInstitution
from app.reference.models import Country, CTIRegion


class FakeClient:
    def __init__(self, payloads):
        self.payloads = payloads

    def fetch_institutions(self):
        return [MoveOnInstitution(payload=payload) for payload in self.payloads]


@pytest.mark.django_db
class TestMoveOnInstitutionSync:
    def test_sync_creates_partner_universities_and_countries(self):
        create_country()

        result = sync_moveon_institutions(FakeClient([institution_payload()]))

        assert result.total == 1
        assert result.created == 1
        assert PartnerUniversity.objects.filter(moveon_id=1359).exists()
        assert Country.objects.filter(iso2="IT").exists()
        assert PartnerUniversityRawImport.objects.filter(
            status=PartnerUniversityRawImportStatus.IMPORTED
        ).exists()

    def test_sync_updates_existing_partner_university(self):
        create_country()
        sync_moveon_institutions(FakeClient([institution_payload()]))
        payload = institution_payload(name="University of Trento Updated")

        result = sync_moveon_institutions(FakeClient([payload]))

        university = PartnerUniversity.objects.get(moveon_id=1359)
        assert result.created == 0
        assert result.updated == 1
        assert university.name == "University of Trento Updated"

    def test_sync_marks_invalid_payload_as_failed(self):
        create_country()
        payload = institution_payload()
        payload.pop("moveon_id")

        result = sync_moveon_institutions(FakeClient([payload]))

        assert result.failed == 1
        assert not PartnerUniversity.objects.exists()
        assert PartnerUniversityRawImport.objects.filter(
            status=PartnerUniversityRawImportStatus.FAILED
        ).exists()

    def test_sync_matches_country_by_french_name_without_iso2(self):
        create_country()
        payload = institution_payload(country={"name": "Italie"})

        result = sync_moveon_institutions(FakeClient([payload]))

        university = PartnerUniversity.objects.get(moveon_id=1359)
        assert result.created == 1
        assert university.country.iso2 == "IT"

    def test_sync_matches_country_by_english_name_without_iso2(self):
        create_country()
        payload = institution_payload(country={"name": "Italy"})

        result = sync_moveon_institutions(FakeClient([payload]))

        university = PartnerUniversity.objects.get(moveon_id=1359)
        assert result.created == 1
        assert university.country.iso2 == "IT"

    def test_sync_matches_country_with_typo(self):
        create_country()
        payload = institution_payload(country={"name": "Itallie"})

        result = sync_moveon_institutions(FakeClient([payload]))

        university = PartnerUniversity.objects.get(moveon_id=1359)
        assert result.created == 1
        assert university.country.iso2 == "IT"

    def test_sync_matches_country_with_separator_variant(self):
        create_country(iso2="NL", name_fr="Pays-Bas", name_en="Netherlands")
        payload = institution_payload(country={"name": "Pays Bas"})

        result = sync_moveon_institutions(FakeClient([payload]))

        university = PartnerUniversity.objects.get(moveon_id=1359)
        assert result.created == 1
        assert university.country.iso2 == "NL"

    def test_fallback_finds_manual_university_by_erasmus_code_and_backfills_moveon_id(
        self,
    ):
        # Université créée manuellement sans moveon_id mais avec erasmus_code.
        country = create_country()
        PartnerUniversity.objects.create(
            moveon_id=None,
            name="Universita di Trento",
            erasmus_code="I TRENTO01",
            country=country,
        )

        result = sync_moveon_institutions(FakeClient([institution_payload()]))

        assert result.created == 0
        assert result.updated == 1
        assert PartnerUniversity.objects.count() == 1  # pas de doublon
        univ = PartnerUniversity.objects.get(erasmus_code__icontains="TRENTO01")
        assert univ.moveon_id == 1359  # ID renseigné automatiquement

    def test_fallback_finds_manual_university_by_name_and_backfills_moveon_id(self):
        # Université créée manuellement sans moveon_id et sans erasmus_code.
        country = create_country()
        PartnerUniversity.objects.create(
            moveon_id=None,
            name="University of Trento",
            erasmus_code="",
            country=country,
        )

        result = sync_moveon_institutions(FakeClient([institution_payload()]))

        assert result.created == 0
        assert result.updated == 1
        assert PartnerUniversity.objects.count() == 1
        univ = PartnerUniversity.objects.get(name="University of Trento")
        assert univ.moveon_id == 1359

    def test_sync_marks_unknown_country_as_failed(self):
        payload = institution_payload(country={"name": "Atlantide"})

        result = sync_moveon_institutions(FakeClient([payload]))

        assert result.failed == 1
        assert PartnerUniversityRawImport.objects.filter(
            status=PartnerUniversityRawImportStatus.FAILED,
            error_message__contains="Unknown country name",
        ).exists()


def institution_payload(**overrides):
    payload = {
        "moveon_id": 1359,
        "name": "University of Trento",
        "short_name": "",
        "translated_name": "",
        "erasmus_code": "I TRENTO01",
        "city": "Trento",
        "url": "https://www.unitn.it/en",
        "email": "",
        "country": {
            "iso2": "IT",
            "name_fr": "Italie",
            "name_en": "Italy",
            "cti_region": "europe_hors_france",
        },
    }
    payload.update(overrides)
    return payload


def create_country(iso2="IT", name_fr="Italie", name_en="Italy"):
    return Country.objects.create(
        iso2=iso2,
        name_fr=name_fr,
        name_en=name_en,
        cti_region=CTIRegion.EUROPE_HORS_FRANCE,
    )
