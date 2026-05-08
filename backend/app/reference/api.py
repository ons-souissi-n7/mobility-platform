from ninja import Router

from .models import Country, Department
from .schemas import CountryOut, DepartmentOut

router = Router()


@router.get("/countries/", response=list[CountryOut], summary="Liste des pays")
def list_countries(request):
    return Country.objects.all()


@router.get(
    "/departments/",
    response=list[DepartmentOut],
    summary="Liste des departements",
)
def list_departments(request):
    return Department.objects.all()
