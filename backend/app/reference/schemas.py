from ninja import Schema


class CountryIn(Schema):
    iso2: str
    name_fr: str
    name_en: str
    cti_region: str


class CountryOut(Schema):
    id: int
    iso2: str
    name_fr: str
    name_en: str
    cti_region: str


class DepartmentIn(Schema):
    code: str
    name: str


class DepartmentOut(Schema):
    id: int
    code: str
    name: str
