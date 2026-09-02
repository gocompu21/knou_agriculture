from django.conf import settings
from django.db import models


class Certification(models.Model):
    CATEGORY_CHOICES = [
        ('기사', '기사'),
        ('산업기사', '산업기사'),
        ('기능사', '기능사'),
        ('기능장', '기능장'),
        ('기술사', '기술사'),
    ]

    name = models.CharField('자격증명', max_length=100)
    category = models.CharField('등급', max_length=20, choices=CATEGORY_CHOICES, default='기사')
    description = models.TextField('설명', blank=True)

    class Meta:
        verbose_name = '자격증'
        verbose_name_plural = '자격증'
        ordering = ['category', 'name']
        unique_together = ['name', 'category']

    def __str__(self):
        return f"{self.name} ({self.category})"


class GisaExam(models.Model):
    EXAM_TYPE_CHOICES = [
        ('필기', '필기'),
        ('실기', '실기'),
        ('최신', '최신기출'),
    ]

    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, verbose_name='자격증')
    year = models.IntegerField('출제연도')
    round = models.IntegerField('회차', default=1)
    exam_date = models.DateField('시험일자', null=True, blank=True)
    exam_type = models.CharField('시험유형', max_length=10, choices=EXAM_TYPE_CHOICES, default='필기')

    class Meta:
        verbose_name = '시험회차'
        verbose_name_plural = '시험회차'
        ordering = ['-year', '-round']
        unique_together = ['certification', 'year', 'round', 'exam_type']

    def __str__(self):
        return f"{self.certification.name} {self.year}년 {self.round}회 {self.exam_type}"


class GisaSubject(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, verbose_name='자격증')
    name = models.CharField('과목명', max_length=100)
    order = models.IntegerField('과목순서', default=1)

    class Meta:
        verbose_name = '과목'
        verbose_name_plural = '과목'
        ordering = ['certification', 'order']
        unique_together = ['certification', 'name']

    def __str__(self):
        return f"[{self.certification.name}] {self.order}. {self.name}"


def _gisa_question_img_path(instance, filename):
    """cert_id/year-round/ 하위에 저장하여 파일명 충돌 방지."""
    import os
    ext = os.path.splitext(filename)[1] or '.png'
    cert_id = instance.exam.certification_id
    year = instance.exam.year
    rnd = instance.exam.round
    return f'gisa/questions/c{cert_id}/{year}-{rnd}/{filename}'


class GisaQuestion(models.Model):
    ANSWER_CHOICES = [
        ('0', '미확인'),
        ('1', '①'), ('2', '②'), ('3', '③'), ('4', '④'),
    ]

    exam = models.ForeignKey(GisaExam, on_delete=models.CASCADE, verbose_name='시험')
    subject = models.ForeignKey(GisaSubject, on_delete=models.CASCADE, verbose_name='과목')
    number = models.IntegerField('문항번호')
    text = models.TextField('문제')
    choice_1 = models.TextField('보기①')
    choice_2 = models.TextField('보기②')
    choice_3 = models.TextField('보기③')
    choice_4 = models.TextField('보기④')
    text_image = models.ImageField('문제 이미지', upload_to=_gisa_question_img_path, blank=True)
    choice_1_image = models.ImageField('보기① 이미지', upload_to=_gisa_question_img_path, blank=True)
    choice_2_image = models.ImageField('보기② 이미지', upload_to=_gisa_question_img_path, blank=True)
    choice_3_image = models.ImageField('보기③ 이미지', upload_to=_gisa_question_img_path, blank=True)
    choice_4_image = models.ImageField('보기④ 이미지', upload_to=_gisa_question_img_path, blank=True)
    answer = models.CharField('정답', max_length=10, choices=ANSWER_CHOICES, default='0')
    explanation = models.TextField('정답 설명', blank=True)
    choice_1_exp = models.TextField('보기① 해설', blank=True)
    choice_2_exp = models.TextField('보기② 해설', blank=True)
    choice_3_exp = models.TextField('보기③ 해설', blank=True)
    choice_4_exp = models.TextField('보기④ 해설', blank=True)
    freq_tier = models.PositiveSmallIntegerField(
        '빈출 등급', default=0, db_index=True,
        help_text='1~5 (5가 최다 빈출). 0은 미산정 — 별표를 표시하지 않는다.')
    created_by_name = models.CharField('등록자', max_length=50, blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True, null=True)

    class Meta:
        verbose_name = '기출문제'
        verbose_name_plural = '기출문제'
        ordering = ['exam', 'number']
        unique_together = ['exam', 'number']

    def __str__(self):
        return f"[{self.exam} {self.subject.name}] {self.number}번"


