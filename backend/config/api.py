from ninja import NinjaAPI

from app.institutions.api import router as institutions_router
from app.reference.api import router as reference_router

api = NinjaAPI(
    title="Mobility Platform API",
    version="1.0.0",
    description="API de gestion des mobilites internationales - ENSEEIHT",
    docs_url="/docs",
)

api.add_router("/reference/", reference_router, tags=["Referentiels"])
api.add_router("/institutions/", institutions_router, tags=["Institutions"])
