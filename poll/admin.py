from django.contrib import admin

from .models import PollResponse


@admin.register(PollResponse)
class PollResponseAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
