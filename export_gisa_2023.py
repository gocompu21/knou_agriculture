#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, django, json, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from gisa.models import GisaQuestion, GisaExam

exam = GisaExam.objects.get(pk=93)
qs = GisaQuestion.objects.filter(exam=exam).select_related('subject').order_by('number')
questions = []
for q in qs:
    questions.append({
        'subject_name': q.subject.name if q.subject else '',
        'number': q.number,
        'text': q.text,
        'choice_1': q.choice_1, 'choice_2': q.choice_2,
        'choice_3': q.choice_3, 'choice_4': q.choice_4,
        'answer': q.answer,
        'explanation': q.explanation or '',
        'choice_1_exp': q.choice_1_exp or '',
        'choice_2_exp': q.choice_2_exp or '',
        'choice_3_exp': q.choice_3_exp or '',
        'choice_4_exp': q.choice_4_exp or '',
    })
data = {
    'exam': {
        'cert_name': exam.certification.name,
        'cert_category': exam.certification.category,
        'year': exam.year,
        'round': exam.round,
        'exam_type': exam.exam_type,
        'exam_date': str(exam.exam_date) if exam.exam_date else None,
    },
    'questions': questions,
}
with open('data/gisa_2023_1.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
has_exp = sum(1 for q in questions if q['explanation'])
print(f'{len(questions)}문제 추출 완료 (해설: {has_exp}개)')
