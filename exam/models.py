from django.db import models
from django.conf import settings
from main.models import Subject


class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ('중간', '중간고사'),
        ('기말', '기말고사'),
        ('계절', '계절학기'),
    ]

    year = models.IntegerField('출제연도')
    exam_type = models.CharField('시험종류', max_length=10, choices=EXAM_TYPE_CHOICES)

    class Meta:
        verbose_name = '시험'
        verbose_name_plural = '시험'
        ordering = ['-year', 'exam_type']
        unique_together = ['year', 'exam_type']

    def __str__(self):
        return f"{self.year}년 {self.get_exam_type_display()}"


class Question(models.Model):
    ANSWER_CHOICES = [
        ('0', '미확인'),
        ('1', '①'), ('2', '②'), ('3', '③'), ('4', '④'),
        ('1,2', '①②'), ('1,3', '①③'), ('1,4', '①④'),
        ('2,3', '②③'), ('2,4', '②④'), ('3,4', '③④'),
        ('1,2,3', '①②③'), ('1,2,4', '①②④'),
        ('1,3,4', '①③④'), ('2,3,4', '②③④'),
        ('1,2,3,4', '①②③④'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='과목')
    year = models.IntegerField('출제연도')
    number = models.IntegerField('문항번호')
    text = models.TextField('문제')
    choice_1 = models.TextField('보기①')
    choice_2 = models.TextField('보기②')
    choice_3 = models.TextField('보기③')
    choice_4 = models.TextField('보기④')
    answer = models.CharField('정답', max_length=10, choices=ANSWER_CHOICES, default='0')
    choice_1_exp = models.TextField('보기① 해설', blank=True)
    choice_2_exp = models.TextField('보기② 해설', blank=True)
    choice_3_exp = models.TextField('보기③ 해설', blank=True)
    choice_4_exp = models.TextField('보기④ 해설', blank=True)
    explanation = models.TextField('정답 설명', blank=True)
    created_by_name = models.CharField('등록자', max_length=50, blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True, null=True)

    class Meta:
        verbose_name = '기출문제'
        verbose_name_plural = '기출문제'
        ordering = ['subject', 'year', 'number']
        unique_together = ['subject', 'year', 'number']

    def __str__(self):
        return f"[{self.subject.name} {self.year}] {self.number}번"


class Attempt(models.Model):
    MODE_CHOICES = [
        ('exam', '풀이모드'),
        ('mock', '모의고사'),
        ('wrong_retry', '오답재풀이'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='문제')
    selected = models.CharField('선택한 답', max_length=10, choices=Question.ANSWER_CHOICES, default='0')
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


class WeedCard(models.Model):
    """잡초 동정 카드 — 사진을 보고 이름을 맞히는 퀴즈용.

    원본은 교수 배포 '잡초방제학 카드' PDF(잡초 122종). q_image 는 이름을 가린
    쪽의 사진 부분, a_image 는 이름·메모·세밀화가 다 보이는 슬라이드 전체다.
    family~control 은 답 화면에 함께 보여 주는 보충 정보(직접 작성)이고,
    notes 는 슬라이드의 교수 메모(글자 층이 있는 카드만), exam_count 는
    슬라이드의 'N회 출제' 배지다. sketch_image 는 답 슬라이드에 붙어 있는
    교수 손그림만 떼어 낸 것으로, 답 화면의 식별 포인트 앞에 보여 준다.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='weed_cards', verbose_name='과목')
    order = models.PositiveIntegerField('순서', default=0)
    card_no = models.PositiveIntegerField('카드 번호')
    name = models.CharField('잡초명', max_length=50)
    family = models.CharField('과', max_length=50, blank=True, default='')
    life_form = models.CharField('생활형', max_length=50, blank=True, default='')
    habitat = models.CharField('발생지', max_length=100, blank=True, default='')
    features = models.TextField('식별 포인트', blank=True, default='')
    similar = models.TextField('유사종 구별', blank=True, default='')
    control = models.TextField('방제·비고', blank=True, default='')
    notes = models.TextField('교수 메모', blank=True, default='')
    exam_count = models.PositiveIntegerField('출제 횟수', default=0)
    q_image = models.ImageField('문제 사진', upload_to='weeds/', blank=True)
    a_image = models.ImageField('답 슬라이드', upload_to='weeds/', blank=True)
    sketch_image = models.ImageField('손그림', upload_to='weeds/', blank=True)

    class Meta:
        verbose_name = '잡초 카드'
        verbose_name_plural = '잡초 카드'
        ordering = ['subject', 'order']
        unique_together = [('subject', 'card_no')]

    def __str__(self):
        return f'{self.subject.name} #{self.card_no} {self.name}'


class WeedQuizAttempt(models.Model):
    """잡초 동정 퀴즈 풀이 기록. 카드별 최신 기록이 틀렸으면 오답으로 본다."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    card = models.ForeignKey(WeedCard, on_delete=models.CASCADE, related_name='attempts', verbose_name='카드')
    selected = models.ForeignKey(WeedCard, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='+', verbose_name='고른 카드')
    is_correct = models.BooleanField('정답 여부')
    created_at = models.DateTimeField('풀이 시각', auto_now_add=True)

    class Meta:
        verbose_name = '잡초 퀴즈 기록'
        verbose_name_plural = '잡초 퀴즈 기록'
        indexes = [models.Index(fields=['user', 'card', '-id'])]


class StudyNote(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='과목', related_name='study_notes')
    title = models.CharField('제목', max_length=200)
    content = models.TextField('내용')
    order = models.PositiveIntegerField('순서', default=0)
    created_at = models.DateTimeField('작성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '정리노트'
        verbose_name_plural = '정리노트'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.subject.name} - {self.title}"
