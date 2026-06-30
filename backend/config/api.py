from ninja import NinjaAPI

from app.academic.api import router as academic_router
from app.audit.api import router as audit_router
from app.imports.api import router as imports_router
from app.institutions.api import router as institutions_router
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
)

api.add_router("/reference/", reference_router, tags=["Referentiels"])
api.add_router("/institutions/", institutions_router, tags=["Institutions"])
api.add_router("/academic/", academic_router, tags=["Academic"])
api.add_router("/mobility/", mobility_router, tags=["Mobility"])
api.add_router("/imports/", imports_router, tags=["Imports"])
api.add_router("/audit/", audit_router, tags=["Audit"])
api.add_router("/students/", students_router, tags=["Students"])
api.add_router("/outgoing/", outgoing_router, tags=["Outgoing"])
api.add_router("/student/", student_portal_router, tags=["Student Portal"])
