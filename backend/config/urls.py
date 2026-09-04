from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_GET

from .api import api


@require_GET
def health_check(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("health/", health_check, name="health-check"),
    # Expose /metrics pour le scrape Prometheus (monitoring/prometheus.yml) —
    # sans cette route, Prometheus interroge un endpoint inexistant (404) et
    # les tableaux de bord Grafana restent vides malgré des conteneurs actifs.
    path("", include("django_prometheus.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Route de debug (dev uniquement) : lève une exception non gérée pour
    # vérifier de bout en bout la remontée vers Sentry via une vraie requête
    # HTTP (transaction, en-têtes et pile d'appel réels). Absente hors DEBUG.
    def _sentry_debug(_request):
        raise RuntimeError(
            "Erreur volontaire /sentry-debug/ - test de la remontee Sentry"
        )

    urlpatterns += [path("sentry-debug/", _sentry_debug)]
