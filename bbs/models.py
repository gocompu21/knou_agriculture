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
