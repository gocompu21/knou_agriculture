from django.contrib import admin

from .models import Subject, FavoriteSubject, SubjectMaterial, MaterialOpenLog


@admin.register(SubjectMaterial)
class SubjectMaterialAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'uploaded_by', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'subject__name')


@admin.register(MaterialOpenLog)
class MaterialOpenLogAdmin(admin.ModelAdmin):
    list_display = ('material', 'user', 'opened_at', 'ip')
    list_filter = ('opened_at',)
    search_fields = ('user__username', 'material__title')
    readonly_fields = ('material', 'user', 'opened_at', 'ip', 'user_agent')
