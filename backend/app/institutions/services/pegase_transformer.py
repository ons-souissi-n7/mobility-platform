from dataclasses import dataclass
from typing import Any

from app.shared.cleaning import normalize_string


@dataclass(frozen=True)
class TransformedDepartment:
    pegase_id: str
    code: str
    name: str


def transform_department(payload: dict[str, Any]) -> TransformedDepartment:
    pegase_id = normalize_string(str(payload.get("pegase_id") or ""))
    if not pegase_id:
        raise ValueError("pegase_id is required")

    return TransformedDepartment(
        pegase_id=pegase_id,
        code=normalize_string(str(payload.get("code") or "")).upper(),
        name=normalize_string(str(payload.get("name") or "")),
    )
