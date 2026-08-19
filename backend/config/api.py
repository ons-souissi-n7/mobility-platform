from ninja import NinjaAPI

from app.academic.api import router as academic_router
from app.alerts.api import router as alerts_router
from app.analytics.api import router as analytics_router
from app.audit.api import router as audit_router
from app.auth.api import router as auth_router
from app.auth.authentication import AdminJWTAuth, JWTAuth
from app.complementary.api import router as complementary_router
from app.cti.api import router as cti_router
from app.imports.api import router as imports_router
from app.incoming.api import router as incoming_router
from app.institutions.api import router as institutions_router
from app.internships.api import router as internships_router
from app.mobility.api import router as mobility_router
from app.outgoing.api import router as outgoing_router
from app.reference.api import router as reference_router
from app.students.api import router as students_router
from app.students.student_api import router as student_portal_router

api = NinjaAPI(
    title="Mobility Platform API",
    version="1.0.0",
    description="API de gestion des mobilites internationales - ENSEEIHT",
    docs_url="/docs",
    auth=JWTAuth(),
)

api.add_router("/auth/", auth_router, tags=["Auth"], auth=None)
# Référentiels et académique : lecture ouverte à tout utilisateur authentifié,
# écritures/actions admin restreintes endpoint par endpoint (auth=AdminJWTAuth()).
api.add_router("/reference/", reference_router, tags=["Referentiels"])
api.add_router("/academic/", academic_router, tags=["Academic"])
# Portail étudiant en libre-service : chaque endpoint vérifie lui-même que
# l'étudiant n'accède qu'à son propre dossier (require_student_owns).
api.add_router("/student/", student_portal_router, tags=["Student Portal"])
# Mixte (déclaration étudiant + supervision admin) : voir complementary/api.py.
api.add_router("/complementary/", complementary_router, tags=["Complementary Mobility"])
# Mixte (consultation étudiant de sa propre durée + reporting institutionnel) :
# voir cti/api.py.
api.add_router("/cti/", cti_router, tags=["CTI"])

# Routeurs entièrement réservés aux administrateurs RI — aucun endpoint
# n'est destiné à un usage étudiant.
api.add_router(
    "/institutions/", institutions_router, tags=["Institutions"], auth=AdminJWTAuth()
)
api.add_router("/mobility/", mobility_router, tags=["Mobility"], auth=AdminJWTAuth())
api.add_router("/imports/", imports_router, tags=["Imports"], auth=AdminJWTAuth())
api.add_router("/audit/", audit_router, tags=["Audit"], auth=AdminJWTAuth())
api.add_router("/alerts/", alerts_router, tags=["Alerts"], auth=AdminJWTAuth())
api.add_router("/students/", students_router, tags=["Students"], auth=AdminJWTAuth())
api.add_router("/outgoing/", outgoing_router, tags=["Outgoing"], auth=AdminJWTAuth())
api.add_router(
    "/internships/", internships_router, tags=["Internships"], auth=AdminJWTAuth()
)
api.add_router("/incoming/", incoming_router, tags=["Incoming"], auth=AdminJWTAuth())
api.add_router("/analytics/", analytics_router, tags=["Analytics"], auth=AdminJWTAuth())
