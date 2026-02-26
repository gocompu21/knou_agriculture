#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""쪽집게 노트 JSON을 DB에 import하는 스크립트 (EC2 배포용)."""
import json, os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import Certification, GisaSubject, GisaTextbook

if len(sys.argv) < 2:
    print('Usage: python load_textbooks.py <json_file>')
    sys.exit(1)

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    cert = Certification.objects.get(name=item['cert_name'], category=item['cert_category'])
    subject = GisaSubject.objects.get(certification=cert, name=item['subject_name'])
    tb, created = GisaTextbook.objects.update_or_create(
        certification=cert,
        subject=subject,
        defaults={'content': item['content']},
    )
    lines = item['content'].count('\n')
    print(f'{"생성" if created else "갱신"}: {item["subject_name"]} ({lines}줄)')

print(f'\n완료! {len(data)}개 교재 반영')
