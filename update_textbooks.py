#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""업데이트된 쪽집게 노트 마크다운을 DB에 반영하는 스크립트."""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from gisa.models import GisaTextbook

subjects = {
    1: '식물병리학',
    2: '농림해충학',
    3: '재배학원론',
    4: '농약학',
    5: '잡초방제학',
}

for tb_pk, subj_name in subjects.items():
    filepath = f'data/tb_{tb_pk}_{subj_name}_updated.md'
    if not os.path.exists(filepath):
        print(f'[SKIP] {filepath} 없음')
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    tb = GisaTextbook.objects.get(pk=tb_pk)
    old_lines = tb.content.count('\n')
    tb.content = content
    tb.save()
    new_lines = content.count('\n')
    print(f'[OK] {subj_name}: {old_lines}줄 → {new_lines}줄 (+{new_lines - old_lines}줄)')

print('\nDB 업데이트 완료!')
