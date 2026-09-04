<#
    seed-full-demo.ps1 — Reconstruit une base de démonstration complète et variée.

    Historique 2021-2022 -> 2025-2026 : 5 campagnes CLÔTURÉES (vraies transitions
    FSM + vrai algorithme Gale-Shapley + CTI finalisé), 2 vagues d'affectation par
    année, + entrants / stages / mobilités complémentaires sur toutes les années,
    + cas de réconciliation d'import, + préparation des données CTI (niveaux
    terminaux, durées d'échange variées, table MobilityDuration).

    L'année courante 2026-2027 n'est PAS créée — à faire soi-même depuis l'admin.

    À lancer depuis d:\PFE\mobility-platform, Docker Desktop démarré.
    N'utilise que les commandes de seed déjà fournies par le projet
    (cf. README « Données de démonstration ») + un post-traitement CTI.

    ⚠️  Étape 1 : REMET LA BASE À ZÉRO (supprime le volume postgres).
        Mémoire Docker limitée (~4 Go) : sonarqube est arrêté pendant le seed.
#>

$ErrorActionPreference = "Stop"
$dev = "docker","compose","-f","docker-compose.dev.yml"
$all = "docker","compose","-f","docker-compose.dev.yml","-f","docker-compose.monitoring.yml"
function dj { & docker compose -f docker-compose.dev.yml exec -T backend python manage.py @args }

$YEARS = @("2021-2022","2022-2023","2023-2024","2024-2025","2025-2026")

# ── 1. Reset base + services légers uniquement (db + backend) ────────────────
Write-Host "`n=== 1. Reset base ===" -ForegroundColor Cyan
& $dev down
docker volume rm mobility-platform_postgres_data 2>$null
& $dev up -d db backend
Write-Host "Attente backend healthy (migrations incluses)..." -ForegroundColor DarkGray
do {
    Start-Sleep -Seconds 3
    $s = (& docker inspect --format '{{.State.Health.Status}}' mobility-platform-backend-1 2>$null)
} until ($s -eq "healthy")

# ── 2. Référentiels ────────────────────────────────────────────────────────────
Write-Host "`n=== 2. Référentiels (pays, dépts, niveaux, parcours, universités, accords) ===" -ForegroundColor Cyan
dj loaddata `
  app/reference/fixtures/countries.json `
  app/reference/fixtures/departments.json `
  app/reference/fixtures/levels.json `
  app/reference/fixtures/parcours.json `
  app/institutions/fixtures/universities.json `
  app/mobility/fixtures/mobility_categories.json `
  app/mobility/fixtures/agreements.json `
  app/mobility/fixtures/agreement_departments.json
dj enrich_partner_network

# ── 3. Historique : 5 campagnes clôturées, ~105 étudiants/an ───────────────────
Write-Host "`n=== 3. reset_historical_years (5 ans, Gale-Shapley réel, CTI finalisé) ===" -ForegroundColor Cyan
dj reset_historical_years --labels @YEARS --students-per-dept 35

# ── 4. Entrants / stages / mobilités complémentaires ──────────────────────────
Write-Host "`n=== 4. seed_mobility_data ===" -ForegroundColor Cyan
dj seed_mobility_data

# ── 5. 2e vague d'affectation par année (capacité restante -> non-affectés) ────
Write-Host "`n=== 5. topup_historical_years ===" -ForegroundColor Cyan
dj topup_historical_years --labels @YEARS --students-per-dept 20

# ── 6. Cas de réconciliation d'import ─────────────────────────────────────────
Write-Host "`n=== 6. seed_reconciliation_cases ===" -ForegroundColor Cyan
dj seed_reconciliation_cases

# ── 7. Post-traitement CTI ───────────────────────────────────────────────────
#   - 3ING + 2M = niveaux terminaux (sinon la cohorte CTI est vide)
#   - duration_weeks variés par partenariat (répartit les catégories <1sem / =1sem / >1sem)
#   - table MobilityDuration remplie pour tous les étudiants
#   - durées lisibles pour les entrants (le parseur CTI attend "1 semestre", "1 an"...)
Write-Host "`n=== 7. Préparation données CTI ===" -ForegroundColor Cyan
$py = @'
from app.reference.models import Level
from app.mobility.models import AgreementYear
from app.incoming.models import IncomingStudent
from app.cti.services import refresh_cti_duration
from app.students.models import Student

print("niveaux terminaux:", Level.objects.filter(code__in=["3ING","2M"]).update(is_terminal=True))

cycle = [12, 16, 20, 20, 24, 26, 30, 36]
for ay in AgreementYear.objects.all():
    ay.duration_weeks = cycle[ay.agreement_id % len(cycle)]
    ay.save(update_fields=["duration_weeks"])
print("AgreementYear.duration_weeks renseignés:", AgreementYear.objects.count())

labels = ["1 semestre", "1 semestre", "2 semestres", "1 an", "5 mois", "10 mois"]
for s in IncomingStudent.objects.all().iterator():
    s.duration = labels[s.id % len(labels)]
    s.save(update_fields=["duration"])
print("IncomingStudent.duration normalisés:", IncomingStudent.objects.count())

n = 0
for s in Student.objects.all().iterator():
    refresh_cti_duration(s); n += 1
print("MobilityDuration rafraîchies:", n)
'@
dj shell -c $py

# ── 8. Relance de toute la stack (hors sonarqube) ────────────────────────────
Write-Host "`n=== 8. Relance stack (frontend, worker, grafana, prometheus, fakes) ===" -ForegroundColor Cyan
& $all up -d --no-recreate db backend worker frontend fake-cas fake-moveon-api fake-pegase-api fake-eudonet-api minio prometheus grafana

Write-Host @"

✓ Base peuplée.
  Frontend   http://localhost:3000      Admin  http://localhost:8000/admin/
  API docs   http://localhost:8000/api/v1/docs
  Grafana    http://localhost:3001 (admin/admin)   Prometheus http://localhost:9090
  (sonarqube arrêté — 'docker start sonarqube' au besoin)

  Export CTI d'une année : GET /api/v1/cti/export/?academic_year_id=<id>
"@ -ForegroundColor Gray
