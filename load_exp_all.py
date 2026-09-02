# -*- coding: utf-8 -*-
"""726문항 해설 재작성 결과를 검증하고 reference 에 반영한다.

화면은 qtext 필터를 거치므로 실제로 렌더링해 보고 SVG 가 걸러지지 않는지,
객관식 어투나 LaTeX 잔재가 없는지 확인한다. 위반은 그 건만 보류한다.
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

from gisa.models import GisaEssayQuestion as Q
from gisa.templatetags.gisa_filters import qtext

# 객관식에서만 성립하는 표현 — 필답 해설에 있으면 수험생이 오해한다
_OBJECTIVE = re.compile(
    r'고르게|고르는|고르면|선지|보기 중|틀린 것|옳은 것|아닌 것은|오답 패턴|객관식'
)


def check(text):
    warns = []
    if not (text or '').strip():
        return ['빈 해설']
    html = str(qtext(text))

    m = _OBJECTIVE.search(text)
    if m:
        warns.append(f'객관식 표현 "{m.group()}"')
    if '{,}' in text:
        warns.append('{,} 표기')
    if re.search(r'\$[^$]+\$', text):
        warns.append('LaTeX $...$ 표기')

    want = text.count('[svg]')
    got = html.count('<svg')
    if want != got:
        warns.append(f'SVG {want}개 중 {got}개만 렌더링')

    if ('|---' in text or '| ---' in text) and '<table' not in html:
        warns.append('표가 변환되지 않음')
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_exp_all')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, 'b*_done.json')))
    if not files:
        print('결과 파일(b*_done.json)이 없습니다.')
        return

    rows = []
    for p in files:
        rows.extend(json.load(open(p, encoding='utf-8')))
    print(f'{len(files)}개 파일 / {len(rows)}건')

    qs = {q.pk: q for q in Q.objects.filter(source='기출')}
    ok, bad, missing = [], [], 0
    seen = set()
    for r in rows:
        pk = r.get('pk')
        if pk in seen:
            continue
        seen.add(pk)
        q = qs.get(pk)
        if not q:
            missing += 1
            continue
        w = check(r.get('reference'))
        (bad if w else ok).append((q, r, w))

    print(f'통과 {len(ok)} / 보류 {len(bad)} / 없는 pk {missing} / '
          f'미작성 {len(qs) - len(seen)}')
    for q, r, w in bad[:30]:
        print(f'  [{q.year}-{q.round}-{q.number}] {", ".join(w)}')

    if ok:
        lens = sorted(len(r['reference']) for _, r, _ in ok)
        print(f'길이: 중앙 {lens[len(lens)//2]}자 / 75% {lens[len(lens)*3//4]}자 / '
              f'최대 {lens[-1]}자 / 합계 {sum(lens):,}자')

    if not args.apply:
        print('\n(--apply 를 붙이면 DB에 반영합니다)')
        return

    for q, r, _ in ok:
        q.reference = r['reference']
        q.save(update_fields=['reference'])
    print(f'반영 {len(ok)}건')


if __name__ == '__main__':
    main()
