"""
Algorithme de Gale-Shapley (student-optimal) avec double niveau de quotas.

Entrées pures Python — aucune dépendance Django.

Capacités :
  - n7_places      : plafond dur global par accord
  - quota_dept     : planchers souples par département (réservations)

Priorité d'affectation (score décroissant) :
  - tier = 1 si nationalité française, 0 sinon
  - gpa  = valeur numérique, -inf si null

Sécurité des slots :
  - slot département  : protégé — tout étudiant du même département
                        réclamant sa réservation prend priorité sur le surplus
  - slot surplus      : provisoire — peut être évincé par un étudiant
                        dont le département a encore des places réservées libres
"""

from collections import deque
from dataclasses import dataclass, field


@dataclass
class StudentInput:
    enrollment_id: int
    dept_id: int
    is_french: bool
    gpa: float | None
    preferences: list[int]  # agreement_year_ids ordonnés par rang croissant
    level_id: int | None = None  # None = compatible avec tous les niveaux


@dataclass
class AgreementInput:
    agreement_year_id: int
    n7_places: int
    quota_dept: dict[int, int]  # dept_id → nb_places réservées
    level_ids: list[int] = field(default_factory=list)  # vide = tous niveaux acceptés


@dataclass
class AssignmentOutput:
    enrollment_id: int
    agreement_year_id: int | None  # None = non affecté
    assigned_rank: int | None  # rang du vœu retenu (1-based), None si non affecté
    slot_type: str  # 'dept' | 'surplus' | 'alternative' | 'unassigned'


# ─────────────────────────────────────────────────────────────
# État interne d'un accord pendant l'algorithme
# ─────────────────────────────────────────────────────────────


@dataclass
class _AgreementState:
    agreement: AgreementInput
    slots_dept: dict[int, list[int]] = field(default_factory=dict)
    slots_surplus: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.slots_dept = {dept_id: [] for dept_id in self.agreement.quota_dept}

    def total_occupied(self) -> int:
        return sum(len(v) for v in self.slots_dept.values()) + len(self.slots_surplus)

    def all_occupants(self) -> list[int]:
        result: list[int] = []
        for lst in self.slots_dept.values():
            result.extend(lst)
        result.extend(self.slots_surplus)
        return result

    def remove_occupant(self, eid: int) -> None:
        if eid in self.slots_surplus:
            self.slots_surplus.remove(eid)
            return
        for lst in self.slots_dept.values():
            if eid in lst:
                lst.remove(eid)
                return


# ─────────────────────────────────────────────────────────────
# Fonction de score (tri décroissant = meilleur en premier)
# ─────────────────────────────────────────────────────────────


def _score(student: StudentInput) -> tuple[int, float]:
    tier = 1 if student.is_french else 0
    gpa = student.gpa if student.gpa is not None else float("-inf")
    return (tier, gpa)


def _worst_in(eids: list[int], student_map: dict[int, StudentInput]) -> int | None:
    if not eids:
        return None
    return min(eids, key=lambda e: _score(student_map[e]))


# ─────────────────────────────────────────────────────────────
# Traitement d'une proposition (retourne l'évincé ou None)
# ─────────────────────────────────────────────────────────────


def _process_proposal(
    state: _AgreementState,
    student: StudentInput,
    student_map: dict[int, StudentInput],
) -> tuple[bool, int | None]:
    """
    Tente d'accepter `student` dans l'accord.

    Retourne :
      (True,  evicted_id)  — accepté, quelqu'un a été évincé
      (True,  None)        — accepté, personne évincé
      (False, None)        — rejeté (CAS 3, score insuffisant)
    """
    dept_id = student.dept_id
    dept_slots = state.slots_dept.get(dept_id, [])
    dept_quota = state.agreement.quota_dept.get(dept_id, 0)
    dept_used = len(dept_slots)
    total = state.total_occupied()
    n7 = state.agreement.n7_places

    # ── CAS 1 : département a un slot réservé disponible ──────────────────
    if dept_used < dept_quota:
        state.slots_dept.setdefault(dept_id, []).append(student.enrollment_id)

        if state.total_occupied() > n7:
            # Éviction obligatoire — surplus en priorité (slot provisoire)
            if state.slots_surplus:
                worst = _worst_in(state.slots_surplus, student_map)
                state.slots_surplus.remove(worst)
                return True, worst
            else:
                # Surplus vide → évince le pire hors l'étudiant qu'on vient d'ajouter
                others = [
                    e for e in state.all_occupants() if e != student.enrollment_id
                ]
                worst = _worst_in(others, student_map)
                state.remove_occupant(worst)
                return True, worst

        return True, None

    # ── CAS 2 : département plein, place en surplus disponible ────────────
    if total < n7:
        state.slots_surplus.append(student.enrollment_id)
        return True, None

    # ── CAS 3 : département plein ET accord plein — compétition par score ─
    worst = _worst_in(state.all_occupants(), student_map)
    if worst is not None and _score(student) > _score(student_map[worst]):
        state.remove_occupant(worst)
        # Après éviction, le slot dept du nouvel étudiant peut être libéré
        new_dept_used = len(state.slots_dept.get(dept_id, []))
        if new_dept_used < dept_quota:
            state.slots_dept.setdefault(dept_id, []).append(student.enrollment_id)
        else:
            state.slots_surplus.append(student.enrollment_id)
        return True, worst

    return False, None


