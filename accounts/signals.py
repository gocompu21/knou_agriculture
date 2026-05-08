from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LoginLog, UserProfile


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginLog.objects.create(user=user)


@receiver(pre_social_login)
def set_name_from_social(sender, request, sociallogin, **kwargs):
    """네이버 로그인 시 이름(first_name) 자동 설정"""
    user = sociallogin.user
    extra = sociallogin.account.extra_data
    name = extra.get("name", "")
    if name and not user.first_name:
        user.first_name = name


@receiver(pre_save, sender=get_user_model())
def track_password_change(sender, instance, **kwargs):
    """User 저장 시 password 필드가 바뀌면 UserProfile.password_changed_at 갱신.

    - 신규 가입(pk 없음)은 제외
    - 비밀번호 해시가 변경된 경우에만 시각 기록
    """
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if old.password != instance.password:
        # post_save에서 처리하면 무한 루프 위험이 있어 pre_save에서 별도 저장
        profile, _ = UserProfile.objects.get_or_create(user_id=instance.pk)
        profile.password_changed_at = timezone.now()
        profile.save(update_fields=["password_changed_at"])
