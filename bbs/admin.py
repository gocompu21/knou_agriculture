from django.contrib import admin

from .models import Comment, Notice, NoticeOpenLog


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_pinned", "view_count", "created_at")
    list_filter = ("is_pinned", "created_at")
    search_fields = ("title", "content")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("notice", "author", "content", "created_at")
    list_filter = ("created_at",)


@admin.register(NoticeOpenLog)
class NoticeOpenLogAdmin(admin.ModelAdmin):
    list_display = ("notice", "user", "opened_at", "ip")
    list_filter = ("opened_at",)
    search_fields = ("user__username", "notice__title")
    readonly_fields = ("notice", "user", "opened_at", "ip", "user_agent")
