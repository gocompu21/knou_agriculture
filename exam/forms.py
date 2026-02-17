from django import forms

from .models import Exam


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['year', 'exam_type']
        widgets = {
            'year': forms.NumberInput(attrs={'placeholder': '2024', 'min': 2000, 'max': 2030}),
        }
