"""
Centralized ETL data-cleaning helpers used across all sync pipelines.

Per report section 4.7.1: standardize → normalize → validate → persist.
"""

import unicodedata
from datetime import date

# ISO 3166-1 alpha-2 → canonical upper-case code.
# Maps common French/English names, ISO-2 and ISO-3 codes to their ISO-2 code.
_COUNTRY_ALIASES: dict[str, str] = {
    # ISO-2 → itself (quick lookup)
    "fr": "FR",
    "de": "DE",
    "es": "ES",
    "it": "IT",
    "pt": "PT",
    "gb": "GB",
    "uk": "GB",
    "us": "US",
    "be": "BE",
    "ch": "CH",
    "nl": "NL",
    "se": "SE",
    "no": "NO",
    "dk": "DK",
    "fi": "FI",
    "pl": "PL",
    "cz": "CZ",
    "at": "AT",
    "ro": "RO",
    "hu": "HU",
    "sk": "SK",
    "si": "SI",
    "hr": "HR",
    "bg": "BG",
    "gr": "GR",
    "lt": "LT",
    "lv": "LV",
    "ee": "EE",
    "ie": "IE",
    "lu": "LU",
    "cy": "CY",
    "mt": "MT",
    "ma": "MA",
    "tn": "TN",
    "dz": "DZ",
    "sn": "SN",
    "cm": "CM",
    "ci": "CI",
    "mg": "MG",
    "ml": "ML",
    "bj": "BJ",
    "bf": "BF",
    "ne": "NE",
    "td": "TD",
    "gn": "GN",
    "rw": "RW",
    "cd": "CD",
    "cg": "CG",
    "ga": "GA",
    "tg": "TG",
    "mr": "MR",
    "km": "KM",
    "dj": "DJ",
    "bi": "BI",
    "sc": "SC",
    "br": "BR",
    "ar": "AR",
    "cl": "CL",
    "co": "CO",
    "mx": "MX",
    "cn": "CN",
    "jp": "JP",
    "kr": "KR",
    "in": "IN",
    "au": "AU",
    "ca": "CA",
    "nz": "NZ",
    "za": "ZA",
    "tr": "TR",
    "ru": "RU",
    "ua": "UA",
    "rs": "RS",
    "ba": "BA",
    "al": "AL",
    "mk": "MK",
    "me": "ME",
    "xk": "XK",
    # ISO-3 codes
    "fra": "FR",
    "deu": "DE",
    "esp": "ES",
    "ita": "IT",
    "prt": "PT",
    "gbr": "GB",
    "usa": "US",
    "bel": "BE",
    "che": "CH",
    "nld": "NL",
    "swe": "SE",
    "nor": "NO",
    "dnk": "DK",
    "fin": "FI",
    "pol": "PL",
    "cze": "CZ",
    "aut": "AT",
    "rou": "RO",
    "hun": "HU",
    "svk": "SK",
    "svn": "SI",
    "hrv": "HR",
    "bgr": "BG",
    "grc": "GR",
    "ltu": "LT",
    "lva": "LV",
    "est": "EE",
    "irl": "IE",
    "lux": "LU",
    "cyp": "CY",
    "mlt": "MT",
    "mar": "MA",
    "tun": "TN",
    "dza": "DZ",
    "sen": "SN",
    "cmr": "CM",
    "civ": "CI",
    "mdg": "MG",
    "mli": "ML",
    "bra": "BR",
    "arg": "AR",
    "chl": "CL",
    "col": "CO",
    "mex": "MX",
    "chn": "CN",
    "jpn": "JP",
    "kor": "KR",
    "ind": "IN",
    "aus": "AU",
    "can": "CA",
    "nzl": "NZ",
    "zaf": "ZA",
    "tur": "TR",
    "rus": "RU",
    "ukr": "UA",
    # French names (accent-stripped, lower-cased)
    "france": "FR",
    "allemagne": "DE",
    "espagne": "ES",
    "italie": "IT",
    "portugal": "PT",
    "royaume-uni": "GB",
    "etats-unis": "US",
    "belgique": "BE",
    "suisse": "CH",
    "pays-bas": "NL",
    "suede": "SE",
    "norvege": "NO",
    "danemark": "DK",
    "finlande": "FI",
    "pologne": "PL",
    "republique-tcheque": "CZ",
    "autriche": "AT",
    "roumanie": "RO",
    "hongrie": "HU",
    "slovaquie": "SK",
    "slovenie": "SI",
    "croatie": "HR",
    "bulgarie": "BG",
    "grece": "GR",
    "lituanie": "LT",
    "lettonie": "LV",
    "estonie": "EE",
    "irlande": "IE",
    "luxembourg": "LU",
    "chypre": "CY",
    "malte": "MT",
    "maroc": "MA",
    "tunisie": "TN",
    "algerie": "DZ",
    "senegal": "SN",
    "cameroun": "CM",
    "cote-d-ivoire": "CI",
    "cote d'ivoire": "CI",
    "madagascar": "MG",
    "mali": "ML",
    "bresil": "BR",
    "argentine": "AR",
    "chili": "CL",
    "colombie": "CO",
    "mexique": "MX",
    "chine": "CN",
    "japon": "JP",
    "coree-du-sud": "KR",
    "inde": "IN",
    "australie": "AU",
    "canada": "CA",
    "turquie": "TR",
    "russie": "RU",
    "ukraine": "UA",
    "serbie": "RS",
    "albanie": "AL",
    # English names (lower-cased); omit names identical to French entries above
    "germany": "DE",
    "spain": "ES",
    "italy": "IT",
    "netherlands": "NL",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "poland": "PL",
    "czech republic": "CZ",
    "czechia": "CZ",
    "austria": "AT",
    "romania": "RO",
    "hungary": "HU",
    "slovakia": "SK",
    "slovenia": "SI",
    "croatia": "HR",
    "bulgaria": "BG",
    "greece": "GR",
    "lithuania": "LT",
    "latvia": "LV",
    "estonia": "EE",
    "ireland": "IE",
    "cyprus": "CY",
    "malta": "MT",
    "morocco": "MA",
    "tunisia": "TN",
    "algeria": "DZ",
    "cameroon": "CM",
    "ivory coast": "CI",
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "mexico": "MX",
    "china": "CN",
    "japan": "JP",
    "south korea": "KR",
    "india": "IN",
    "australia": "AU",
    "new zealand": "NZ",
    "south africa": "ZA",
    "turkey": "TR",
    "russia": "RU",
    "serbia": "RS",
    "albania": "AL",
}


