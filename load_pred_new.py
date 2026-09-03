# -*- coding: utf-8 -*-
"""자체 예상문제를 검증하고 GisaEssayQuestion(source='예상')에 넣는다.

필기 빈출인데 실기 미출제인 주제로 직접 만든 문항이다. 교재 예상문제
(적중 4%, 삭제됨)와 달리 데이터 근거가 있고 저작권 부담도 없다.
"""
import argparse
import glob
import json
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import Certification, GisaEssayQuestion as Q
from gisa.templatetags.gisa_filters import qtext

VALID_TYPES = {'단답', '빈칸', '열거', '서술', '계산', '표그림'}


def check(r):
    warns = []
    if r.get('qtype') not in VALID_TYPES:
        warns.append(f"qtype {r.get('qtype')}")
    if not (r.get('text') or '').strip():
        warns.append('빈 문제')
    if not (r.get('answer_items') or r.get('answer_text')):
        warns.append('답 없음')
    for f in ('text', 'reference', 'answer_text'):
        v = r.get(f) or ''
        if '{,}' in v or re.search(r'\$[^$]+\$', v):
            warns.append(f'{f}에 LaTeX 표기')
        html = str(qtext(v))
        if v.count('[svg]') != html.count('<svg'):
            warns.append(f'{f} SVG 필터 걸림')
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_pred_new')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--cert', default='자연생태복원기사')
    args = ap.parse_args()

    rows = []
    for p in sorted(glob.glob(os.path.join(args.src, 'qs_*.json'))):
        rows.extend(json.load(open(p, encoding='utf-8')))
    if not rows:
        print('결과 파일(qs_*.json)이 없습니다.')
        return

    ok, bad = [], []
    seen = set()
    for r in rows:
        key = (r.get('section'), r.get('number'))
        w = check(r)
        if key in seen:
            w.append('section·number 중복')
        seen.add(key)
        (bad if w else ok).append((r, w))

    print(f'{len(rows)}건 — 통과 {len(ok)} / 문제 {len(bad)}')
    for r, w in bad[:20]:
        print(f"  [{r.get('section')} {r.get('number')}] {', '.join(w)}")

    import collections
    sec = collections.Counter(r['section'] for r, _ in ok)
    for s, n in sec.items():
        print(f'  {s}: {n}문항')

    if not args.apply:
        print('\n(--apply 를 붙이면 DB에 반영합니다)')
        return

    cert = Certification.objects.get(name=args.cert)
    made = 0
    for r, _ in ok:
        Q.objects.update_or_create(
            certification=cert, source='예상', section=r['section'],
            year=None, round=None, number=r['number'],
            defaults={
                'qtype': r['qtype'], 'points': r['points'],
                'text': r['text'],
                'answer_items': r.get('answer_items') or [],
                'answer_text': r.get('answer_text') or '',
                'reference': r.get('reference') or '',
                'notes': '자체 제작 — 필기 빈출·실기 미출제 후보 기반',
            })
        made += 1
    print(f'반영 {made}건')


if __name__ == '__main__':
    main()
