from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication


class PlanExpiryMiddleware(MiddlewareMixin):
    """Auto-suspend admin accounts when plan expires on every request."""

    def process_request(self, request):
        jwt_auth = JWTAuthentication()
        try:
            result = jwt_auth.authenticate(request)
            if result:
                user, _ = result
                if user.role == 'admin' and user.status == 'active':
                    if user.plan_end and timezone.now().date() > user.plan_end:
                        user.status = 'inactive'
                        user.save(update_fields=['status'])
        except Exception:
            pass