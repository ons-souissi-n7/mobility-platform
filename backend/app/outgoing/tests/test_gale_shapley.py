"""
Tests unitaires de l'algorithme Gale-Shapley.

Fonction testée : app.outgoing.services.gale_shapley.gale_shapley()
Aucune dépendance Django — tests purement Python.

Cas couverts :
  CAS1  — slot département libre → affecté directement
  CAS2  — département plein, surplus disponible (n7 > sum_quota) → slot surplus
  CAS3  — département plein ET accord plein → compétition par score
  OVF   — CAS1 overflow : étudiant dept déplace un occupant surplus
  CAS   — cascade : A évince B, B évince C
  ALT   — destination alternative pour étudiant non-affecté
  GPA0  — GPA null traité comme -inf (priorité la plus basse)
  TIE   — égalité de score → occupant conservé (statu quo)
  EXH   — étudiant épuise tous ses vœux → unassigned
"""

from app.outgoing.services.gale_shapley import (
    AgreementInput,
    AssignmentOutput,
    StudentInput,
    gale_shapley,
)

# ── helpers ──────────────────────────────────────────────────────────────────

DEPT_SN = 1
DEPT_3EA = 2
DEPT_MF2E = 3

AY_A = 101
AY_B = 102
AY_C = 103


def make_student(eid, dept, gpa, prefs, is_french=True):
    return StudentInput(
        enrollment_id=eid,
        dept_id=dept,
        is_french=is_french,
        gpa=gpa,
        preferences=prefs,
    )


def make_agr(ay_id, quota_dept, n7=None):
    if n7 is None:
        n7 = sum(quota_dept.values())
    return AgreementInput(
        agreement_year_id=ay_id,
        n7_places=n7,
        quota_dept=quota_dept,
    )


def result_map(results: list[AssignmentOutput]) -> dict[int, AssignmentOutput]:
    return {r.enrollment_id: r for r in results}


# ── CAS 1 : slot département libre ───────────────────────────────────────────


class TestCas1:
    def test_single_student_placed_in_dept(self):
        students = [make_student(1, DEPT_SN, 3.5, [AY_A])]
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].agreement_year_id == AY_A
        assert results[1].slot_type == "dept"
        assert results[1].assigned_rank == 1

    def test_two_students_fill_both_dept_slots(self):
        students = [
            make_student(1, DEPT_SN, 3.5, [AY_A]),
            make_student(2, DEPT_SN, 3.0, [AY_A]),
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 2})]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "dept"
        assert results[2].slot_type == "dept"

    def test_student_respects_wish_rank(self):
        students = [make_student(1, DEPT_SN, 3.5, [AY_A, AY_B])]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),
            make_agr(AY_B, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].agreement_year_id == AY_A  # premier choix respecté
        assert results[1].assigned_rank == 1


# ── CAS 2 : slot surplus disponible ──────────────────────────────────────────


class TestCas2:
    def test_student_placed_in_surplus_when_dept_full(self):
        """
        Accord : SN=1, n7=2 → 1 surplus.
        Étudiant SN prend le slot dept.
        Étudiant 3EA (no quota 3EA) prend le surplus.
        """
        students = [
            make_student(1, DEPT_SN, 3.5, [AY_A]),
            make_student(2, DEPT_3EA, 3.0, [AY_A]),
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1}, n7=2)]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "dept"
        assert results[2].slot_type == "surplus"
        assert results[2].agreement_year_id == AY_A

    def test_surplus_fills_in_order(self):
        """
        Accord : SN=1, n7=3 → 2 surplus.
        1 SN (dept) + 2 étudiants sans quota (surplus).
        """
        students = [
            make_student(1, DEPT_SN, 3.5, [AY_A]),
            make_student(2, DEPT_3EA, 3.0, [AY_A]),
            make_student(3, DEPT_MF2E, 2.5, [AY_A]),
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1}, n7=3)]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "dept"
        assert results[2].slot_type == "surplus"
        assert results[3].slot_type == "surplus"


# ── CAS 3 : compétition par score ─────────────────────────────────────────────


