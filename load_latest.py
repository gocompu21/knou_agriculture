"""최신기출 JSON을 update_or_create로 import하는 스크립트.

Usage:
    python load_latest.py 식물의학_latest.json
"""
import json, sys, os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from exam.models import Question
from main.models import Subject

if len(sys.argv) < 2:
    print("Usage: python load_latest.py <json_file>")
    sys.exit(1)

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

created_count = 0
updated_count = 0

for item in data:
    subject = Subject.objects.get(name=item["subject_name"])
    _, created = Question.objects.update_or_create(
        subject=subject,
        year=item["year"],
        number=item["number"],
        defaults={
            "text": item["text"],
            "choice_1": item["choice_1"],
            "choice_2": item["choice_2"],
            "choice_3": item["choice_3"],
            "choice_4": item["choice_4"],
            "answer": item["answer"],
            "explanation": item.get("explanation", ""),
            "choice_1_exp": item.get("choice_1_exp", ""),
            "choice_2_exp": item.get("choice_2_exp", ""),
            "choice_3_exp": item.get("choice_3_exp", ""),
            "choice_4_exp": item.get("choice_4_exp", ""),
        },
    )
    if created:
        created_count += 1
    else:
        updated_count += 1

print(f"완료: {created_count}개 신규, {updated_count}개 업데이트 (총 {len(data)}문항)")
