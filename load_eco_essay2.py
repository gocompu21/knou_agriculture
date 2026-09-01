# -*- coding: utf-8 -*-
"""2005~2021 필답 기출 JSON을 DB에 적재한다.

교재(2022~2025)와 같은 GisaEssayQuestion 에 들어가며, 회차가 다르므로
충돌하지 않는다. 회차 단위로 정리되는 대로 하나씩 적재·배포할 수 있다.

배점은 유형별 기본값을 주고 회차 합계를 45점에 맞춘다
(normalize_essay_points 와 같은 규칙).

사용:
  python load_eco_essay2.py                       # 검증만
  python load_eco_essay2.py --apply               # 전체 적재
  python load_eco_essay2.py --apply --file E_2021-3.json
"""
import argparse
import glob
import json
import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction                      # noqa: E402
from gisa.models import Certification, GisaEssayQuestion   # noqa: E402

SRC = '_eco_essay_parsed2'
CERT = '자연생태복원기사'
TARGET_POINTS = 45.0
STEP = 0.5
MIN_POINTS = 1.0

POINTS_BY_TYPE = {
    '계산': 4, '서술': 4, '표그림': 4,
    '열거': 3, '빈칸': 2, '단답': 2,
}
TYPES = set(POINTS_BY_TYPE)


def guess_type(q):
    """type이 비어 있으면 문제문·답 모양으로 추정한다."""
    t = (q.get('type') or '').strip()
    if t in TYPES:
        return t
    text = q.get('text', '')
    if re.search(r'\(\s*\)|\(\s*[A-D가-힣]\s*\)|빈칸', text):
        return '빈칸'
    if re.search(r'구하시오|계산|산출', text):
        return '계산'
    if re.search(r'\d+\s*가지', text):
        return '열거'
    if re.search(r'분류하시오|표시하시오|나열하시오', text):
        return '표그림'
    items = q.get('answer_items') or []
    if len(items) == 1 and len(items[0]) < 40:
        return '단답'
    return '서술'


# 문항이 이보다 적으면 부분 복원으로 보고 45점 정규화를 하지 않는다.
# 6문항짜리를 45점으로 부풀리면 문항당 7.5점이 되어 실제 배점과 어긋난다.
MIN_FULL_ROUND = 10


def normalize_points(rows):
    """회차 합계를 45점으로 맞춘다 (배점이 큰 문항부터 0.5씩 가감).

    문항 수가 너무 적은 부분 복원 회차는 유형별 기본 배점을 그대로 둔다.
    """
    pts = {i: float(POINTS_BY_TYPE.get(r['_type'], 3)) for i, r in enumerate(rows)}
    if len(rows) < MIN_FULL_ROUND:
        return pts
    diff = TARGET_POINTS - sum(pts.values())
    order = sorted(range(len(rows)), key=lambda i: (-pts[i], rows[i]['number']))
    guard = 0
    while abs(diff) >= 0.01 and guard < 5000:
        moved = False
        for i in order:
            if abs(diff) < 0.01:
                break
            if diff > 0:
                pts[i] += STEP
                diff -= STEP
                moved = True
            elif pts[i] - STEP >= MIN_POINTS:
                pts[i] -= STEP
                diff += STEP
                moved = True
        guard += 1
        if not moved:
            break
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC)
    ap.add_argument('--file', default='')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    cert = Certification.objects.filter(name=CERT).first()
    if not cert:
        print(f'자격증 없음: {CERT}')
        return

    files = ([os.path.join(args.src, args.file)] if args.file
             else sorted(glob.glob(os.path.join(args.src, '*.json'))))

    total_new = total_upd = 0
    for f in files:
        if os.path.basename(f).startswith('SPEC'):
            continue
        try:
            rows = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print(f'{os.path.basename(f)}: 파싱 실패 {e}')
            continue
        if not rows:
            continue

        # 회차별로 묶는다
        by_round = {}
        for r in rows:
            by_round.setdefault((r['year'], r['round']), []).append(r)

        for (year, rnd), items in sorted(by_round.items()):
            items.sort(key=lambda x: x['number'])
            for it in items:
                it['_type'] = guess_type(it)
            pts = normalize_points(items)

            problems = []
            for i, it in enumerate(items):
                if not (it.get('text') or '').strip():
                    problems.append(f'{it["id"]}: text 없음')
                if not it.get('answer_items') and not (it.get('answer_text') or '').strip():
                    problems.append(f'{it["id"]}: 답 없음')

            print(f'\n[{year}-{rnd}] {len(items)}문항  '
                  f'배점합 {sum(pts.values()):g}점  ({os.path.basename(f)})')
            for i, it in enumerate(items):
                print(f'   {it["number"]:2d}. [{it["_type"]}] {pts[i]:g}점  {it["text"][:52]}')
            if problems:
                print('   문제점:', problems)

            if not args.apply:
                continue

            with transaction.atomic():
                for i, it in enumerate(items):
                    obj, is_new = GisaEssayQuestion.objects.update_or_create(
                        certification=cert, source='기출', section='기출',
                        year=year, round=rnd, number=it['number'],
                        defaults={
                            'qtype': it['_type'],
                            'text': it.get('text', ''),
                            'answer_items': it.get('answer_items') or [],
                            'answer_text': it.get('answer_text', ''),
                            'reference': it.get('reference', ''),
                            'notes': (it.get('notes', '') + ' [재서술]').strip(),
                            'points': pts[i],
                        },
                    )
                    total_new += is_new
                    total_upd += (not is_new)

    if args.apply:
        print(f'\n적재 완료: 신규 {total_new} / 갱신 {total_upd}')
    else:
        print('\n[dry-run] --apply 를 붙이면 DB에 반영합니다')


if __name__ == '__main__':
    main()
