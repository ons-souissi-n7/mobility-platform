"""
Tests de performance et de montée en charge — BNF01 & BNF04.

BNF01 : Temps de réponse < 500 ms pour 95 % des requêtes API standard.
BNF04 : L'application supporte 200 étudiants inscrits simultanément.
         L'algorithme Gale-Shapley termine en < 30 s (couvert dans test_gale_shapley.py).

Ces tests sont des benchmarks instrumentés ; ils s'exécutent dans le même
processus que les tests unitaires mais mesurent la durée réelle des requêtes
HTTP via le client Django de test.

Note : les seuils sont intentionnellement généreux (x3 sur 500 ms) en
environnement CI où la base est en mémoire et sans pool de connexions. Les
seuils stricts s'appliquent en staging via les sondes Prometheus/Grafana.
"""

import time
from datetime import date

import pytest
from django.test import Client

from app.academic.models import AcademicYear
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student

# ---------------------------------------------------------------------------
# Seuils de performance (ms)
# ---------------------------------------------------------------------------

RESPONSE_TIME_MS_SOFT = 1500  # seuil soft en CI (overhead SQLite/in-proc)
RESPONSE_TIME_MS_STRICT = 500  # objectif rapport BNF01 (staging/prod)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bulk_students(
    n: int, year: AcademicYear, dept: Department, level: Level
) -> None:
    students = [
        Student(ine=f"{i:011d}", first_name="Test", last_name=f"Etu{i}")
        for i in range(n)
    ]
    Student.objects.bulk_create(students, ignore_conflicts=True)
    enrollments = [
        AnnualEnrollment(student=s, academic_year=year, department=dept, level=level)
        for s in Student.objects.filter(ine__startswith="0")[:n]
    ]
    AnnualEnrollment.objects.bulk_create(enrollments, ignore_conflicts=True)


