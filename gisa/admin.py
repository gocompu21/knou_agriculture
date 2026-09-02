from django.contrib import admin

from .models import (Certification, GisaExam, GisaSubject, GisaQuestion, GisaAttempt,
                     GisaTextbook, GisaGlossary, MockGeneration, CertificationViewLog,
                     GisaEssayQuestion, GisaEssaySession, GisaEssayAttempt, GisaEssayUpload)


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


@admin.register(MockGeneration)
class MockGenerationAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'generation', 'seen_count', 'updated_at')
    list_filter = ('subject', 'generation')
    search_fields = ('user__username', 'subject__name')
    readonly_fields = ('seen_question_ids',)

    def seen_count(self, obj):
        return len(obj.seen_question_ids or [])
    seen_count.short_description = '누적 출제수'


@admin.register(CertificationViewLog)
class CertificationViewLogAdmin(admin.ModelAdmin):
    list_display = ('viewed_at', 'user', 'certification', 'tab', 'ip')
    list_filter = ('tab', 'certification')
    search_fields = ('user__username', 'user__first_name', 'certification__name')
    date_hierarchy = 'viewed_at'
    readonly_fields = ('certification', 'user', 'tab', 'viewed_at', 'ip', 'user_agent')


# ════════════════════ 실기 필답형 ════════════════════

@admin.register(GisaEssayQuestion)
class GisaEssayQuestionAdmin(admin.ModelAdmin):
    list_display = ('label_col', 'number', 'orig_number', 'qtype', 'points',
                    'topic_group', 'text_head', 'has_note')
    list_filter = ('certification', 'source', 'qtype', 'topic_group', 'section', 'year')
    search_fields = ('text', 'answer_text', 'notes')
    list_per_page = 40
    fieldsets = (
        ('분류', {'fields': ('certification', 'source', 'section', 'year', 'round',
                           'number', 'orig_number', 'qtype', 'points',
                           'topic_group', 'std_major', 'std_sub')}),
        ('문제', {'fields': ('text', 'text_image')}),
        ('답', {'fields': ('answer_items', 'answer_text', 'answer_image', 'rubric')}),
        ('해설', {'fields': ('reference', 'reference_image')}),
        ('메모', {'fields': ('notes',)}),
    )

    def label_col(self, obj):
        return obj.label
    label_col.short_description = '출처'

    def text_head(self, obj):
        return (obj.text or '')[:60]
    text_head.short_description = '문제'

    def has_note(self, obj):
        return bool(obj.notes)
    has_note.boolean = True
    has_note.short_description = '메모'


class GisaEssayAttemptInline(admin.TabularInline):
    model = GisaEssayAttempt
    extra = 0
    fields = ('question', 'answer_text', 'ai_score', 'final_score', 'graded_at')
    readonly_fields = ('question', 'graded_at')


@admin.register(GisaEssaySession)
class GisaEssaySessionAdmin(admin.ModelAdmin):
    list_display = ('started_at', 'user', 'certification', 'label_col', 'mode',
                    'status', 'score', 'total_points')
    list_filter = ('certification', 'source', 'mode', 'status')
    search_fields = ('user__username', 'user__first_name', 'paper_code')
    date_hierarchy = 'started_at'
    inlines = [GisaEssayAttemptInline]

    def label_col(self, obj):
        return obj.label
    label_col.short_description = '범위'


@admin.register(GisaEssayUpload)
class GisaEssayUploadAdmin(admin.ModelAdmin):
    list_display = ('uploaded_at', 'session', 'page_no', 'transcribed')
    list_filter = ('transcribed',)
    readonly_fields = ('session', 'page_no', 'image', 'uploaded_at')
