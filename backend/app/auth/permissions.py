from functools import wraps

from ninja.errors import HttpError

# Pour restreindre un routeur (ou un endpoint) aux administrateurs, utiliser
# `auth=AdminJWTAuth()` (app.auth.authentication) plutôt qu'un décorateur ici :
# c'est ce que Ninja utilise pour l'authentification/autorisation, donc un
# rejet lève directement la bonne erreur HTTP sans risque d'oubli au câblage.


def require_admin(func):
    """Raise 403 if request.user_role is not 'admin'.

    View-level fallback for endpoints where operation-level auth=AdminJWTAuth()
    is insufficient (e.g. when the router itself carries a less-restrictive auth).
    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "user_role", "") != "admin":
            raise HttpError(403, "Accès réservé aux administrateurs RI")
        return func(request, *args, **kwargs)

    return wrapper


def require_student_owns(ine_param: str = "ine"):
    """
    Endpoint decorator: students can only access their own resource.
    Admin bypasses the check. The INE to check is taken from kwargs[ine_param].
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # `request.auth` is the User instance Ninja's JWTAuth.authenticate()
            # already resolved for this request — unlike `request.user` (set by
            # the separate JWTMiddleware), it is guaranteed to be populated
            # whenever this view runs, since `auth=JWTAuth()` already rejected
            # unauthenticated requests with 401 before reaching here.
            if getattr(request.auth, "is_staff", False):
                return func(request, *args, **kwargs)
            user_ine = getattr(request, "user_ine", None)
            target_ine = kwargs.get(ine_param)
            if not user_ine or user_ine != target_ine:
                raise HttpError(
                    403,
                    "Accès refusé : vous ne pouvez consulter que votre propre dossier",
                )
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
