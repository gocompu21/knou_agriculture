from django.contrib.auth.models import User
from django.db import models


class Notice(models.Model):
    title = models.CharField("제목", max_length=200)
    content = models.TextField("내용")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_pinned = models.BooleanField("상단고정", default=False)
    view_count = models.IntegerField("조회수", default=0)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    notice = models.ForeignKey(
        Notice, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField("댓글")
    created_at = models.DateTimeField("작성일", auto_now_add=True)

    class Meta:
        verbose_name = "댓글"
        verbose_name_plural = "댓글"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} - {self.content[:20]}"


class NoticeOpenLog(models.Model):
    """공지사항 메일 열람 기록 (트래킹 픽셀 호출 시 생성)."""

    notice = models.ForeignKey(
        Notice, on_delete=models.CASCADE, related_name="open_logs", verbose_name="공지"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notice_opens", verbose_name="사용자"
    )
    opened_at = models.DateTimeField("열람 시각", auto_now_add=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=300, blank=True)

    class Meta:
        verbose_name = "메일 열람 기록"
        verbose_name_plural = "메일 열람 기록"
        ordering = ["-opened_at"]
        indexes = [
            models.Index(fields=["notice", "user"]),
            models.Index(fields=["opened_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.notice.title[:20]} @ {self.opened_at:%Y-%m-%d %H:%M}"
