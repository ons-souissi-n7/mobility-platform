class DomainValidationError(Exception):
    """Raised by business-layer validators (import, sync).

    Distinct from django.core.exceptions.ValidationError, which is raised by
    model clean() methods and caught by the ORM / admin / forms layer.
    """