class TestCas3:
    def test_higher_gpa_wins_over_lower(self):
        """
        Accord plein (SN=1). Meilleur GPA évince le moins bon.
        """
        students = [
            make_student(1, DEPT_SN, 2.0, [AY_A]),  # faible GPA, premier dans la queue
            make_student(2, DEPT_SN, 3.8, [AY_A]),  # fort GPA
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        assigned = [r for r in results.values() if r.slot_type == "dept"]
        unassigned = [r for r in results.values() if r.slot_type == "unassigned"]
        assert assigned[0].enrollment_id == 2  # fort GPA garde sa place
        assert unassigned[0].enrollment_id == 1  # faible GPA éliminé

    def test_french_beats_international_regardless_of_gpa(self):
        """
        Tier 1 (français) prime sur tier 0 (étranger) même avec GPA inférieur.
        """
        students = [
            make_student(
                10, DEPT_SN, 3.9, [AY_A], is_french=False
            ),  # étranger fort GPA
            make_student(
                11, DEPT_SN, 2.5, [AY_A], is_french=True
            ),  # français faible GPA
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        assert results[11].slot_type == "dept"  # français placé
        assert results[10].slot_type == "unassigned"

    def test_rejected_student_tries_next_wish(self):
        """
        Étudiant rejeté de AY_A (meilleur déjà là) tente AY_B.
        """
        students = [
            make_student(1, DEPT_SN, 3.5, [AY_A]),  # occupe AY_A
            make_student(2, DEPT_SN, 2.0, [AY_A, AY_B]),  # évincé de AY_A → essaie AY_B
        ]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),
            make_agr(AY_B, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].agreement_year_id == AY_A
        assert results[2].agreement_year_id == AY_B


# ── CAS1 overflow : étudiant dept évince un surplus ──────────────────────────


class TestCas1Overflow:
    def test_dept_student_evicts_surplus_occupant(self):
        """
        Accord SN=2, n7=2.
        Étudiant MF2E (sans quota) prend le surplus tant que total < n7.
        Puis le 2e étudiant SN arrive (CAS1) → total dépasserait n7 → évince le MF2E.

        Séquence garantie : MF2E en tête de queue → proposent en premier.
        """
        students = [
            make_student(99, DEPT_MF2E, 3.9, [AY_A]),  # MF2E, pas de quota → surplus
            make_student(1, DEPT_SN, 3.5, [AY_A]),  # SN_1 → dept
            make_student(2, DEPT_SN, 3.0, [AY_A]),  # SN_2 → dept, déborde → évince MF2E
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 2})]  # n7=2, surplus=0

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "dept"
        assert results[2].slot_type == "dept"
        assert results[99].slot_type == "unassigned"  # MF2E évincé, plus de vœu dispo


# ── Cascade d'évictions ───────────────────────────────────────────────────────