def strip_accents(s: str) -> str:
    """Remove diacritics for accent-insensitive comparison."""
    normalized = unicodedata.normalize("NFD", s)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_string(value: str | None) -> str:
    """Strip whitespace and collapse internal spaces."""
    if not value:
        return ""
    return " ".join(value.strip().split())


def normalize_for_comparison(value: str | None) -> str:
    """Lowercase, strip accents, collapse whitespace — for fuzzy matching."""
    if not value:
        return ""
    cleaned = normalize_string(value).lower()
    return strip_accents(cleaned)


def normalize_country_code(value: str | None) -> str | None:
    """
    Resolve a country to its ISO 3166-1 alpha-2 upper-case code.

    Accepts: ISO-2, ISO-3, French name, English name (with or without accents).
    Returns None when the value cannot be resolved.
    """
    if not value:
        return None
    # Try exact ISO-2 match first (most common in Pegase/MoveOn exports)
    candidate = value.strip().lower()
    if candidate in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[candidate]
    # Try accent-stripped version (e.g. "Côte d'Ivoire" → "cote d'ivoire")
    stripped = strip_accents(candidate)
    if stripped in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[stripped]
    # Replace common separators and retry
    normalized = stripped.replace("'", "-").replace(" ", "-")
    return _COUNTRY_ALIASES.get(normalized)


def normalize_date(value: str | None) -> date | None:
    """
    Parse common date formats and return a `date`.

    Accepts: ISO 8601 (YYYY-MM-DD), DD/MM/YYYY, DD-MM-YYYY.
    Returns None when the value is empty or unparseable.
    """
    if not value:
        return None
    v = value.strip()
    # ISO 8601
    try:
        return date.fromisoformat(v)
    except ValueError:
        pass
    # DD/MM/YYYY or DD-MM-YYYY
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def normalize_ine(value: str | None) -> str:
    """Strip, uppercase, and remove internal whitespace from an INE code."""
    if not value:
        return ""
    return "".join(value.strip().upper().split())


def deduplicate_by_key(records: list[dict], *key_fields: str) -> list[dict]:
    """
    Remove exact-duplicate records based on a composite key.

    Keeps the first occurrence; silently drops subsequent identical ones.
    Used during the Transform step before any DB writes.
    """
    seen: set[tuple] = set()
    result: list[dict] = []
    for record in records:
        key = tuple(record.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            result.append(record)
    return result
