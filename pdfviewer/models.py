from django.conf import settings
from django.db import models


class UploadedPDF(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='uploaded_pdfs', verbose_name='업로더'
    )
    title = models.CharField('제목', max_length=200)
    file = models.FileField('PDF 파일', upload_to='pdfs/%Y/%m/')
    uploaded_at = models.DateTimeField('업로드일', auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'PDF 파일'
        verbose_name_plural = 'PDF 파일'

    def __str__(self):
        return self.title