class TestCascade:
    def test_two_level_cascade(self):
        """
        A(3.8) évince B(3.0) de AY_B.
        B évince ensuite C(2.0) de AY_C.
        C est finalement non-affecté.

        Préférences :
          A  = [AY_A, AY_B]    → rejeté de AY_A (plein + meilleur score), gagne AY_B
          B  = [AY_B, AY_C]    → évincé de AY_B par A, gagne AY_C en évincant C
          C  = [AY_C, AY_A]    → évincé de AY_C par B, rejeté de AY_A → unassigned
          D  = [AY_A]           → occupe AY_A (meilleur score que A)
        """
        students = [
            make_student(10, DEPT_SN, 4.0, [AY_A]),  # D : occupe AY_A
            make_student(1, DEPT_SN, 3.8, [AY_A, AY_B]),  # A
            make_student(2, DEPT_SN, 3.0, [AY_B, AY_C]),  # B
            make_student(3, DEPT_SN, 2.0, [AY_C, AY_A]),  # C
        ]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),
            make_agr(AY_B, {DEPT_SN: 1}),
            make_agr(AY_C, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[10].agreement_year_id == AY_A  # D reste en AY_A
        assert results[1].agreement_year_id == AY_B  # A placé en AY_B
        assert results[2].agreement_year_id == AY_C  # B placé en AY_C
        assert results[3].slot_type == "unassigned"  # C évincé partout


# ── Destination alternative ───────────────────────────────────────────────────


class TestAlternativeDestination:
    def test_unmatched_student_gets_alternative_slot(self):
        """
        AY_A (SN=1) a 1 place restante après la boucle principale
        (aucun étudiant ne l'a souhaité).
        Étudiant SN non-affecté → destination alternative dans AY_A.
        """
        students = [
            make_student(
                1, DEPT_SN, 3.0, [AY_B]
            ),  # préfère AY_B, rejeté (meilleur déjà là)
            make_student(2, DEPT_SN, 3.5, [AY_B]),  # occupe AY_B
        ]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),  # personne ne le souhaite → place libre
            make_agr(AY_B, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[2].slot_type == "dept"
        assert results[1].slot_type == "alternative"
        assert results[1].agreement_year_id == AY_A

    def test_alternative_respects_dept_constraint(self):
        """
        Étudiant MF2E non-affecté.
        AY_A a des places mais quota uniquement pour SN → MF2E ne peut pas y aller.
        → unassigned.
        """
        students = [make_student(1, DEPT_MF2E, 3.0, [AY_B])]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 2}),  # place libre, mais pour SN uniquement
            make_agr(AY_B, {DEPT_MF2E: 0}),  # pas de quota MF2E non plus
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "unassigned"


# ── GPA null ──────────────────────────────────────────────────────────────────


class TestGpaNull:
    def test_null_gpa_has_lowest_priority(self):
        """
        Étudiant avec gpa=None perd contre tout étudiant avec une vraie GPA.
        """
        students = [
            make_student(1, DEPT_SN, None, [AY_A]),  # GPA null → -inf
            make_student(2, DEPT_SN, 0.1, [AY_A]),  # GPA très faible mais réelle
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        assert results[2].slot_type == "dept"
        assert results[1].slot_type == "unassigned"

    def test_two_null_gpa_tie(self):
        """
        Deux étudiants avec gpa=None : le premier proposant reste (pas d'éviction).
        """
        students = [
            make_student(1, DEPT_SN, None, [AY_A]),
            make_student(2, DEPT_SN, None, [AY_A]),
        ]
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        placed = [r for r in results.values() if r.slot_type == "dept"]
        assert len(placed) == 1  # un seul placé


# ── Égalité de score ──────────────────────────────────────────────────────────


class TestTie:
    def test_tie_preserves_current_occupant(self):
        """
        Scores identiques → l'occupant actuel conserve sa place (pas d'éviction).
        """
        students = [
            make_student(1, DEPT_SN, 3.5, [AY_A]),  # occupe AY_A en premier
            make_student(2, DEPT_SN, 3.5, [AY_A, AY_B]),  # même score → essaie AY_B
        ]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),
            make_agr(AY_B, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].agreement_year_id == AY_A
        assert results[2].agreement_year_id == AY_B


# ── Épuisement des vœux ───────────────────────────────────────────────────────


class TestExhausted:
    def test_student_with_no_matching_wish_is_unassigned(self):
        students = [make_student(1, DEPT_SN, 3.5, [])]  # aucun vœu
        agreements = [make_agr(AY_A, {DEPT_SN: 1})]

        results = result_map(gale_shapley(students, agreements))

        assert results[1].slot_type == "unassigned"
        assert results[1].agreement_year_id is None

    def test_student_rejected_everywhere_is_unassigned(self):
        students = [
            make_student(1, DEPT_SN, 3.9, [AY_A]),  # occupe AY_A
            make_student(2, DEPT_SN, 2.0, [AY_A, AY_B]),  # perd AY_A, perd AY_B
            make_student(3, DEPT_SN, 3.5, [AY_B]),  # occupe AY_B
        ]
        agreements = [
            make_agr(AY_A, {DEPT_SN: 1}),
            make_agr(AY_B, {DEPT_SN: 1}),
        ]

        results = result_map(gale_shapley(students, agreements))

        assert results[2].slot_type == "unassigned"

    def test_empty_inputs(self):
        results = gale_shapley([], [])
        assert results == []
