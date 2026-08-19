from __future__ import annotations

from io import BytesIO

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation

from app.shared.excel_utils import write_header_row

_HEADERS = [
    "DEPARTEMENT",
    "CIVILITE",
    "NOM",
    "PRENOM",
    "PAYS",
    "UNIV ORIGINE",
    "DATE NAISSANCE",
    "CADRE",
    "MAIL",
    "MAIL ENSEEIHT",
    "DUREE",
    "ANNEE",
    "PARCOURS",
    "REMARQUES",
    "STAGE",
    "DIPLOME",
    "POURSUITE DOCTORAT",
]

_WIDTHS = [18, 10, 25, 25, 22, 40, 16, 25, 35, 35, 14, 18, 20, 30, 30, 30, 18]


def generate_incoming_template() -> bytes:
    from app.institutions.models import PartnerUniversity
    from app.mobility.models import MobilityCategory
    from app.reference.models import Country, Department, Level, Parcours

    countries = list(
        Country.objects.order_by("name_fr").values_list("name_fr", flat=True)
    )
    departments = list(
        Department.objects.order_by("code").values_list("code", flat=True)
    )
    civilities = ["M.", "Mme"]
    categories = list(
        MobilityCategory.objects.order_by("name").values_list("name", flat=True)
    )
    levels = list(Level.objects.order_by("code").values_list("code", flat=True))
    parcours_list = list(
        Parcours.objects.select_related("department")
        .order_by("department__code", "code")
        .values_list("code", flat=True)
    )
    universities = list(
        PartnerUniversity.objects.order_by("name").values_list("name", flat=True)
    )

    wb = openpyxl.Workbook()

    def _ref_sheet(name: str, values: list[str]):
        ws = wb.create_sheet(name)
        for v in values:
            ws.append([v])
        ws.sheet_state = "hidden"
        return ws

    _ref_sheet("_Pays", countries)
    _ref_sheet("_Departements", departments)
    _ref_sheet("_Civilites", civilities)
    _ref_sheet("_Cadres", categories)
    _ref_sheet("_Niveaux", levels)
    _ref_sheet("_Parcours", parcours_list)
    _ref_sheet("_Universites", universities)

    ws = wb.active
    ws.title = "Etudiants entrants"

    write_header_row(ws, _HEADERS, _WIDTHS)

    from openpyxl.styles import NamedStyle

    date_style = NamedStyle(name="date_dmy")
    date_style.number_format = "DD/MM/YYYY"
    wb.add_named_style(date_style)
    ws.column_dimensions["G"].number_format = "DD/MM/YYYY"

    def _dv(formula: str, col: str) -> None:
        dv = DataValidation(
            type="list",
            formula1=formula,
            allow_blank=True,
            showDropDown=False,
        )
        dv.sqref = f"{col}2:{col}10000"
        ws.add_data_validation(dv)

    if departments:
        _dv(f"_Departements!$A$1:$A${len(departments)}", "A")
    if civilities:
        _dv(f"_Civilites!$A$1:$A${len(civilities)}", "B")
    if countries:
        _dv(f"_Pays!$A$1:$A${len(countries)}", "E")
    if universities:
        _dv(f"_Universites!$A$1:$A${len(universities)}", "F")

    dv_date = DataValidation(
        type="date",
        operator="between",
        formula1="1900-01-01",
        formula2="2099-12-31",
        allow_blank=True,
        showDropDown=False,
    )
    dv_date.sqref = "G2:G10000"
    ws.add_data_validation(dv_date)

    if categories:
        _dv(f"_Cadres!$A$1:$A${len(categories)}", "H")
    if levels:
        _dv(f"_Niveaux!$A$1:$A${len(levels)}", "L")
    if parcours_list:
        _dv(f"_Parcours!$A$1:$A${len(parcours_list)}", "M")

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()
