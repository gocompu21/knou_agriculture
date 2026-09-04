# -*- coding: utf-8 -*-
"""같은 것을 묻는 문항끼리 답을 똑같이 맞춘다.

한 주제가 여러 회차에 되풀이 출제되는데 답이 표현만 다르게 제각각
적혀 있으면, 학습자는 "어느 쪽이 맞나" 하고 멈춘다. 앞서 계산 문항에
했던 것과 같은 일을 서술·열거·빈칸까지 넓힌 것이다.

**통일하는 것은 표현이지 내용이 아니다.** 묻는 개수가 다르거나(3가지 vs
2가지), 묻는 대상이 다르거나(복원·복구·대체 셋 vs 복원·복구 둘),
빈칸 위치가 다른 문항은 답이 달라야 맞으므로 건드리지 않는다. 그 판정은
문항을 직접 읽고 내렸고, 여기서는 그 결과만 반영한다.

반영 전에 원본을 _essay_unify_backup.json 으로 남긴다.

pk 가 로컬 6 / 서버 3 으로 달라 (year, round, number) 로 찾는다.
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

BACKUP = '_essay_unify_backup.json'


def load(paths):
    rows = []
    for p in paths:
        if not os.path.exists(p):
            print(f'  파일 없음: {p}')
            continue
        rows += json.load(io.open(p, encoding='utf-8'))
    return rows


def main():
    apply = '--apply' in sys.argv
    files = [a for a in sys.argv[1:] if a.endswith('.json')]
    if not files:
        files = ['unified_b1.json', 'unified_b2.json', 'unified_b3.json']

    rows = load(files)
    uni = [r for r in rows if r.get('apply')]
    skip = [r for r in rows if r.get('skipped')]
    print(f'묶음 {len(rows)}건 | 통일 {len(uni)} | 건너뜀 {len(skip)}')

    backup, changed, missing = [], 0, []
    for r in uni:
        items = r.get('answer_items') or []
        text = r.get('answer_text') or ''
        if not items and not text:
            print(f"  답 비어 있음 — 건너뜀: {r.get('key')}")
            continue
        for y, rd, num in r['apply']:
            q = Q.objects.filter(source='기출', year=y, round=rd,
                                 number=num).first()
            if not q:
                missing.append(f'{y}-{rd}#{num}')
                continue
            if q.answer_items == items and (q.answer_text or '') == text:
                continue
            backup.append({
                'year': y, 'round': rd, 'number': num,
                'answer_items': q.answer_items or [],
                'answer_text': q.answer_text or '',
            })
            changed += 1
            if apply:
                q.answer_items = items
                q.answer_text = text
                q.save(update_fields=['answer_items', 'answer_text'])

    if missing:
        print(f'  DB 에 없는 문항 {len(missing)}건: {missing[:8]}')
    print(f'{"반영" if apply else "대상"} {changed}문항')

    if apply and backup:
        io.open(BACKUP, 'w', encoding='utf-8').write(
            json.dumps(backup, ensure_ascii=False, indent=1))
        print(f'  원본 백업 → {BACKUP} ({len(backup)}건)')
    if not apply:
        print('(--apply 로 반영)')


if __name__ == '__main__':
    main()
