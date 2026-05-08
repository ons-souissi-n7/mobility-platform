from ninja import Schema


class CountryOut(Schema):
    id: int
    iso2: str
    name_fr: str
    name_en: str
    cti_region: str


class DepartmentOut(Schema):
    id: int
    code: str
    name: str
