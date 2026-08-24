"""
Ajoute un lot supplémentaire d'étudiants, de vœux et d'affectations à des
années historiques déjà existantes, sans toucher à ce qui y est déjà —
contrairement à `reset_historical_years`, qui vide tout avant de reconstruire.

Le nouveau lot est traité comme une affectation Gale-Shapley indépendante :
il ne recalcule jamais les résultats déjà en base, il complète simplement la
capacité restante des accords (places totales et quotas par département moins
ce qui est déjà occupé par les affectations précédentes de l'année). Une
deuxième ligne `Assignment` est créée pour ce lot, comme c'était déjà le cas
sur cette instance avant notre intervention (années 2022-2023 à 2024-2025,
qui portent chacune deux lots d'affectation antérieurs).

`random` sert uniquement à générer des étudiants/vœux de démonstration
plausibles. Sans objet pour les hotspots Sonar "pseudorandom number
generator" (S2245) ci-dessous.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.academic.management.commands._demo_students import (
    NATIONALITY_POOL,
    create_demo_students,
    create_demo_wishes,
)


class Command(BaseCommand):
    help = (
        "Ajoute un lot supplémentaire d'étudiants/vœux/affectations à des "
        "années historiques déjà existantes, en respectant la capacité "
        "restante des accords — n'efface et ne recalcule jamais les "
        "affectations déjà en base."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--labels",
            nargs="+",
            required=True,
            help="Libellés des années à compléter (doivent déjà exister en base).",
        )
        parser.add_argument(
            "--students-per-dept",
            type=int,
            default=35,
            help="Nombre d'étudiants supplémentaires par département (défaut: 35).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=142,
            help="Graine aléatoire (défaut: 142, différente de reset_historical_years "
            "pour éviter de régénérer exactement les mêmes profils).",
        )

    def handle(self, *args, **options):
        from app.academic.models import AcademicYear

        n_per_dept = options["students_per_dept"]
        random.seed(options["seed"])  # NOSONAR (S2245) — donnée de démo

        depts, levels_by_code, parcours_by_dept, countries = self._load_reference_data()

        for label in options["labels"]:
            year = AcademicYear.objects.filter(label=label).first()
            if year is None:
                self.stderr.write(
                    self.style.ERROR(f"Année {label} introuvable — ignorée.")
                )
                continue
            with transaction.atomic():
                self._topup_year(
                    year, n_per_dept, depts, levels_by_code, parcours_by_dept, countries
                )

        self.stdout.write(self.style.SUCCESS("\n✓ Complément d'historique terminé."))

    # ────────────────────────────────────────────────────────────────────────

    def _load_reference_data(self):
        from app.reference.models import Country, Department, Level, Parcours

        depts = list(Department.objects.all())
        levels_by_code = {lv.code: lv for lv in Level.objects.all()}
        parcours_by_dept: dict[str, list] = {}
        for p in Parcours.objects.select_related("department").all():
            parcours_by_dept.setdefault(p.department.code, []).append(p)
        countries = {
            c.iso2: c for c in Country.objects.filter(iso2__in=set(NATIONALITY_POOL))
        }
        return depts, levels_by_code, parcours_by_dept, countries

    def _widen_agreement_catalog(self, year):
        """Crée un AgreementYear (+ quotas département) pour tout Agreement qui
        n'est pas encore rattaché à cette année — additif, ne touche jamais un
        AgreementYear déjà existant. Sans ça, les accords ajoutés après coup
        (cf. enrich_partner_network) restent invisibles pour les années déjà
        closes, qui ne portaient que l'ancien catalogue réduit."""
        from app.mobility.models import (
            Agreement,
            AgreementDepartment,
            AgreementYear,
            AgreementYearDepartment,
        )

        existing_agreement_ids = set(
            AgreementYear.objects.filter(academic_year=year).values_list(
                "agreement_id", flat=True
            )
        )
        candidate_agreements = Agreement.objects.exclude(
            id__in=existing_agreement_ids
        ).prefetch_related("levels")
        # is_valid_for_year() écarte les accords hors de leur fenêtre
        # valid_from/valid_until — sans ce filtre, un accord signé en 2024
        # pourrait être rattaché à une campagne 2020-2021, avec des étudiants
        # affectés à un partenariat qui n'existait pas encore à l'époque.
        new_agreements = [
            agreement
            for agreement in candidate_agreements
            if agreement.is_valid_for_year(year)
        ]
        if not new_agreements:
            return 0

        agreement_depts_by_agreement: dict[int, list] = {}
        for ad in AgreementDepartment.objects.filter(
            agreement__in=new_agreements
        ).select_related("department"):
            agreement_depts_by_agreement.setdefault(ad.agreement_id, []).append(ad)

        for agreement in new_agreements:
            n7_places = max(agreement.inp_total_places, 2)
            ay = AgreementYear.objects.create(
                agreement=agreement,
                academic_year=year,
                is_active=True,
                n7_places=n7_places,
                inp_total_places=n7_places,
                is_validated=True,
                validated_by="topup_historical_years",
                validated_at=timezone.now(),
            )
            linked = agreement_depts_by_agreement.get(agreement.id, [])
            if linked:
                share = max(n7_places // len(linked), 1)
                for ad in linked:
                    AgreementYearDepartment.objects.create(
                        agreement_year=ay,
                        agreement_department=ad,
                        estimated_places=share,
                    )
        return len(new_agreements)

    def _topup_year(
        self, year, n_per_dept, depts, levels_by_code, parcours_by_dept, countries
    ):
        from app.mobility.models import AgreementYear

        widened = self._widen_agreement_catalog(year)
        if widened:
            self.stdout.write(
                f"  {year.label} : catalogue accords élargi (+{widened} accords-année)"
            )

        agreement_years = (
            AgreementYear.objects.filter(academic_year=year, is_active=True)
            .select_related("agreement")
            .prefetch_related(
                "department_quotas__agreement_department__department",
                "agreement__levels",
            )
        )
        if not agreement_years:
            self.stderr.write(
                self.style.WARNING(
                    f"  {year.label} : aucun accord-année actif — ignorée."
                )
            )
            return

        remaining_by_ay, remaining_dept_by_ay, level_ids_by_ay = (
            self._compute_remaining_capacity(year, agreement_years)
        )

        dept_to_ays: dict[str, list[tuple]] = {}
        for ay in agreement_years:
            level_ids = level_ids_by_ay[ay.id]
            for dq in ay.department_quotas.all():
                dept_code = dq.agreement_department.department.code
                dept_to_ays.setdefault(dept_code, []).append((ay, level_ids))

        enrollments = create_demo_students(
            year,
            depts,
            levels_by_code,
            parcours_by_dept,
            countries,
            n_per_dept,
            ine_start_index=lambda dept: self._next_ine_index(year, dept),
        )
        n_wishes = create_demo_wishes(enrollments, dept_to_ays)
        self.stdout.write(
            f"  {year.label} : {len(enrollments)} étudiants ajoutés, "
            f"{n_wishes} vœux créés"
        )

        self._run_topup_assignment(
            year, enrollments, remaining_by_ay, remaining_dept_by_ay, level_ids_by_ay
        )

    def _compute_remaining_capacity(self, year, agreement_years):
        from app.outgoing.models import AssignmentResult

        used_by_ay: dict[int, int] = {}
        used_dept_by_ay: dict[int, dict[int, int]] = {}
        results = AssignmentResult.objects.filter(
            assignment__academic_year=year, agreement_year__isnull=False
        ).select_related("annual_enrollment")
        for r in results:
            used_by_ay[r.agreement_year_id] = used_by_ay.get(r.agreement_year_id, 0) + 1
            dept_id = r.annual_enrollment.department_id
            used_dept_by_ay.setdefault(r.agreement_year_id, {})
            used_dept_by_ay[r.agreement_year_id][dept_id] = (
                used_dept_by_ay[r.agreement_year_id].get(dept_id, 0) + 1
            )

        remaining_by_ay: dict[int, int] = {}
        remaining_dept_by_ay: dict[int, dict[int, int]] = {}
        level_ids_by_ay: dict[int, list[int]] = {}
        for ay in agreement_years:
            used = used_by_ay.get(ay.id, 0)
            remaining_by_ay[ay.id] = max(ay.n7_places - used, 0)
            level_ids_by_ay[ay.id] = [lv.id for lv in ay.agreement.levels.all()]

            dept_quota: dict[int, int] = {}
            used_dept = used_dept_by_ay.get(ay.id, {})
            for dq in ay.department_quotas.all():
                dept_id = dq.agreement_department.department_id
                total = dq.get_effective_quota()
                dept_quota[dept_id] = max(total - used_dept.get(dept_id, 0), 0)
            remaining_dept_by_ay[ay.id] = dept_quota

        return remaining_by_ay, remaining_dept_by_ay, level_ids_by_ay

    def _next_ine_index(self, year, dept) -> int:
        """Repart après le plus haut INE déjà utilisé pour ce couple
        (année, département), pour rester idempotent d'un lancement à l'autre
        au lieu de re-collisionner sur le même point de départ. La longueur du
        INE (max_length=11) ne laisse que 3 chiffres pour le département le
        plus long (MF2E) — le compteur boucle avant 999 uniquement dans un
        scénario de volumes extrêmes hors de portée ici."""
        from app.students.models import Student

        prefix = f"{year.start_date.year}{dept.code}"
        existing_suffixes = [
            int(ine[len(prefix) :])
            for ine in Student.objects.filter(
                ine__startswith=prefix, ine__regex=r"\d{3}$"
            ).values_list("ine", flat=True)
            if ine[len(prefix) :].isdigit()
        ]
        return max(existing_suffixes, default=500) + 1

    def _run_topup_assignment(
        self, year, enrollments, remaining_by_ay, remaining_dept_by_ay, level_ids_by_ay
    ):
        from app.outgoing.models import Assignment, AssignmentResult
        from app.outgoing.services.gale_shapley import (
            AgreementInput,
            StudentInput,
            gale_shapley,
        )
        from app.students.models import StudentWish

        agreement_inputs = [
            AgreementInput(
                agreement_year_id=ay_id,
                n7_places=remaining_by_ay[ay_id],
                quota_dept=remaining_dept_by_ay[ay_id],
                level_ids=level_ids_by_ay[ay_id],
            )
            for ay_id in remaining_by_ay
        ]

        wishes_by_enrollment: dict[int, list[int]] = {}
        wishes_qs = StudentWish.objects.filter(
            annual_enrollment__in=enrollments
        ).order_by("annual_enrollment_id", "rank")
        for wish in wishes_qs:
            wishes_by_enrollment.setdefault(wish.annual_enrollment_id, []).append(
                wish.agreement_year_id
            )

        student_inputs = []
        for enrollment in enrollments:
            prefs = wishes_by_enrollment.get(enrollment.id, [])
            if not prefs:
                continue
            nationality = enrollment.student.nationality
            is_french = nationality is not None and nationality.iso2 == "FR"
            gpa = float(enrollment.gpa) if enrollment.gpa is not None else None
            student_inputs.append(
                StudentInput(
                    enrollment_id=enrollment.id,
                    dept_id=enrollment.department_id,
                    is_french=is_french,
                    gpa=gpa,
                    preferences=prefs,
                    level_id=enrollment.level_id,
                )
            )

        outputs = gale_shapley(student_inputs, agreement_inputs)
        assigned = sum(1 for o in outputs if o.agreement_year_id is not None)
        unassigned = sum(1 for o in outputs if o.agreement_year_id is None)

        assignment = Assignment.objects.create(
            academic_year=year,
            run_by="topup_historical_years",
            total_students=len(outputs),
            assigned_count=assigned,
            unassigned_count=unassigned,
        )
        AssignmentResult.objects.bulk_create(
            [
                AssignmentResult(
                    assignment=assignment,
                    annual_enrollment_id=output.enrollment_id,
                    agreement_year_id=output.agreement_year_id,
                    slot_type=output.slot_type,
                    assigned_rank=output.assigned_rank,
                    system_note=output.note,
                )
                for output in outputs
            ]
        )
        assignment.validate()
        assignment.save(update_fields=["status", "updated_at"])
        assignment.publish()
        assignment.save(update_fields=["status", "updated_at"])

        rate = round(assigned / len(outputs) * 100, 1) if outputs else 0
        self.stdout.write(
            f"    → lot supplémentaire : {assigned}/{len(outputs)} affectés ({rate}%) "
            f"— {unassigned} non affectés (capacité restante épuisée)"
        )
