from django.contrib.auth.models import User


def pending_signup_count(request):
    """staff에게만 가입 승인 대기 건수를 노출."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return {"pending_signup_count": 0}
    cnt = User.objects.filter(
        is_active=False, profile__is_approved=False
    ).count()
    return {"pending_signup_count": cnt}
