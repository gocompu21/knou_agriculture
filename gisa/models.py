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


# 회차(연도·회)로 시험지를 꾸리는 출처. 나머지(예상·적산)는 영역(section)으로 묶는다.
ESSAY_ROUND_SOURCES = ('기출', '학원')


class GisaEssayQuestion(models.Model):
    """실기 필답형 문항 (주관식).

    예상문제(source='예상')는 영역별 학습용, 기출(source='기출')은 회차별 실전용.
    답은 채점 포인트 단위인 answer_items(리스트)로 저장하며, 표·계산식처럼
    항목으로 쪼갤 수 없는 답은 answer_text에 둔다.
    """
    SOURCE_CHOICES = [
        ('예상', '예상문제'),
        ('기출', '기출문제'),
        # 회차가 밝혀지지 않은 문제 모음. 조경 실기의 구유형(2022년 이전) 적산
        # 기출이 여기 들어간다 — 회차별 시험지를 꾸릴 수 없어 영역 단위로 푼다.
        ('적산', '구유형 적산'),
        # 학원에서 치른 예상 모의고사. 기출처럼 회차(연도·회)로 시험지를 꾸린다.
        ('학원', '학원예상시험'),
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
    # 학습 편의를 위해 number 를 주제순으로 다시 매기므로, 실제 시험지의 번호를
    # 여기에 남긴다. 다른 수험 자료와 대조하거나 원본을 확인할 때 필요하다.
    orig_number = models.IntegerField('원본 문항번호', null=True, blank=True)

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

    # 출제기준 8항목은 실무 수행 순서(구상→기반환경→…→종합평가)라, 학술 지식을
    # 묻는 기출과 잘 맞지 않는다. 실제로 무엇을 묻는지로 따로 나눠 학습 순서를
    # 잡는다. 번호도 이 순서로 다시 매긴다.
    TOPIC_CHOICES = [
        (1, '생태학 기초'),
        (2, '경관생태'),
        (3, '생태조사·분석'),
        (4, '복원 계획·설계'),
        (5, '기반환경 복원'),
        (6, '생태시설물·현장관리'),
        (7, '환경영향평가'),
        (8, '법규·제도'),
    ]
    # **분류 이름은 자격증마다 다르다** — `gisa/essay_topics.py` 의 TOPIC_GROUPS 가
    # 갖고 있다. 위의 TOPIC_CHOICES 는 자연생태복원 것이고 renumber_essay.py 가
    # 아직 쓰므로 남겨 두지만, 식물보호는 분류가 11개라 8을 넘는 값이 들어간다.
    # 그래서 필드에 choices 를 걸지 않는다 — 걸어 두면 관리자 화면에서 9~11번이
    # 빈칸으로 보이고 폼 검증에 걸린다.
    topic_group = models.PositiveSmallIntegerField(
        '주제 분류', default=0,
        help_text='0은 미분류. 이름은 essay_topics.TOPIC_GROUPS 가 자격증별로 갖는다. '
                  '회차 내 문항 순서를 이 값으로 매긴다')

    # 같은 주제가 표현만 바꿔 되풀이 출제되므로, 주제 단위로 묶어 빈도를 센다.
    # analyze_essay_freq.py 가 군집을 만들고 tag_essay_frequency 가 여기에 쓴다.
    topic_key = models.CharField('주제 키', max_length=64, blank=True, db_index=True,
                                 help_text='같은 주제로 묶인 문항이 공유하는 식별자')
    freq_rounds = models.PositiveSmallIntegerField(
        '출제 회차 수', default=0,
        help_text='이 주제가 출제된 시험지 수. 기사·산업기사를 함께 묶는 자격증은 '
                  '묶음 전체의 시험지를 센다(식물보호는 9가 아니라 18이 모수)')
    freq_note = models.CharField('출제 이력', max_length=200, blank=True,
                                 help_text='이 주제가 나온 회차 목록')
    # 실기에 1회만 나왔지만 필기에서 자주 다뤄진 주제는 재출제 유력 후보다.
    # 최근 3개 회차 신규 주제를 역검증하니 81%가 필기 빈출 영역에서 나왔다.
    # tag_written_freq.py 가 주제어의 필기 등장 횟수를 계산해 채운다.
    written_freq = models.PositiveSmallIntegerField(
        '필기 등장 횟수', default=0,
        help_text='이 문항 주제어가 필기 기출에 등장한 횟수')
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
        if self.source == '학원':
            return f"[{self.certification.name} 실기] 학원예상 {self.round}회 {self.number}번"
        return f"[{self.certification.name} 실기] {self.section} {self.number}번"

    @property
    def label(self):
        """화면에 표시할 출처 라벨."""
        if self.source == '기출':
            return f"{self.year}년 {self.round}회"
        if self.source == '학원':
            return f"학원예상 {self.round}회"
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
        ('quiz', '퀴즈'),
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
        if self.source == '모의':
            # section 에 범위가 들어 있다 ("모의 2020~2026 · 3분류"). 없으면 기본 라벨
            s = (self.section or '').strip()
            return s.replace('모의', '모의고사', 1) if s and s != '모의고사' else '모의고사'
        if self.source == '오답':
            return '오답 재풀이'
        if self.source == '학원':
            return f"학원예상 {self.round}회"
        return self.section or '학습'

    @property
    def percent(self):
        if not self.total_points:
            return 0
        return round(self.score / self.total_points * 100, 1)

    @property
    def practical_estimate(self):
        """필답 점수를 실기 합격선(합계 60점) 기준으로 환산.

        작업형에서 몇 점을 더 받아야 합격인지 알려준다. 필답과 작업형을 합쳐
        100점이므로 자격증마다 배점이 갈려도(45+55, 40+60) 셈은 같다.

        **작업형이 없는 자격증에서는 None 이다.** 식물보호산업기사는 실기가
        필답형 단독이라 '작업형에서 N점 더'라는 말 자체가 성립하지 않는다.
        화면은 None 이면 그 칸을 감춘다.
        """
        from .essay_examinfo import exam_info
        info = exam_info(self.certification.name)
        if info and not info.get('work_points'):
            return None
        need = 60 - self.score
        if need <= 0:
            return 0
        return round(need, 1)

    @property
    def has_work_stage(self):
        """이 자격증 실기에 작업형이 있나. 개요가 없으면 있다고 본다(종전 동작)."""
        from .essay_examinfo import exam_info
        info = exam_info(self.certification.name)
        return bool(info.get('work_points')) if info else True


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
    # 오답노트 "노트 X" — 사용자가 이 답안을 오답노트에서 뺐다. 문항의 가장 최근
    # 답안에만 의미가 있다(나중에 다시 틀리면 새 답안이 최근이 되어 다시 나온다)
    wrong_dismissed = models.BooleanField('오답노트 제외', default=False)
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


def _essay_flat_path(instance, filename):
    return f'gisa/essay_uploads/{instance.session.user_id}/{instance.session_id}/p{instance.page_no}_flat.jpg'


class GisaEssayUpload(models.Model):
    """시험지 사진 업로드 (paper 모드).

    올리자마자 사진을 A4 로 곧게 펴(essay_rectify) flat_image 에 두고, 판독은
    편 사진으로 한다. 원본(image)은 그대로 둔다 — 보정이 잘못됐을 때 되짚을 수 있게.
    """
    session = models.ForeignKey(GisaEssaySession, on_delete=models.CASCADE,
                                related_name='uploads', verbose_name='응시')
    page_no = models.PositiveSmallIntegerField('페이지', default=1)
    image = models.ImageField('사진', upload_to=_essay_upload_path)
    flat_image = models.ImageField('편 사진', upload_to=_essay_flat_path, blank=True)
    # marker(모서리 마커) / edge(종이 가장자리) / none(펴지 못함) / 빈 값(보정 전)
    flat_method = models.CharField('보정 방법', max_length=10, blank=True)
    flat_info = models.JSONField('보정 정보', default=dict, blank=True)
    transcribed = models.BooleanField('판독 완료', default=False)
    uploaded_at = models.DateTimeField('업로드', auto_now_add=True)

    class Meta:
        verbose_name = '시험지 사진'
        verbose_name_plural = '시험지 사진'
        ordering = ['session', 'page_no']
        unique_together = ['session', 'page_no']

    def __str__(self):
        return f"{self.session} p{self.page_no}"


class GisaEssayNote(models.Model):
    """실기 필답 학습 자료 (빈출 주제 정리 등).

    GisaTextbook 은 필기 과목(GisaSubject)에 묶여 있어 실기에는 맞지 않는다.
    실기는 과목이 하나뿐이므로 자격증에 바로 달고, 자료 종류만 slug 로 나눈다.
    """
    certification = models.ForeignKey(
        Certification, on_delete=models.CASCADE,
        related_name='essay_notes', verbose_name='자격증')
    slug = models.SlugField('식별자', max_length=40,
                            help_text='freq58 처럼 자료를 구분하는 이름')
    title = models.CharField('제목', max_length=100)
    summary = models.CharField('한 줄 설명', max_length=200, blank=True)
    content = models.TextField('마크다운 내용')
    order = models.PositiveSmallIntegerField('표시 순서', default=0)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '실기 학습자료'
        verbose_name_plural = '실기 학습자료'
        ordering = ['order', 'slug']
        unique_together = ['certification', 'slug']

    def __str__(self):
        return f"[{self.certification.name}] {self.title}"


# ------------------------------------------------------------------ 작업형(도면)

def _drawing_img_path(instance, filename):
    t = instance.task
    return f'gisa/drawing/c{t.certification_id}/{t.year or 0}-{t.round or 0}/{filename}'


class GisaDrawingTask(models.Model):
    """실기 작업형 — 회차별로 출제된 도면 설계 과제.

    조경(산업)기사 실기는 필답형과 작업형(도면)으로 나뉜다. 필답형은 문항 단위라
    GisaEssayQuestion 에 담았지만, 작업형은 **한 회차에 과제 하나**(대상지 + 요구 도면
    몇 장)라 따로 둔다. 목록 한 줄이 곧 "그 회차에 무엇을 그렸나"다.

    처음에는 연도별 출제 목록(대상지·요구 도면·축척)만 채우고, 요구조건 원문·현황도·
    모범 도면·해설은 자료가 생기는 대로 붙인다 — 빈 칸은 화면에서 감춘다.
    """
    certification = models.ForeignKey(
        Certification, on_delete=models.CASCADE,
        related_name='drawing_tasks', verbose_name='자격증')
    year = models.IntegerField('출제연도')
    round = models.IntegerField('회차', null=True, blank=True)
    title = models.CharField('과제(대상지)', max_length=100,
                             help_text='예: 근린 공원, 주택 정원, 옥상')
    # 같은 번호면 같은 도면이 되나온 것이다(근린 공원 323·360·412 는 서로 다른 도면)
    code = models.CharField('도면 번호', max_length=10, blank=True,
                            help_text='수험 자료의 도면 번호 — 예: 412')
    pass_rate = models.FloatField('합격률(%)', null=True, blank=True)
    drawings = models.JSONField('요구 도면', default=list, blank=True,
                                help_text='["설계개념도", "배식설계도", "단면도"] 처럼')
    scale = models.CharField('축척', max_length=40, blank=True)
    site_area = models.CharField('대상지 규모', max_length=60, blank=True)
    note = models.CharField('비고', max_length=200, blank=True)
    conditions = models.TextField('요구조건', blank=True, help_text='마크다운')
    commentary = models.TextField('해설', blank=True, help_text='마크다운')
    order = models.PositiveSmallIntegerField('같은 회차 안 순서', default=0)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '실기 작업형 과제'
        verbose_name_plural = '실기 작업형 과제'
        ordering = ['-year', '-round', 'order']
        unique_together = ['certification', 'year', 'round']

    def __str__(self):
        r = f'{self.round}회 ' if self.round else ''
        return f"[{self.certification.name}] {self.year}년 {r}{self.title}"


class GisaDrawingImage(models.Model):
    """작업형 과제에 붙는 그림 — 현황도, 모범 답안 도면, 참고 그림."""
    KIND_CHOICES = [
        ('site', '현황도'),
        ('answer', '모범 도면'),
        ('ref', '참고'),
    ]
    task = models.ForeignKey(GisaDrawingTask, on_delete=models.CASCADE,
                             related_name='images', verbose_name='과제')
    kind = models.CharField('종류', max_length=10, choices=KIND_CHOICES, default='answer')
    image = models.ImageField('그림', upload_to=_drawing_img_path)
    caption = models.CharField('설명', max_length=100, blank=True)
    order = models.PositiveSmallIntegerField('순서', default=0)

    class Meta:
        verbose_name = '작업형 도면 그림'
        verbose_name_plural = '작업형 도면 그림'
        ordering = ['kind', 'order', 'id']

    def __str__(self):
        return f"{self.task} · {self.get_kind_display()} {self.caption}"


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


class PesticideCard(models.Model):
    """농약명 → 살충제·살균제·제초제 암기 카드 (92종).

    출처는 한울회 배포 `농약_DVD_기출.pptx`(2018~2023 기출 빈도). 농약명은
    **어미·어두가 계열을 말해 준다** — '-포스'·'-티온'은 유기인계 살충제,
    '-졸'·'-코나졸'은 살균제, '-클로르'·'-랄린'은 제초제 식이다. 그 단서가
    `hint` 이고, 단서로 못 가르는 것(폴펫·캡탄·디캄바 …)은 `whole=True` 로
    두어 화면이 '통암기'라고 알린다.

    **예외가 시험에 나온다** — 비알라포스와 피페로포스는 '-포스'인데 제초제다.
    그런 것은 `note` 에 적어 답을 고른 뒤 보여 준다.
    """
    CATEGORIES = [('살충제', '살충제'), ('살균제', '살균제'), ('제초제', '제초제')]

    no = models.IntegerField('일련번호', unique=True)
    name = models.CharField('농약명', max_length=60, unique=True)
    # ISO 일반명. 답 화면에 괄호로 곁들인다 — 실기 답안은 한글로 쓰지만
    # 어미 규칙은 영문 철자에서 온 것이라(-phos·-conazole·-chlor) 함께 보면 붙는다
    en_name = models.CharField('영문명', max_length=60, blank=True)
    category = models.CharField('구분', max_length=10, choices=CATEGORIES)
    hint = models.CharField('분류 단서', max_length=40, blank=True)
    whole = models.BooleanField('통암기', default=False,
                                help_text='어미·어두로 못 가르는 것')
    exam_count = models.IntegerField('출제수', default=0,
                                     help_text='2018~2023 기출 빈도')
    # 잡초 카드처럼 답을 고른 뒤 보여 주는 보충 정보. 계열을 알면 어미 규칙이
    # 왜 통하는지가 이어진다 — '-포스'가 살충제인 까닭이 유기인계이기 때문이다.
    family = models.CharField('계열', max_length=40, blank=True)
    action = models.CharField('작용', max_length=120, blank=True,
                              help_text='어떻게 듣는가 (침투이행·접촉·훈증 …)')
    target = models.CharField('주요 대상', max_length=120, blank=True)
    note = models.TextField('비고', blank=True)

    class Meta:
        verbose_name = '농약 암기카드'
        verbose_name_plural = '농약 암기카드'
        ordering = ['no']

    def __str__(self):
        return f'{self.no}. {self.name} ({self.category})'


class PesticideQuizAttempt(models.Model):
    """농약 카드 풀이 기록. **카드별 최신 기록이 틀리면 오답**이다.

    잡초 동정(WeedQuizAttempt)과 같은 규칙이다 — 기록을 쌓아 두고 마지막
    것만 보므로, 다시 풀어 맞히면 오답 목록에서 빠진다.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='pesticide_attempts', verbose_name='사용자')
    card = models.ForeignKey(PesticideCard, on_delete=models.CASCADE,
                             related_name='attempts', verbose_name='카드')
    selected = models.CharField('고른 답', max_length=10, blank=True)
    is_correct = models.BooleanField('정답 여부', default=False)
    created_at = models.DateTimeField('시각', auto_now_add=True)

    class Meta:
        verbose_name = '농약 카드 풀이'
        verbose_name_plural = '농약 카드 풀이'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'card', '-created_at'])]

    def __str__(self):
        return f'{self.user.username} {self.card.name} {"O" if self.is_correct else "X"}'


class PestCard(models.Model):
    """사진 → 해충 이름 암기 카드 (152종).

    출처는 한울회 배포 해충 슬라이드 152장(2022-V1). 슬라이드는 좌상단 해충명,
    우상단 설명, 그 아래 사진 여러 장으로 짜여 있어 — **사진 부분만 통째로**
    잘라 문제로 쓰고 이름과 설명은 답 화면에 보여 준다.

    사진을 낱장으로 가르지 않는 까닭은 실물을 보는 감각이 살기 때문이다.
    성충·유충·피해 사진이 한 화면에 있어야 그 해충을 안다.
    """
    GROUPS = [('농작물', '농작물'), ('수목', '수목')]

    no = models.IntegerField('일련번호', unique=True)
    slide = models.IntegerField('슬라이드 번호', unique=True)
    name = models.CharField('해충명', max_length=60, unique=True)
    group = models.CharField('구분', max_length=10, choices=GROUPS, blank=True)
    image = models.ImageField('사진', upload_to='pests/')
    desc = models.TextField('설명', blank=True)
    note = models.TextField('비고', blank=True)

    class Meta:
        verbose_name = '해충 암기카드'
        verbose_name_plural = '해충 암기카드'
        ordering = ['no']

    def __str__(self):
        return f'{self.no}. {self.name}'


class PestQuizAttempt(models.Model):
    """해충 카드 풀이 기록. 카드별 최신 기록이 틀리면 오답이다."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='pest_attempts', verbose_name='사용자')
    card = models.ForeignKey(PestCard, on_delete=models.CASCADE,
                             related_name='attempts', verbose_name='카드')
    selected = models.CharField('고른 답', max_length=60, blank=True)
    is_correct = models.BooleanField('정답 여부', default=False)
    created_at = models.DateTimeField('시각', auto_now_add=True)

    class Meta:
        verbose_name = '해충 카드 풀이'
        verbose_name_plural = '해충 카드 풀이'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'card', '-created_at'])]

    def __str__(self):
        return f'{self.user.username} {self.card.name} {"O" if self.is_correct else "X"}'