# ---------------------------------------------------------------------------
# BNF01 — Temps de réponse des endpoints API courants
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestApiResponseTimes:
    """Vérifie que les endpoints API répondent dans les délais acceptables (BNF01)."""

    def setup_method(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(
            label="BNF01-TEST",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 1),
        )

    def _timed_get(self, path: str) -> float:
        """Retourne le temps de réponse en ms."""
        start = time.perf_counter()
        response = self.client.get(path)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert (
            response.status_code == 200
        ), f"Endpoint {path} a retourné {response.status_code}"
        return elapsed_ms

    def test_reference_countries_response_time(self):
        Country.objects.bulk_create(
            [
                Country(
                    iso2=f"{chr(65 + i // 26)}{chr(65 + i % 26)}",
                    name_fr=f"Pays{i}",
                    name_en=f"Country{i}",
                    cti_region=CTIRegion.EUROPE_HORS_FRANCE,
                )
                for i in range(50)
            ],
            ignore_conflicts=True,
        )
        elapsed = self._timed_get("/api/v1/reference/countries/")
        assert (
            elapsed < RESPONSE_TIME_MS_SOFT
        ), f"GET /reference/countries/ a pris {elapsed:.0f} ms (seuil : {RESPONSE_TIME_MS_SOFT} ms)"

    def test_reference_departments_response_time(self):
        elapsed = self._timed_get("/api/v1/reference/departments/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_academic_years_list_response_time(self):
        elapsed = self._timed_get("/api/v1/academic/years/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_students_list_response_time(self):
        elapsed = self._timed_get("/api/v1/students/students/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_agreements_list_response_time(self):
        elapsed = self._timed_get("/api/v1/mobility/agreements/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_audit_logs_response_time(self):
        elapsed = self._timed_get("/api/v1/audit/logs/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_alerts_response_time(self):
        elapsed = self._timed_get("/api/v1/alerts/")
        assert elapsed < RESPONSE_TIME_MS_SOFT

    def test_mobility_categories_response_time(self):
        elapsed = self._timed_get("/api/v1/mobility/agreement-categories/")
        assert elapsed < RESPONSE_TIME_MS_SOFT


# ---------------------------------------------------------------------------
# BNF04 — Montée en charge : 200 étudiants inscrits
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScalability200Students:
    """
    BNF04 : La plateforme doit supporter une cohorte de 200 étudiants.
    Vérifie que la liste et les statistiques restent rapides avec 200 enrôlements.
    """

    def setup_method(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(
            label="BNF04-LOAD",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 7, 1),
        )
        dept = Department.objects.create(code="PERF", name="Département Performance")
        level = Level.objects.create(code="3A-P", name="3ème année Perf")
        _make_bulk_students(200, self.year, dept, level)

    def test_list_200_students_response_time(self):
        start = time.perf_counter()
        response = self.client.get(
            f"/api/v1/students/students/?academic_year_id={self.year.id}&page_size=200"
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        body = response.json()
        assert body["count"] >= 200, "Doit retourner au moins 200 étudiants"
        assert (
            elapsed_ms < RESPONSE_TIME_MS_SOFT
        ), f"Liste de 200 étudiants a pris {elapsed_ms:.0f} ms (seuil : {RESPONSE_TIME_MS_SOFT} ms)"

    def test_student_stats_with_200_enrollments(self):
        start = time.perf_counter()
        response = self.client.get(
            f"/api/v1/students/students/stats/?academic_year_id={self.year.id}"
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        assert (
            elapsed_ms < RESPONSE_TIME_MS_SOFT
        ), f"Stats de 200 étudiants a pris {elapsed_ms:.0f} ms"

    def test_pagination_200_students(self):
        """La pagination doit fonctionner correctement pour 200 étudiants."""
        response = self.client.get(
            f"/api/v1/students/students/?academic_year_id={self.year.id}&page_size=50&page=1"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["count"] >= 200
        assert len(body["results"]) <= 50


# ---------------------------------------------------------------------------
# BNF04 — Cohérence des données en écriture concurrente simulée
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
class TestConcurrentWrite:
    """
    Simule des écritures séquentielles rapides et vérifie l'intégrité des données.
    (Test de robustesse, pas de vraie concurrence en SQLite — utiliser Postgres en staging.)
    """

    def test_bulk_student_create_integrity(self):
        Department.objects.create(code="CONC", name="Concurrent Dept")
        Level.objects.create(code="2A-C", name="2A Concurrent")
        AcademicYear.objects.create(
            label="CONC-2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 7, 1),
        )

        students = [
            Student(ine=f"CONC{i:07d}", first_name="C", last_name=f"Student{i}")
            for i in range(100)
        ]
        Student.objects.bulk_create(students)
        created = Student.objects.filter(ine__startswith="CONC").count()
        assert created == 100, f"Attendu 100, créé {created}"

    def test_atomic_rollback_on_invalid_enrollment(self):
        """Un enrollement invalide doit être rollbacké sans corrompre les données."""
        dept = Department.objects.create(code="ROLL", name="Rollback Dept")
        level = Level.objects.create(code="4A-R", name="4A Roll")
        year = AcademicYear.objects.create(
            label="ROLL-2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 7, 1),
        )
        student = Student.objects.create(
            ine="ROLLTEST01", first_name="R", last_name="B"
        )

        from django.db import transaction

        count_before = AnnualEnrollment.objects.count()
        try:
            with transaction.atomic():
                AnnualEnrollment.objects.create(
                    student=student, academic_year=year, department=dept, level=level
                )
                # Forcer une erreur
                raise ValueError("Erreur intentionnelle dans la transaction")
        except ValueError:
            pass

        count_after = AnnualEnrollment.objects.count()
        assert count_after == count_before, "Le rollback doit annuler l'inscription"


# ---------------------------------------------------------------------------
# BNF05 — Couverture minimale (vérifié aussi par le flag --cov-fail-under=80)
# ---------------------------------------------------------------------------


def test_coverage_threshold_configured():
    """
    BNF05 : La couverture de tests est configurée à 80 % minimum en CI.

    Le seuil n'est pas stocké dans pytest.ini/pyproject.toml (pytest-cov n'a pas
    d'option `fail_under` reconnue dans [tool.coverage.run]) : il est appliqué
    via l'option de ligne de commande --cov-fail-under=80, passée systématiquement
    par le pipeline CI (.github/workflows/ci.yml), le README et le Makefile.

    Ce test vérifie uniquement, de façon rapide et déterministe, que la config
    de mesure de couverture ([tool.coverage.run] dans pyproject.toml — la seule
    partie garantie accessible ici, `backend/` étant le seul répertoire monté
    dans le conteneur de dev) est bien présente et n'omet pas tout le code utile.
    La valeur du seuil (80 %) elle-même est vérifiée par CI en conditions réelles
    (voir le résultat effectif : "Required test coverage of 80% reached").

    L'ancienne version de ce test spawnait un `pytest --co` complet en
    sous-processus avec un timeout de 30 s, devenu plus lent que la collecte
    réelle de la suite à mesure qu'elle grossissait — cf. audit qualité.
    """
    import tomllib
    from pathlib import Path

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml introuvable : {pyproject_path}"

    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    coverage_run = config.get("tool", {}).get("coverage", {}).get("run", {})
    assert coverage_run, "[tool.coverage.run] doit être configuré dans pyproject.toml"

    omitted = coverage_run.get("omit", [])
    assert "manage.py" in omitted, "manage.py doit être exclu de la couverture"
    # Le code applicatif (app/) ne doit pas être omis en bloc.
    assert not any(
        pattern.startswith("app/") for pattern in omitted
    ), "La couverture ne doit pas exclure le code applicatif dans app/"