class GisaTextbook(models.Model):
    """기사시험 교재(핵심정리) 마크다운 콘텐츠 - 과목별 1건"""
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, verbose_name='자격증')
    subject = models.ForeignKey(GisaSubject, on_delete=models.CASCADE, verbose_name='과목')
    content = models.TextField('마크다운 내용')
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '교재'
        verbose_name_plural = '교재'
        unique_together = ['certification', 'subject']

    def __str__(self):
        return f"[{self.certification.name}] {self.subject.name} 핵심정리"


class GisaGlossary(models.Model):
    """기사시험 용어집 - 자격증×과목별 용어와 설명"""
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, verbose_name='자격증')
    subject = models.ForeignKey(GisaSubject, on_delete=models.CASCADE, verbose_name='과목')
    term = models.CharField('용어', max_length=200)
    description = models.TextField('설명', blank=True)

    class Meta:
        verbose_name = '용어'
        verbose_name_plural = '용어집'
        ordering = ['subject__order', 'term']
        unique_together = ['certification', 'subject', 'term']

    def __str__(self):
        return f"[{self.certification.name}/{self.subject.name}] {self.term}"


class GisaAttempt(models.Model):
    MODE_CHOICES = [
        ('exam', '풀이모드'),
        ('mock', '모의고사'),
        ('wrong_retry', '오답재풀이'),
        ('wrong_review', '오답복습'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    question = models.ForeignKey(GisaQuestion, on_delete=models.CASCADE, verbose_name='문제')
    selected = models.CharField('선택한 답', max_length=10, default='0')
    is_correct = models.BooleanField('정답여부')
    mode = models.CharField('풀이유형', max_length=20, choices=MODE_CHOICES, default='exam')
    session_id = models.CharField('세션ID', max_length=36, blank=True, default='')
    created_at = models.DateTimeField('풀이시각', auto_now_add=True)

    class Meta:
        verbose_name = '풀이기록'
        verbose_name_plural = '풀이기록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.question} ({'O' if self.is_correct else 'X'})"


class GisaStudyLog(models.Model):
    """학습모드(기출학습)에서 문항을 풀어본 기록. 진도율 산출용.

    선지를 고른 시점에 1건 기록한다(같은 페이지에서 같은 문항은 1회).
    여러 번 학습하면 누적되므로 진도율이 100%를 넘을 수 있다.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    question = models.ForeignKey(GisaQuestion, on_delete=models.CASCADE, verbose_name='문제')
    created_at = models.DateTimeField('학습시각', auto_now_add=True)

    class Meta:
        verbose_name = '학습기록'
        verbose_name_plural = '학습기록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'question']),
        ]

    def __str__(self):
        return f"{self.user} - {self.question} @ {self.created_at:%Y-%m-%d %H:%M}"


class MockGeneration(models.Model):
    """사용자·과목별 모의고사 세대 추적.
    한 과목의 모든 문제를 모의고사로 다 풀면 generation +1 후 다시 시작.
    같은 세대 안에서는 이전에 낸 문제는 다시 안 나옴.
    전체 모의고사·부분 과목 모의고사 모두 과목별로 독립 추적.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_generations', verbose_name='사용자')
    subject = models.ForeignKey(GisaSubject, on_delete=models.CASCADE, related_name='mock_generations', verbose_name='과목')
    generation = models.IntegerField('세대', default=1)
    seen_question_ids = models.JSONField('이번 세대에 출제된 문제 ID', default=list)
    updated_at = models.DateTimeField('최종 갱신', auto_now=True)

    class Meta:
        verbose_name = '모의고사 세대'
        verbose_name_plural = '모의고사 세대'
        unique_together = [('user', 'subject')]

    def __str__(self):
        return f"{self.user.username} · {self.subject.name} (세대 {self.generation}, {len(self.seen_question_ids)}문제 누적)"


def _essay_question_img_path(instance, filename):
    """실기 필답형 문항 이미지 경로. 자격증·출처별로 분리."""
    import os
    ext = os.path.splitext(filename)[1] or '.png'
    cert_id = instance.certification_id
    return f'gisa/essay/c{cert_id}/{instance.source}/{filename}'


class GisaEssayQuestion(models.Model):
    """실기 필답형 문항 (주관식).

    예상문제(source='예상')는 영역별 학습용, 기출(source='기출')은 회차별 실전용.
    답은 채점 포인트 단위인 answer_items(리스트)로 저장하며, 표·계산식처럼
    항목으로 쪼갤 수 없는 답은 answer_text에 둔다.
    """
    SOURCE_CHOICES = [
        ('예상', '예상문제'),
        ('기출', '기출문제'),
    ]
    TYPE_CHOICES = [
        ('열거', '열거형'),
        ('서술', '서술형'),
        ('단답', '단답형'),
        ('빈칸', '빈칸형'),
        ('계산', '계산형'),
        ('표그림', '표·그림형'),
    ]

    certification = models.ForeignKey(
        Certification, on_delete=models.CASCADE,
        related_name='essay_questions', verbose_name='자격증')
    source = models.CharField('출처', max_length=10, choices=SOURCE_CHOICES, default='기출')
    section = models.CharField('영역', max_length=30, blank=True,
                               help_text='예상문제의 소절명(생태학·법규 등). 기출은 "기출"')
    year = models.IntegerField('출제연도', null=True, blank=True)
    round = models.IntegerField('회차', null=True, blank=True)
    number = models.IntegerField('문항번호')

    qtype = models.CharField('유형', max_length=10, choices=TYPE_CHOICES, default='서술')
    text = models.TextField('문제')
    text_image = models.ImageField('문제 이미지', upload_to=_essay_question_img_path, blank=True)
    answer_items = models.JSONField('답 항목', default=list, blank=True,
                                    help_text='채점 포인트 단위 리스트')
    answer_text = models.TextField('답 서술', blank=True,
                                   help_text='표·계산식 등 항목화하기 어려운 답')
    answer_image = models.ImageField('답 이미지', upload_to=_essay_question_img_path, blank=True)
    reference = models.TextField('해설', blank=True,
                                 help_text='법조문·지침·배경 설명 등. 채점에는 쓰지 않고 학습용으로 노출')
    reference_image = models.ImageField('해설 이미지', upload_to=_essay_question_img_path, blank=True)

    points = models.FloatField('배점', default=3,
                               help_text='기출은 회차 합계가 45점이 되도록 0.5점 단위로 정규화')
    rubric = models.JSONField('채점 기준표', default=list, blank=True,
                              help_text='[{point, keywords[], score}] 형식. 비어 있으면 answer_items로 자동 생성')
    std_major = models.PositiveSmallIntegerField('출제기준 주요항목', default=0,
                                                 help_text='1~8. 0은 미분류')
    std_sub = models.PositiveSmallIntegerField('출제기준 세부항목', default=0)

    # 같은 주제가 표현만 바꿔 되풀이 출제되므로, 주제 단위로 묶어 빈도를 센다.
    # analyze_essay_freq.py 가 군집을 만들고 tag_essay_frequency 가 여기에 쓴다.
    topic_key = models.CharField('주제 키', max_length=64, blank=True, db_index=True,
                                 help_text='같은 주제로 묶인 문항이 공유하는 식별자')
    freq_rounds = models.PositiveSmallIntegerField(
        '출제 회차 수', default=0,
        help_text='이 주제가 출제된 회차 수. 1이면 한 번만 나온 주제')
    freq_note = models.CharField('출제 이력', max_length=200, blank=True,
                                 help_text='이 주제가 나온 회차 목록')
    notes = models.TextField('판독 메모', blank=True,
                             help_text='원문 오식 등. 관리자만 확인')

    created_at = models.DateTimeField('등록일', auto_now_add=True, null=True)

    class Meta:
        verbose_name = '실기 필답 문항'
        verbose_name_plural = '실기 필답 문항'
        ordering = ['source', 'section', '-year', '-round', 'number']
        unique_together = ['certification', 'source', 'section', 'year', 'round', 'number']
        indexes = [
            models.Index(fields=['certification', 'source']),
            models.Index(fields=['certification', 'year', 'round']),
        ]

    def __str__(self):
        if self.source == '기출':
            return f"[{self.certification.name} 실기] {self.year}-{self.round} {self.number}번"
        return f"[{self.certification.name} 실기] {self.section} {self.number}번"

    @property
    def label(self):
        """화면에 표시할 출처 라벨."""
        if self.source == '기출':
            return f"{self.year}년 {self.round}회"
        return self.section

    def build_rubric(self):
        """저장된 rubric이 없으면 answer_items로 균등 배분 기준표를 만든다."""
        if self.rubric:
            return self.rubric
        items = self.answer_items or []
        if not items:
            return [{'point': (self.answer_text or '')[:200], 'score': self.points}]
        base = self.points / len(items)
        return [{'point': it, 'score': round(base, 2)} for it in items]


class GisaEssaySession(models.Model):
    """필답형 응시 세션 (회차 단위 또는 영역 학습 단위)."""
    MODE_CHOICES = [
        ('online', '온라인 입력'),
        ('paper', '시험지 사진'),
    ]
    STATUS_CHOICES = [
        ('progress', '진행중'),
        ('grading', '채점중'),
        ('done', '채점완료'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='essay_sessions', verbose_name='사용자')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, verbose_name='자격증')
    source = models.CharField('출처', max_length=10, default='기출')
    section = models.CharField('영역', max_length=30, blank=True)
    year = models.IntegerField('출제연도', null=True, blank=True)
    round = models.IntegerField('회차', null=True, blank=True)

    mode = models.CharField('입력방식', max_length=10, choices=MODE_CHOICES, default='online')
    status = models.CharField('상태', max_length=10, choices=STATUS_CHOICES, default='progress')
    paper_code = models.CharField('시험지 코드', max_length=12, blank=True, db_index=True,
                                 help_text='인쇄 시험지 QR에 담기는 세션 식별 코드')

    total_points = models.PositiveSmallIntegerField('총 배점', default=45)
    score = models.FloatField('획득 점수', default=0)
    started_at = models.DateTimeField('시작', auto_now_add=True)
    submitted_at = models.DateTimeField('제출', null=True, blank=True)

    class Meta:
        verbose_name = '필답 응시'
        verbose_name_plural = '필답 응시'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.label} ({self.score}/{self.total_points})"

    @property
    def label(self):
        if self.source == '기출':
            return f"{self.year}년 {self.round}회"
        return self.section or '학습'

    @property
    def percent(self):
        if not self.total_points:
            return 0
        return round(self.score / self.total_points * 100, 1)

    @property
    def practical_estimate(self):
        """필답 점수를 실기 합격선(합계 60점) 기준으로 환산.

        작업형 55점 중 몇 점을 받아야 합격인지 알려준다.
        """
        need = 60 - self.score
        if need <= 0:
            return 0
        return round(need, 1)


class GisaEssayAttempt(models.Model):
    """필답형 문항별 답안과 채점 결과."""
    session = models.ForeignKey(GisaEssaySession, on_delete=models.CASCADE,
                                related_name='attempts', verbose_name='응시')
    question = models.ForeignKey(GisaEssayQuestion, on_delete=models.CASCADE, verbose_name='문항')

    answer_text = models.TextField('제출 답안', blank=True)
    transcribed_text = models.TextField('사진 판독 원문', blank=True,
                                        help_text='손글씨 판독 결과. 사용자가 수정하면 answer_text에 확정본이 들어간다')
    transcribe_confirmed = models.BooleanField('판독 확인', default=False)

    ai_score = models.FloatField('AI 채점 점수', null=True, blank=True)
    final_score = models.FloatField('최종 점수', null=True, blank=True,
                                    help_text='사용자가 조정한 값. 없으면 ai_score를 쓴다')
    feedback = models.JSONField('채점 상세', default=dict, blank=True,
                                help_text='{points: [{point, matched, comment}], summary: str}')
    graded_at = models.DateTimeField('채점 시각', null=True, blank=True)
    created_at = models.DateTimeField('작성 시각', auto_now_add=True)

    class Meta:
        verbose_name = '필답 답안'
        verbose_name_plural = '필답 답안'
        ordering = ['question__number']
        unique_together = ['session', 'question']

    def __str__(self):
        return f"{self.session.user.username} · {self.question} ({self.score}점)"

    @property
    def score(self):
        if self.final_score is not None:
            return self.final_score
        return self.ai_score or 0

    @property
    def is_perfect(self):
        return self.score >= self.question.points


def _essay_upload_path(instance, filename):
    import os
    ext = os.path.splitext(filename)[1] or '.jpg'
    return f'gisa/essay_uploads/{instance.session.user_id}/{instance.session_id}/p{instance.page_no}{ext}'


class GisaEssayUpload(models.Model):
    """시험지 사진 업로드 (paper 모드)."""
    session = models.ForeignKey(GisaEssaySession, on_delete=models.CASCADE,
                                related_name='uploads', verbose_name='응시')
    page_no = models.PositiveSmallIntegerField('페이지', default=1)
    image = models.ImageField('사진', upload_to=_essay_upload_path)
    transcribed = models.BooleanField('판독 완료', default=False)
    uploaded_at = models.DateTimeField('업로드', auto_now_add=True)

    class Meta:
        verbose_name = '시험지 사진'
        verbose_name_plural = '시험지 사진'
        ordering = ['session', 'page_no']
        unique_together = ['session', 'page_no']

    def __str__(self):
        return f"{self.session} p{self.page_no}"


class CertificationViewLog(models.Model):
    """자격증 상세 페이지(certification_detail) 진입 기록.
    사용자가 어느 자격증의 어느 탭을 언제 봤는지 추적.
    """
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='view_logs', verbose_name='자격증')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certification_views', verbose_name='사용자')
    tab = models.CharField('탭', max_length=20, blank=True, default='')
    viewed_at = models.DateTimeField('시각', auto_now_add=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=300, blank=True)

    class Meta:
        verbose_name = '자격증 페이지 조회'
        verbose_name_plural = '자격증 페이지 조회'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['certification', 'tab', 'viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed {self.certification.name}[{self.tab}] @ {self.viewed_at:%Y-%m-%d %H:%M}"
