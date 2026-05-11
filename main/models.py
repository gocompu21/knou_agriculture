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
    """PDF 자료(SubjectMaterial) 열람 기록.
    material_view 페이지 진입 시 한 행 저장. 동일 사용자가 여러 번 열면 행도 늘어남.
    """
    material = models.ForeignKey(SubjectMaterial, on_delete=models.CASCADE, related_name='open_logs', verbose_name='자료')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='material_opens', verbose_name='사용자')
    opened_at = models.DateTimeField('열람 시각', auto_now_add=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=300, blank=True)

    class Meta:
        verbose_name = 'PDF 열람 기록'
        verbose_name_plural = 'PDF 열람 기록'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['material', 'user']),
            models.Index(fields=['opened_at']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.material.title[:20]} @ {self.opened_at:%Y-%m-%d %H:%M}"
