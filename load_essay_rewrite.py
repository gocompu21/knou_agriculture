# -*- coding: utf-8 -*-
"""재서술한 모범답안을 DB에 반영한다.

`_rewrite/*.json` 의 answer_items / answer_text 를 GisaEssayQuestion 에 쓴다.
문제문·배점·분류는 건드리지 않는다. rubric 은 비워서 새 답으로 다시
생성되게 한다.

사용:
  python load_essay_rewrite.py                 # 검증만
  python load_essay_rewrite.py --apply         # DB 반영
  python load_essay_rewrite.py --src _rewrite  # 입력 디렉토리
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

from django.db import transaction                       # noqa: E402
from gisa.models import GisaEssayQuestion               # noqa: E402

REWRITE_MARK = '[재서술]'


def word_set(s):
    return set(re.findall(r'[가-힣A-Za-z0-9]{2,}', s or ''))


def overlap(a, b):
    ta, tb = word_set(a), word_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def flat(items, text):
    return '\n'.join(items or []) + '\n' + (text or '')


def count_required(text):
    """문제문이 요구하는 항목 개수. 판정할 수 없으면 0.

    단순히 'N가지'를 세면 오탐이 많다. 실제 문제문에는 이런 것들이 섞여 있다.
      - "3가지 이상"      → 개수 하한이라 초과해도 정상
      - "7가지 중 3가지"  → 뒤의 3이 답할 개수
      - "사례 1가지와 물질 2가지" → 합쳐서 3개
    """
    t = text or ''
    if re.search(r'\d+\s*가지\s*이상', t):
        return 0                      # 하한 조건이면 검사하지 않는다
    nums = [int(n) for n in re.findall(r'(\d+)\s*가지', t)]
    if not nums:
        return 0
    if re.search(r'\d+\s*가지\s*중', t) and len(nums) >= 2:
        return nums[-1]               # "N가지 중 M가지" → M
    if len(nums) >= 2:
        return sum(nums)              # "A 1가지와 B 2가지" → 3
    return nums[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_rewrite')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    files = sorted(f for f in glob.glob(os.path.join(args.src, '*.json')))
    if not files:
        print(f'파일 없음: {args.src}')
        return

    rows, pending = [], []
    for f in files:
        try:
            data = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print(f'  파싱 실패 {os.path.basename(f)}: {e}')
            continue
        for r in data:
            r['_file'] = os.path.basename(f)
            (rows if r.get('rewritten') else pending).append(r)

    print(f'재서술 완료 {len(rows)} / 미처리 {len(pending)} '
          f'(파일 {len(files)}개)')
    if pending:
        by_file = {}
        for r in pending:
            by_file[r['_file']] = by_file.get(r['_file'], 0) + 1
        print('  미처리 파일:', dict(sorted(by_file.items())))

    if not rows:
        return

    problems, high_overlap = [], []
    pk_map = {q.pk: q for q in GisaEssayQuestion.objects.filter(
        pk__in=[r['pk'] for r in rows])}

    for r in rows:
        q = pk_map.get(r['pk'])
        if not q:
            problems.append(f"pk={r['pk']} DB에 없음")
            continue
        new = flat(r.get('answer_items'), r.get('answer_text'))
        if not new.strip():
            problems.append(f"{q.label} {q.number}번: 답이 비어 있음")
            continue
        # 표·순서형은 수치와 공정 순서가 답이라 겹침이 높은 게 정상이다.
        # 설명 문장이 붙는 서술·열거형만 재서술 정도를 본다.
        if q.qtype not in ('표그림', '계산'):
            ov = overlap(flat(q.answer_items, q.answer_text), new)
            if ov > 0.80:
                high_overlap.append((q, ov))
        # 개수 요구 확인
        need = count_required(q.text)
        got = len(r.get('answer_items') or [])
        if need and got and got != need:
            problems.append(
                f"{q.label} {q.number}번: '{need}가지' 요구인데 항목 {got}개")

    print(f'\n[검증] 문제 {len(problems)}건 / 겹침 0.8 초과 {len(high_overlap)}건')
    for p in problems[:25]:
        print('  -', p)
    if len(problems) > 25:
        print(f'  … 외 {len(problems) - 25}건')
    if high_overlap:
        print('\n[겹침 높음 — 재서술이 덜 된 문항]')
        for q, ov in sorted(high_overlap, key=lambda x: -x[1])[:12]:
            print(f'  {ov:.2f} {q.label} {q.number}번 {q.text[:44]}')

    if not args.apply:
        print('\n[dry-run] --apply 를 붙이면 DB에 반영합니다')
        return

    n = 0
    with transaction.atomic():
        for r in rows:
            q = pk_map.get(r['pk'])
            if not q:
                continue
            new = flat(r.get('answer_items'), r.get('answer_text'))
            if not new.strip():
                continue
            q.answer_items = r.get('answer_items') or []
            q.answer_text = r.get('answer_text') or ''
            q.rubric = []
            note = r.get('notes') or q.notes or ''
            if REWRITE_MARK not in note:
                note = (note + f' {REWRITE_MARK}').strip()
            q.notes = note
            q.save(update_fields=['answer_items', 'answer_text', 'rubric', 'notes'])
            n += 1
    print(f'\nDB 반영 완료: {n}문항')


if __name__ == '__main__':
    main()
