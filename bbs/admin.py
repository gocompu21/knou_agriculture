from django.contrib import admin

from .models import Comment, Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_pinned", "view_count", "created_at")
    list_filter = ("is_pinned", "created_at")
    search_fields = ("title", "content")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("notice", "author", "content", "created_at")
    list_filter = ("created_at",)
