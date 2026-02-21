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
    answer = models.CharField('정답', max_length=10, choices=ANSWER_CHOICES, default='0')
    explanation = models.TextField('정답 설명', blank=True)
    choice_1_exp = models.TextField('보기① 해설', blank=True)
    choice_2_exp = models.TextField('보기② 해설', blank=True)
    choice_3_exp = models.TextField('보기③ 해설', blank=True)
    choice_4_exp = models.TextField('보기④ 해설', blank=True)

    class Meta:
        verbose_name = '기출문제'
        verbose_name_plural = '기출문제'
        ordering = ['exam', 'number']
        unique_together = ['exam', 'number']

    def __str__(self):
        return f"[{self.exam} {self.subject.name}] {self.number}번"


class GisaAttempt(models.Model):
    MODE_CHOICES = [
        ('exam', '풀이모드'),
        ('mock', '모의고사'),
        ('wrong_retry', '오답재풀이'),
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
