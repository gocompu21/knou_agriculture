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

    class Meta:
        verbose_name = '기출문제'
        verbose_name_plural = '기출문제'
        ordering = ['subject', 'year', 'number']
        unique_together = ['subject', 'year', 'number']

    def __str__(self):
        return f"[{self.subject.name} {self.year}] {self.number}번"


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='사용자')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='문제')
    selected = models.CharField('선택한 답', max_length=10, choices=Question.ANSWER_CHOICES, default='0')
    is_correct = models.BooleanField('정답여부')
    created_at = models.DateTimeField('풀이시각', auto_now_add=True)

    class Meta:
        verbose_name = '풀이기록'
        verbose_name_plural = '풀이기록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.question} ({'O' if self.is_correct else 'X'})"
