from django.contrib import admin

from .models import Certification, GisaExam, GisaSubject, GisaQuestion, GisaAttempt, GisaTextbook, GisaGlossary


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(GisaExam)
class GisaExamAdmin(admin.ModelAdmin):
    list_display = ('certification', 'year', 'round', 'exam_type', 'exam_date')
    list_filter = ('certification', 'year', 'exam_type')


@admin.register(GisaSubject)
class GisaSubjectAdmin(admin.ModelAdmin):
    list_display = ('certification', 'order', 'name')
    list_filter = ('certification',)
    ordering = ('certification', 'order')


@admin.register(GisaQuestion)
class GisaQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'subject', 'number', 'text_short', 'answer')
    list_filter = ('exam__certification', 'exam', 'subject')
    search_fields = ('text', 'choice_1', 'choice_2', 'choice_3', 'choice_4')
    list_per_page = 25
    ordering = ('exam', 'number')

    fieldsets = (
        (None, {
            'fields': ('exam', 'subject', 'number', 'text', 'answer'),
        }),
        ('보기', {
            'fields': ('choice_1', 'choice_2', 'choice_3', 'choice_4'),
        }),
        ('이미지', {
            'fields': ('text_image', 'choice_1_image', 'choice_2_image', 'choice_3_image', 'choice_4_image'),
            'classes': ('collapse',),
        }),
        ('해설', {
            'fields': ('choice_1_exp', 'choice_2_exp', 'choice_3_exp', 'choice_4_exp', 'explanation'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='문제')
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text


@admin.register(GisaTextbook)
class GisaTextbookAdmin(admin.ModelAdmin):
    list_display = ('certification', 'subject', 'content_length', 'updated_at')
    list_filter = ('certification',)

    @admin.display(description='분량')
    def content_length(self, obj):
        return f"{len(obj.content):,} chars"


@admin.register(GisaGlossary)
class GisaGlossaryAdmin(admin.ModelAdmin):
    list_display = ('certification', 'subject', 'term', 'has_description')
    list_filter = ('certification', 'subject')
    search_fields = ('term', 'description')
    list_per_page = 50

    @admin.display(description='설명', boolean=True)
    def has_description(self, obj):
        return bool(obj.description)


@admin.register(GisaAttempt)
class GisaAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected', 'is_correct', 'mode', 'created_at')
    list_filter = ('is_correct', 'mode', 'created_at')
    list_per_page = 25
