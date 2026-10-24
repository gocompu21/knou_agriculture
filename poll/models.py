from django.db import models


class PollResponse(models.Model):
    """AI 모임 사전 설문 응답 1건. 이름 외 개인정보는 받지 않는다(IP 도 저장하지 않는다)."""

    name = models.CharField("이름", max_length=50, db_index=True)
    answers = models.JSONField("답", default=dict)
    created_at = models.DateTimeField("제출 시각", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "AI 설문 응답"
        verbose_name_plural = "AI 설문 응답"

    def __str__(self):
        return f"{self.name} ({self.created_at:%m-%d %H:%M})"
