"""
Ajoute, dans les 3 API factices (fake-pegase-api, fake-moveon-api,
fake-eudonet-api), les données nécessaires pour dérouler le cycle de vie
complet d'une année universitaire via de VRAIES synchronisations déclenchées
depuis l'admin (pas en remplissant la base directement) :

  Pégase   : étudiants + GPA (inscriptions.json)
  MoveOn   : accords (agreements.json + agreement_quotas.json), vœux
             étudiants (student_wishes.json)
  Eudonet  : stages internationaux (internships.json)

Additif : n'écrase jamais une ligne existante. Deux exceptions ciblées et
documentées : les accords REL-001..REL-004 de agreements.json (et leur
quota associé) sont corrigés sur place — ils utilisaient la mauvaise clé
d'identifiant (`moveon_relation_id` au lieu de `moveon_id` réellement lu
par le transformer réel) et n'avaient pas `inp_institutions`/
`department_codes`/`levels`, ce qui les aurait fait échouer silencieusement
à la synchronisation. REL-005 (cas de résolution manuelle volontairement
cassé) n'est pas touché.

Usage : python generate_fake_api_year.py 2026-2027
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEPARTMENTS = ["SN", "3EA", "MF2E"]
PARCOURS_BY_DEPT = {"SN": ["IA", "SESG", "ROB"], "3EA": ["EEA", "RT", "SC"], "MF2E": ["EE", "THD"]}
LEVEL_CYCLE = ["2ING", "3ING", "2ING", "3ING", "1M", "2M"]
NATIONALITY_CYCLE = ["FR", "ES", "DE", "IT", "MA", "CM", "EG", "CH", "GB", "PT", "PL", "SE", "DK", "NO", "CA", "JP"]

FIRST_NAMES = [
    "Louis", "Emma", "Gabriel", "Jade", "Raphael", "Alice", "Arthur", "Rose",
    "Jules", "Anna", "Adam", "Louise", "Sacha", "Zoe", "Noe", "Mila",
    "Eden", "Lina",
]
LAST_NAMES = [
    "PETIT", "ROBIN", "MOULIN", "FAURE", "ANDRE", "MERCIER", "BLANC", "GUERIN",
    "MULLER", "HENRY", "ROBERT", "DUVAL", "JOLY", "GAY", "ROLLAND", "CLEMENT",
    "MOREL", "PAYET",
]


def load(path: Path) -> list:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, data: list) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  {path.relative_to(ROOT)}: {len(data)} lignes")


def build_students(year_label: str, start_year: int, n_per_dept: int) -> list:
    students = []
    seq = 0
    for dept_idx, dept in enumerate(DEPARTMENTS, start=1):
        for i in range(n_per_dept):
            seq += 1
            ine = f"{start_year}{dept_idx:02d}{seq:05d}"
            first = FIRST_NAMES[(seq - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[(seq - 1) % len(LAST_NAMES)]
            level = LEVEL_CYCLE[i % len(LEVEL_CYCLE)]
            parcours = PARCOURS_BY_DEPT[dept][i % len(PARCOURS_BY_DEPT[dept])]
            gpa = round(10.5 + ((seq * 37) % 75) / 10, 2)  # étalé sur 10.5-18.0
            nat = NATIONALITY_CYCLE[seq % len(NATIONALITY_CYCLE)]
            students.append(
                {
                    "ine": ine,
                    "nom": last,
                    "prenom": first,
                    "email": f"{first.lower()}.{last.lower()}.{ine}@etu.inp-toulouse.fr",
                    "sexe": "F" if seq % 2 == 0 else "M",
                    "departement": dept,
                    "niveau": level,
                    "parcours": parcours,
                    "moyenne": gpa,
                    "nationalite": nat,
                    "date_creation": f"{start_year}-09-{(seq % 20) + 1:02d}",
                    "date_modification": f"{start_year}-11-{(seq % 25) + 1:02d}",
                }
            )
    return students


def fix_and_extend_agreements(agreements: list, year_label: str, start_year: int) -> list:
    fix_spec = {
        "REL-001": (["SN", "3EA"], ["2ING", "3ING"]),
        "REL-002": (["3EA", "MF2E"], ["2ING", "3ING"]),
        "REL-003": (["SN"], ["1M", "2M"]),
        "REL-004": (["SN", "3EA", "MF2E"], ["2ING", "3ING", "1M", "2M"]),
    }

    for ag in agreements:
        rel_id = ag.get("moveon_relation_id")
        if rel_id in fix_spec:
            dept_codes, levels = fix_spec[rel_id]
            ag["moveon_id"] = ag.pop("moveon_relation_id")
            ag["inp_institutions"] = "ENSEEIHT"
            ag.setdefault("department_codes", dept_codes)
            ag.setdefault("levels", levels)

    existing_ids = {a.get("moveon_id") or a.get("moveon_relation_id") for a in agreements}
    new_agreements = [
        {
            "moveon_id": "REL-006",
            "reference": "REF-006",
            "name": f"Erasmus+ KTH Stockholm {year_label}",
            "partner_university_moveon_id": 2004,
            "relation_type": "Erasmus",
            "framework": "Erasmus Enseignement",
            "direction": "outgoing",
            "status": "active",
            "is_active": True,
            "start_date": f"{start_year}-09-01",
            "end_date": f"{start_year + 1}-08-31",
            "start_academic_year": year_label,
            "end_academic_year": f"{start_year + 1}-{start_year + 2}",
            "discipline": "Engineering",
            "isced": "071",
            "level": "Master",
            "formation": "SN",
            "inp_institutions": "ENSEEIHT",
            "department_codes": ["SN", "3EA"],
            "levels": ["2ING", "3ING"],
            "created_at": f"{start_year}-09-01",
            "updated_at": f"{start_year}-09-01",
        },
        {
            "moveon_id": "REL-007",
            "reference": "REF-007",
            "name": f"Convention PUC Chile {year_label}",
            "partner_university_moveon_id": 2005,
            "relation_type": "Exchange",
            "framework": "Erasmus Enseignement",
            "direction": "outgoing",
            "status": "active",
            "is_active": True,
            "start_date": f"{start_year}-09-01",
            "end_date": f"{start_year + 1}-08-31",
            "start_academic_year": year_label,
            "end_academic_year": f"{start_year + 1}-{start_year + 2}",
            "discipline": "Engineering",
            "isced": "071",
            "level": "Master",
            "formation": "MF2E",
            "inp_institutions": "ENSEEIHT",
            "department_codes": ["MF2E"],
            "levels": ["2ING", "3ING"],
            "created_at": f"{start_year}-09-01",
            "updated_at": f"{start_year}-09-01",
        },
        {
            "moveon_id": "REL-008",
            "reference": "REF-008",
            "name": f"University of Trento {year_label}",
            "partner_university_moveon_id": 1359,
            "relation_type": "Erasmus",
            "framework": "Erasmus Enseignement",
            "direction": "outgoing",
            "status": "active",
            "is_active": True,
            "start_date": f"{start_year}-09-01",
            "end_date": f"{start_year + 1}-08-31",
            "start_academic_year": year_label,
            "end_academic_year": f"{start_year + 1}-{start_year + 2}",
            "discipline": "Engineering",
            "isced": "071",
            "level": "Ingenieur",
            "formation": "3EA",
            "inp_institutions": "ENSEEIHT",
            "department_codes": ["3EA"],
            "levels": ["1M", "2ING", "3ING"],
            "created_at": f"{start_year}-09-01",
            "updated_at": f"{start_year}-09-01",
        },
        {
            "moveon_id": "REL-009",
            "reference": "REF-009",
            "name": f"University of Klagenfurt {year_label}",
            "partner_university_moveon_id": 1349,
            "relation_type": "Erasmus",
            "framework": "Erasmus Enseignement",
            "direction": "outgoing",
            "status": "active",
            "is_active": True,
            "start_date": f"{start_year}-09-01",
            "end_date": f"{start_year + 1}-08-31",
            "start_academic_year": year_label,
            "end_academic_year": f"{start_year + 1}-{start_year + 2}",
            "discipline": "Engineering",
            "isced": "071",
            "level": "Master",
            "formation": "SN",
            "inp_institutions": "ENSEEIHT",
            "department_codes": ["SN", "MF2E"],
            "levels": ["2ING", "3ING", "2M"],
            "created_at": f"{start_year}-09-01",
            "updated_at": f"{start_year}-09-01",
        },
    ]
    for na in new_agreements:
        if na["moveon_id"] not in existing_ids:
            agreements.append(na)
    return agreements


def fix_and_extend_quotas(quotas: list, year_label: str) -> list:
    for q in quotas:
        if q.get("moveon_relation_id") == "REL-001":
            q["moveon_id"] = q.pop("moveon_relation_id")

    existing_ids = {q.get("moveon_id") or q.get("moveon_relation_id") for q in quotas}
    new_quotas = [
        {"moveon_id": "REL-002", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-002", "total_places": 3, "remaining_places": 3, "total_duration": 12, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-003", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-003", "total_places": 2, "remaining_places": 2, "total_duration": 6, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-004", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-004", "total_places": 2, "remaining_places": 2, "total_duration": 24, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-006", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-006", "total_places": 3, "remaining_places": 3, "total_duration": 12, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-007", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-007", "total_places": 2, "remaining_places": 2, "total_duration": 12, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-008", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-008", "total_places": 4, "remaining_places": 4, "total_duration": 12, "duration_unit": "months", "is_effective": True},
        {"moveon_id": "REL-009", "academic_year_label": year_label, "period": "S1", "places_id": "PLC-009", "total_places": 2, "remaining_places": 2, "total_duration": 12, "duration_unit": "months", "is_effective": True},
    ]
    for nq in new_quotas:
        if nq["moveon_id"] not in existing_ids:
            quotas.append(nq)
    return quotas


def build_wishes(students: list, start_year: int) -> list:
    offer_ids = ["REL-001", "REL-002", "REL-003", "REL-004", "REL-006", "REL-007", "REL-008", "REL-009"]
    offer_names = {
        "REL-001": "Erasmus outgoing agreement",
        "REL-002": "Exchange incoming agreement",
        "REL-003": "Industry internship agreement",
        "REL-004": "Joint double degree",
        "REL-006": f"Erasmus+ KTH Stockholm {start_year}-{start_year + 1}",
        "REL-007": f"Convention PUC Chile {start_year}-{start_year + 1}",
        "REL-008": f"University of Trento {start_year}-{start_year + 1}",
        "REL-009": f"University of Klagenfurt {start_year}-{start_year + 1}",
    }
    wishes = []
    no = 1
    for idx, s in enumerate(students):
        n_wishes = 1 + (idx % 3)
        chosen = [offer_ids[(idx + k) % len(offer_ids)] for k in range(n_wishes)]
        # dédoublonne tout en gardant l'ordre (rang de vœu)
        seen = []
        for c in chosen:
            if c not in seen:
                seen.append(c)
        for rank, offer_id in enumerate(seen, start=1):
            wishes.append(
                {
                    "Individu": f"{s['nom']} {s['prenom']}",
                    "Numéro étudiant": s["ine"],
                    "No": rank,
                    "Offre de séjour": offer_names[offer_id],
                    "Offre de séjour ID": offer_id,
                    "Statut Sélection": "Candidat",
                    "Crée le": f"{(idx % 28) + 1:02d}/10/{start_year} 09:{(idx % 59):02d}",
                    "Dernière modification le": f"{(idx % 28) + 1:02d}/11/{start_year} 09:{(idx % 59):02d}",
                }
            )
            no += 1
    return wishes


def _ddmmyyyy(iso_date: str) -> str:
    y, m, d = iso_date.split("-")
    return f"{d}/{m}/{y}"


def build_internships(students: list, start_year: int) -> list:
    companies = [
        ("Airbus", "Toulouse", "FR"), ("Siemens", "Munich", "DE"), ("ABB", "Zurich", "CH"),
        ("Ericsson", "Stockholm", "SE"), ("Philips", "Amsterdam", "NL"),
    ]
    internships = []
    for i, s in enumerate(students[:6]):
        company, city, iso2 = companies[i % len(companies)]
        start = f"{start_year + 1}-03-01"
        end = f"{start_year + 1}-08-31"
        internships.append(
            {
                "N°INE": s["ine"],
                "Libellé": f"Stage_{start_year + 1}",
                "Raison sociale": company,
                "Pays": city,
                "Ville": city,
                "Type": "Stage 3A",
                "Statut": "9 Justificatif de fin de stage retourné",
                "Date de début": _ddmmyyyy(start),
                "Date de fin": _ddmmyyyy(end),
                "Nb semaines dans l'entreprise": "24",
                "Tuteur pédagogique Ecole": "Pr. Demo",
                "Tuteur technique entreprise": "M. Demo",
                "Titre": f"Ingenieur {s['departement']}",
                "Mobilité à l'international": "Oui",
                "Composante": "ENSEEIHT",
                "Modifié le": f"01/09/{start_year} 10:00",
            }
        )
    return internships


def main() -> None:
    if len(sys.argv) != 2 or "-" not in sys.argv[1]:
        print("Usage : python generate_fake_api_year.py 2026-2027")
        sys.exit(1)
    year_label = sys.argv[1]
    start_year = int(year_label.split("-")[0])

    pegase_dir = ROOT / "fake-pegase-api" / "data"
    moveon_dir = ROOT / "fake-moveon-api" / "data"
    eudonet_dir = ROOT / "fake-eudonet-api" / "data"

    # ── Pégase : étudiants + GPA ──────────────────────────────────────────
    inscriptions = load(pegase_dir / "inscriptions.json")
    new_students = build_students(year_label, start_year, n_per_dept=6)
    existing_ines = {r["ine"] for r in inscriptions}
    new_students = [s for s in new_students if s["ine"] not in existing_ines]
    inscriptions.extend(new_students)
    save(pegase_dir / "inscriptions.json", inscriptions)

    # ── MoveOn : accords + quotas ─────────────────────────────────────────
    agreements = load(moveon_dir / "agreements.json")
    agreements = fix_and_extend_agreements(agreements, year_label, start_year)
    save(moveon_dir / "agreements.json", agreements)

    quotas = load(moveon_dir / "agreement_quotas.json")
    quotas = fix_and_extend_quotas(quotas, year_label)
    save(moveon_dir / "agreement_quotas.json", quotas)

    # ── MoveOn : vœux étudiants ────────────────────────────────────────────
    wishes = load(moveon_dir / "student_wishes.json")
    wishes.extend(build_wishes(new_students, start_year))
    save(moveon_dir / "student_wishes.json", wishes)

    # ── Eudonet : stages ────────────────────────────────────────────────────
    internships = load(eudonet_dir / "internships.json")
    internships.extend(build_internships(new_students, start_year))
    save(eudonet_dir / "internships.json", internships)

    print(f"\nOK - donnees factices pretes pour {year_label} ({len(new_students)} nouveaux etudiants).")


if __name__ == "__main__":
    main()
