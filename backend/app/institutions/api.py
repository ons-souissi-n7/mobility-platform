from ninja import Router

from .models import PartnerUniversity
from .schemas import PartnerUniversityOut

router = Router()


@router.get(
    "/universities/",
    response=list[PartnerUniversityOut],
    summary="Liste des universites partenaires",
)
def list_universities(request):
    return PartnerUniversity.objects.select_related("country").all()
