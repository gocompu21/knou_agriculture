from django.conf import settings
from django.db import models


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
