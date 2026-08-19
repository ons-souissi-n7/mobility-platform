from django.contrib.auth import get_user_model


class JWTMiddleware:
    """
    Sets request.user from a JWT Bearer token (or auth_token cookie) on every request,
    so that AuditlogMiddleware and Django admin see the correct user.
    Must be placed between AuthenticationMiddleware and AuditlogMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = self._extract_token(request)
        if token:
            from .authentication import verify_jwt

            payload = verify_jwt(token)
            if payload:
                user_model = get_user_model()
                email = payload.get("email", "")
                try:
                    user = user_model.objects.get(username=email)
                    request.user = user
                except user_model.DoesNotExist:
                    pass
                else:
                    request.jwt_payload = payload
                    request.user_role = payload.get("role", "student")
                    request.user_ine = payload.get("ine", "") or ""

        return self.get_response(request)

    @staticmethod
    def _extract_token(request) -> str | None:
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        # Fallback: cookie (set by the Next.js frontend)
        return request.COOKIES.get("auth_token")
