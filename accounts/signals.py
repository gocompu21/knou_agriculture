from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import LoginLog


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
