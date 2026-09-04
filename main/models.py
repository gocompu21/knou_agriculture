from django.conf import settings
from django.db import models


class Subject(models.Model):
    GRADE_CHOICES = [(1, '1학년'), (2, '2학년'), (3, '3학년'), (4, '4학년')]
    SEMESTER_CHOICES = [(1, '1학기'), (2, '2학기')]
    CATEGORY_CHOICES = [('전공', '전공'), ('교양', '교양')]

    department = models.CharField('학과', max_length=50, default='농학과')
    name = models.CharField('과목명', max_length=100)
    grade = models.IntegerField('학년', choices=GRADE_CHOICES)
    semester = models.IntegerField('학기', choices=SEMESTER_CHOICES)
    category = models.CharField('구분', max_length=10, choices=CATEGORY_CHOICES, default='전공')

    class Meta:
        verbose_name = '교과과목'
        verbose_name_plural = '교과과목'
        ordering = ['grade', 'semester', 'name']

    def __str__(self):
        return f"[{self.get_grade_display()} {self.get_semester_display()}] {self.name} ({self.category})"


class FavoriteSubject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='과목')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        verbose_name = '관심과목'
        verbose_name_plural = '관심과목'
        unique_together = ['user', 'subject']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.subject.name}"


def _material_upload_path(instance, filename):
    return f"materials/subject_{instance.subject_id}/{filename}"


class SubjectMaterial(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='과목', related_name='materials')
    title = models.CharField('자료 제목', max_length=200)
    file = models.FileField('PDF 파일', upload_to=_material_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='등록자')
    created_at = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        verbose_name = '교과목 자료'
        verbose_name_plural = '교과목 자료'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject.name} - {self.title}"


class MaterialOpenLog(models.Model):
    """PDF 자료(SubjectMaterial) 열람·인쇄 기록.
    - action='view': material_view 페이지 진입 시 저장
    - action='print': 인쇄 버튼 클릭 시 저장
    """
    ACTION_CHOICES = [
        ('view', '열람'),
        ('print', '인쇄'),
    ]
    material = models.ForeignKey(SubjectMaterial, on_delete=models.CASCADE, related_name='open_logs', verbose_name='자료')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='material_opens', verbose_name='사용자')
    action = models.CharField('동작', max_length=10, choices=ACTION_CHOICES, default='view')
    opened_at = models.DateTimeField('시각', auto_now_add=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=300, blank=True)

    class Meta:
        verbose_name = 'PDF 열람·인쇄 기록'
        verbose_name_plural = 'PDF 열람·인쇄 기록'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['material', 'user']),
            models.Index(fields=['opened_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.material.title[:20]} @ {self.opened_at:%Y-%m-%d %H:%M}"


class SubjectViewLog(models.Model):
    """과목 상세 페이지(subject_detail) 진입 기록.
    사용자가 어느 과목의 어느 탭을 언제 봤는지 추적.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='view_logs', verbose_name='과목')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subject_views', verbose_name='사용자')
    tab = models.CharField('탭', max_length=20, blank=True, default='')
    viewed_at = models.DateTimeField('시각', auto_now_add=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=300, blank=True)

    class Meta:
        verbose_name = '과목 페이지 조회'
        verbose_name_plural = '과목 페이지 조회'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['subject', 'tab', 'viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed {self.subject.name}[{self.tab}] @ {self.viewed_at:%Y-%m-%d %H:%M}"


class QnaQuestion(models.Model):
    """질의응답 — 과목별로 묻고 AI가 답한다.

    답은 Gemini 가 실시간으로 쓴다. 사전 검증을 거치지 않으므로 화면에
    그 사실을 밝히고, 이상한 답을 신고받아(flagged) 관리 화면에서
    모아 볼 수 있게 한다. 실제로 생태통로 기능이나 파편화 용어처럼
    정설과 어긋난 서술이 나오는 일이 있다.

    과목은 사용자가 고르는 대신 질문한 화면에서 자동으로 잡는다.
    회원 대부분이 한쪽 시험만 쓰고(방송대 59 / 기사 8 / 둘 다 24),
    실기는 과목 구분 자체가 없어 고르게 하면 번거롭기만 하다.
    """
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='questions',
        null=True, blank=True, verbose_name='과목')
    # 기사시험 쪽 질문은 자격증으로 묶는다 (문자열로 두어 앱 간 결합을 피함)
    cert_name = models.CharField('자격증', max_length=50, blank=True, default='')
    cert_subject = models.CharField('기사 과목', max_length=50, blank=True, default='')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='qna_questions', verbose_name='질문자')
    title = models.CharField('질문', max_length=200)
    body = models.TextField('보충 설명', blank=True, default='')

    answer = models.TextField('답변', blank=True, default='')
    answer_model = models.CharField('모델', max_length=40, blank=True, default='')
    # 답에 근거로 쓴 쪽집게 노트 대목. 비어 있으면 교재 밖 내용이라는 뜻이라
    # 화면에서 그 차이를 알려 준다.
    note_ref = models.CharField('참고 노트', max_length=200, blank=True, default='')
    answered_at = models.DateTimeField('답변 시각', null=True, blank=True)
    error = models.CharField('오류', max_length=200, blank=True, default='')

    view_count = models.PositiveIntegerField('조회수', default=0)
    flagged = models.PositiveIntegerField('신고', default=0)
    created_at = models.DateTimeField('작성일', auto_now_add=True)

    class Meta:
        verbose_name = '질의응답'
        verbose_name_plural = '질의응답'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', '-created_at']),
            models.Index(fields=['cert_name', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        where = self.subject.name if self.subject else (self.cert_name or '전체')
        return f"[{where}] {self.title[:30]}"

    @property
    def where(self):
        """질문이 걸린 자리 — 과목 또는 자격증(+과목)"""
        if self.subject:
            return self.subject.name
        if self.cert_subject:
            return f"{self.cert_name} · {self.cert_subject}"
        return self.cert_name or '전체'


class QnaView(models.Model):
    """질문 조회 기록 — 같은 사람이 여러 번 열어도 조회수는 한 번만 센다."""
    question = models.ForeignKey(
        QnaQuestion, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='qna_views')
    viewed_at = models.DateTimeField('시각', auto_now_add=True)

    class Meta:
        verbose_name = '질문 조회'
        verbose_name_plural = '질문 조회'
        unique_together = [('question', 'user')]
