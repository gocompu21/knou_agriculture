from django.contrib import admin
from .models import UploadedPDF


@admin.register(UploadedPDF)
class UploadedPDFAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['title']
