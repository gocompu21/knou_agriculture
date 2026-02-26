"""
기사시험 기출문제 JSON을 EC2 DB에 import하는 스크립트.
사용법: python load_gisa_exam.py data/gisa_2023_1.json
"""
import json
import os
import sys
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from gisa.models import Certification, GisaExam, GisaQuestion, GisaSubject


def main():
    if len(sys.argv) < 2:
        print('Usage: python load_gisa_exam.py <json_file>')
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    exam_info = data['exam']

    # Certification
    cert, _ = Certification.objects.get_or_create(
        name=exam_info['cert_name'],
        category=exam_info['cert_category'],
        defaults={'description': f'{exam_info["cert_name"]} {exam_info["cert_category"]} 자격증'},
    )

    # GisaExam
    exam_date = date.fromisoformat(exam_info['exam_date']) if exam_info.get('exam_date') else None
    exam, created = GisaExam.objects.update_or_create(
        certification=cert,
        year=exam_info['year'],
        round=exam_info['round'],
        exam_type=exam_info['exam_type'],
        defaults={'exam_date': exam_date},
    )
    print(f'시험 {"생성" if created else "기존"}: {exam}')

    # Questions
    created_count = 0
    updated_count = 0
    for q in data['questions']:
        subject = None
        if q.get('subject_name'):
            subject, _ = GisaSubject.objects.get_or_create(
                certification=cert,
                name=q['subject_name'],
                defaults={'order': 0},
            )

        _, was_created = GisaQuestion.objects.update_or_create(
            exam=exam,
            number=q['number'],
            defaults={
                'subject': subject,
                'text': q['text'],
                'choice_1': q['choice_1'],
                'choice_2': q['choice_2'],
                'choice_3': q['choice_3'],
                'choice_4': q['choice_4'],
                'answer': q['answer'],
                'explanation': q.get('explanation', ''),
                'choice_1_exp': q.get('choice_1_exp', ''),
                'choice_2_exp': q.get('choice_2_exp', ''),
                'choice_3_exp': q.get('choice_3_exp', ''),
                'choice_4_exp': q.get('choice_4_exp', ''),
            },
        )
        if was_created:
            created_count += 1
        else:
            updated_count += 1

    print(f'완료! 신규 {created_count}개, 갱신 {updated_count}개 (총 {len(data["questions"])}문제)')


if __name__ == '__main__':
    main()
