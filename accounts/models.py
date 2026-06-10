import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="사용자",
    )
    receive_email = models.BooleanField("이메일 수신", default=True)
    password_changed_at = models.DateTimeField("비밀번호 변경 시각", null=True, blank=True)
    is_approved = models.BooleanField("관리자 승인", default=False)
    approved_at = models.DateTimeField("승인 시각", null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_signups",
        verbose_name="승인자",
    )

    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필"

    def __str__(self):
        return f"{self.user.username} 프로필"


class LoginLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_logs",
        verbose_name="사용자",
    )
    logged_in_at = models.DateTimeField("로그인 시각", auto_now_add=True)

    class Meta:
        verbose_name = "로그인 기록"
        verbose_name_plural = "로그인 기록"
        ordering = ["-logged_in_at"]

    def __str__(self):
        return f"{self.user.username} - {self.logged_in_at:%Y-%m-%d %H:%M}"


def _default_expiry():
    return timezone.now() + timedelta(hours=24)


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
        verbose_name="사용자",
    )
    token = models.UUIDField("토큰", default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("생성 시각", auto_now_add=True)
    expires_at = models.DateTimeField("만료 시각", default=_default_expiry)

    class Meta:
        verbose_name = "이메일 인증 토큰"
        verbose_name_plural = "이메일 인증 토큰"

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def refresh(self):
        self.token = uuid.uuid4()
        self.expires_at = _default_expiry()
        self.save(update_fields=["token", "expires_at"])

    def __str__(self):
        return f"{self.user.username} 인증토큰"
