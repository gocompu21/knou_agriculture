from django import forms

from .models import Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['department', 'name', 'grade', 'semester', 'category']
        widgets = {
            'department': forms.TextInput(attrs={'placeholder': '농학과'}),
            'name': forms.TextInput(attrs={'placeholder': '과목명을 입력하세요'}),
        }
