from django.contrib import admin

from .models import Exam, Question, Attempt


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('year', 'exam_type')
    list_filter = ('exam_type',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'year', 'number', 'text_short', 'answer')
    list_filter = ('subject', 'year')
    search_fields = ('text', 'choice_1', 'choice_2', 'choice_3', 'choice_4')
    list_per_page = 25
    ordering = ('subject', 'year', 'number')

    fieldsets = (
        (None, {
            'fields': ('subject', 'year', 'number', 'text', 'answer'),
        }),
        ('보기', {
            'fields': ('choice_1', 'choice_2', 'choice_3', 'choice_4'),
        }),
        ('해설', {
            'fields': ('choice_1_exp', 'choice_2_exp', 'choice_3_exp', 'choice_4_exp', 'explanation'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='문제')
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    list_per_page = 25
