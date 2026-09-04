# -*- coding: utf-8 -*-
"""통일한 답을 서버에 옮긴다.

export : 로컬에서 통일된 문항의 답을 뽑아 _essay_unify_deploy.json 생성
load   : 서버에서 그 파일을 읽어 반영

자격증 pk 가 로컬 6 / 서버 3 으로 다르므로 (year, round, number) 로 찾는다.
"""
import io
import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

FILE = '_essay_unify_deploy.json'


def export():
    """통일 결과 파일에 적힌 문항들의 현재 답을 뽑는다."""
    keys = []
    for p in ('unified_b1.json', 'unified_b2.json', 'unified_b3.json'):
        if not os.path.exists(p):
            continue
        for r in json.load(io.open(p, encoding='utf-8')):
            keys += r.get('apply') or []

    out = []
    for y, rd, num in keys:
        q = Q.objects.filter(source='기출', year=y, round=rd,
                             number=num).first()
        if not q:
            continue
        out.append({
            'year': y, 'round': rd, 'number': num,
            'answer_items': q.answer_items or [],
            'answer_text': q.answer_text or '',
        })
    io.open(FILE, 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(f'export {len(out)}문항 → {FILE}')


def load():
    rows = json.load(io.open(FILE, encoding='utf-8'))
    n = miss = 0
    for r in rows:
        q = Q.objects.filter(source='기출', year=r['year'],
                             round=r['round'], number=r['number']).first()
        if not q:
            miss += 1
            continue
        if q.answer_items == r['answer_items'] and \
                (q.answer_text or '') == r['answer_text']:
            continue
        q.answer_items = r['answer_items']
        q.answer_text = r['answer_text']
        q.save(update_fields=['answer_items', 'answer_text'])
        n += 1
    print(f'load {n}문항 반영 (파일 {len(rows)}건, 못 찾음 {miss})')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'export':
        export()
    elif cmd == 'load':
        load()
    else:
        print('사용법: python deploy_essay_unify.py export|load')
