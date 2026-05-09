import pytest
from django.db import IntegrityError

from app.institutions.models import PartnerUniversity
from app.reference.models import Country, CTIRegion


@pytest.mark.django_db
class TestPartnerUniversity:
    def setup_method(self):
        self.country = Country.objects.create(
            iso2="ES",
            name_fr="Espagne",
            name_en="Spain",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )

    def test_create_partner_university(self):
        university = PartnerUniversity.objects.create(
            moveon_id=123,
            name="Universidad Politecnica de Madrid",
            short_name="UPM",
            erasmus_code="E MADRID05",
            city="Madrid",
            country=self.country,
        )

        assert university.pk is not None
        assert str(university) == "Universidad Politecnica de Madrid (ES)"

    def test_moveon_id_unique(self):
        PartnerUniversity.objects.create(
            moveon_id=123,
            name="Universidad Politecnica de Madrid",
            country=self.country,
        )

        with pytest.raises(IntegrityError):
            PartnerUniversity.objects.create(
                moveon_id=123,
                name="Universidad Complutense de Madrid",
                country=self.country,
            )

    def test_moveon_id_can_be_blank(self):
        first = PartnerUniversity.objects.create(
            name="Universidad Politecnica de Madrid",
            country=self.country,
        )
        second = PartnerUniversity.objects.create(
            name="Universidad Complutense de Madrid",
            country=self.country,
        )

        assert first.moveon_id is None
        assert second.moveon_id is None