# ─────────────────────────────────────────────────────────────
# Algorithme principal
# ─────────────────────────────────────────────────────────────


def gale_shapley(
    students: list[StudentInput],
    agreements: list[AgreementInput],
) -> list[AssignmentOutput]:
    """
    Lance l'algorithme de Gale-Shapley et retourne la liste des affectations.

    Après la boucle principale, les étudiants sans affectation tentent d'être
    placés en destination alternative (accord avec places restantes compatible
    avec leur département), puis marqués 'unassigned' si impossible.
    """
    student_map: dict[int, StudentInput] = {s.enrollment_id: s for s in students}
    agreement_map: dict[int, _AgreementState] = {
        a.agreement_year_id: _AgreementState(a) for a in agreements
    }

    next_proposal: dict[int, int] = {s.enrollment_id: 0 for s in students}
    queue: deque[int] = deque(s.enrollment_id for s in students)
    unmatched: list[int] = []

    # ── Boucle principale ─────────────────────────────────────────────────
    while queue:
        eid = queue.popleft()
        student = student_map[eid]

        if next_proposal[eid] >= len(student.preferences):
            unmatched.append(eid)
            continue

        ay_id = student.preferences[next_proposal[eid]]
        next_proposal[eid] += 1

        if ay_id not in agreement_map:
            # Accord inconnu → passer au vœu suivant
            queue.appendleft(eid)
            continue

        state = agreement_map[ay_id]
        accepted, evicted = _process_proposal(state, student, student_map)

        if not accepted:
            # Rejeté → reprend le vœu suivant
            queue.append(eid)

        if evicted is not None:
            # Évincé → reprend le vœu suivant (cascade)
            queue.append(evicted)

    # ── Construction du résultat depuis l'état final ──────────────────────
    results: list[AssignmentOutput] = []
    assigned_eids: set[int] = set()

    for ay_id, state in agreement_map.items():
        for _dept_id, eids in state.slots_dept.items():
            for eid in eids:
                s = student_map[eid]
                rank = (
                    s.preferences.index(ay_id) + 1 if ay_id in s.preferences else None
                )
                results.append(
                    AssignmentOutput(
                        enrollment_id=eid,
                        agreement_year_id=ay_id,
                        assigned_rank=rank,
                        slot_type="dept",
                    )
                )
                assigned_eids.add(eid)

        for eid in state.slots_surplus:
            s = student_map[eid]
            rank = s.preferences.index(ay_id) + 1 if ay_id in s.preferences else None
            results.append(
                AssignmentOutput(
                    enrollment_id=eid,
                    agreement_year_id=ay_id,
                    assigned_rank=rank,
                    slot_type="surplus",
                )
            )
            assigned_eids.add(eid)

    # ── Phase destination alternative ─────────────────────────────────────
    # Accords avec des places encore disponibles (total < n7_places)
    agreements_with_space = [
        state
        for state in agreement_map.values()
        if state.total_occupied() < state.agreement.n7_places
    ]

    # Trier les non-affectés par score décroissant (meilleurs en priorité)
    unmatched.sort(key=lambda e: _score(student_map[e]), reverse=True)

    for eid in unmatched:
        student = student_map[eid]

        # Pas de vœux exprimés → aucune destination alternative
        if not student.preferences:
            results.append(
                AssignmentOutput(
                    enrollment_id=eid,
                    agreement_year_id=None,
                    assigned_rank=None,
                    slot_type="unassigned",
                )
            )
            continue

        placed = False

        for state in agreements_with_space:
            dept_quota = state.agreement.quota_dept.get(student.dept_id, 0)
            if dept_quota == 0:
                # Accord non prévu pour ce département
                continue
            # Contrainte de niveau : si l'accord restreint les niveaux, vérifier la compatibilité
            if (
                state.agreement.level_ids
                and student.level_id is not None
                and student.level_id not in state.agreement.level_ids
            ):
                continue
            if state.total_occupied() < state.agreement.n7_places:
                state.slots_surplus.append(eid)
                ay_id = state.agreement.agreement_year_id
                results.append(
                    AssignmentOutput(
                        enrollment_id=eid,
                        agreement_year_id=ay_id,
                        assigned_rank=None,
                        slot_type="alternative",
                    )
                )
                assigned_eids.add(eid)
                placed = True
                break

        if not placed:
            results.append(
                AssignmentOutput(
                    enrollment_id=eid,
                    agreement_year_id=None,
                    assigned_rank=None,
                    slot_type="unassigned",
                )
            )

    return results
