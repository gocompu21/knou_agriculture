from django.contrib import admin

from .models import Subject, FavoriteSubject, SubjectMaterial


@admin.register(SubjectMaterial)
class SubjectMaterialAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'uploaded_by', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'subject__name')
