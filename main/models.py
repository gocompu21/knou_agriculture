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
