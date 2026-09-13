# -*- coding: utf-8 -*-
"""조경기사 실기 2026년 필답형 복원 문항을 DB에 넣는다.

출처는 **수험생 복원**이다 — 2회는 사용자가 직접 응시하고 적어 온 것, 1회는
응시자 정리표와 수험생 후기 블로그 두 편을 맞춰 본 것이다. 복원본을 그대로
옮기지 않고 확인되는 사실로 다듬었으며, 무엇을 왜 고쳤는지는 문항마다
`notes` 에 남겼다.

  python load_ls_2026.py            # 두 회차 검증만
  python load_ls_2026.py --apply    # DB 반영
  python load_ls_2026.py 1 --apply  # 한 회차만

**1회의 5·7·9번은 수치가 복원되지 않았다.** 발문을 지어낼 수 없어 같은 유형의
기출에서 조건을 빌려 풀이 방법만 익히도록 두고, 발문 첫머리에 `(세부 미복원)` 을
박아 이것이 실제 시험지의 수치가 아님을 분명히 했다. 실제 수치가 확인되면
그 문항만 갈아 끼우면 된다.
"""
import io
import json
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from gisa.models import Certification, GisaEssayQuestion  # noqa: E402

CERT, YEAR, TOTAL = '조경기사', 2026, 40

# 회차 → (파일, 배점 합계를 40점으로 검사할지, 덜 된 부분 설명)
ROUNDS = {
    1: ('_ls_2026_1.json', True,
        '5·7·9번은 수치가 복원되지 않아 같은 유형의 기출 조건을 빌렸다 (발문에 표시)'),
    2: ('_ls_2026_2.json', True, ''),
}


def check(rows, strict):
    bad = []
    pts = sum(r['points'] for r in rows)
    if strict and pts != TOTAL:
        bad.append(f'배점 합계가 {pts}점이다 — 조경기사 필답은 {TOTAL}점이어야 한다')
    nums = [r['number'] for r in rows]
    if len(set(nums)) != len(nums):
        bad.append(f'문항 번호가 겹친다: {nums}')
    for r in rows:
        n = r['number']
        if not r['text'].strip():
            bad.append(f'{n}번: 문제가 비었다')
        if not r.get('answer_items'):
            bad.append(f'{n}번: 답이 비었다')
        if len(r.get('reference', '')) < 80:
            bad.append(f'{n}번: 해설이 너무 짧다({len(r.get("reference", ""))}자)')
        if not r.get('notes'):
            bad.append(f'{n}번: 복원 근거(notes)가 비었다')
    return bad, pts


def load_round(rnd, apply_):
    path, strict, note = ROUNDS[rnd]
    rows = json.load(io.open(path, encoding='utf-8'))
    bad, pts = check(rows, strict)
    if bad:
        print(f'{YEAR}-{rnd}회 검증 실패 — 넣지 않는다')
        for x in bad:
            print('  ', x)
        return 1

    cert = Certification.objects.get(name=CERT, category='기사')
    have = {q.number: q for q in GisaEssayQuestion.objects.filter(
        certification=cert, source='기출', year=YEAR, round=rnd)}

    add = upd = 0
    for r in rows:
        fields = dict(
            section='기출', qtype=r['qtype'], text=r['text'],
            answer_items=r['answer_items'], answer_text=r.get('answer_text', ''),
            reference=r['reference'], points=r['points'],
            notes=r['notes'], orig_number=r['number'],
        )
        q = have.get(r['number'])
        if q is None:
            add += 1
            if apply_:
                GisaEssayQuestion.objects.create(
                    certification=cert, source='기출', year=YEAR, round=rnd,
                    number=r['number'], **fields)
        else:
            changed = [k for k, v in fields.items() if getattr(q, k) != v]
            if changed:
                upd += 1
                print(f'  {r["number"]}번 — {", ".join(changed)}')
                if apply_:
                    for k, v in fields.items():
                        setattr(q, k, v)
                    q.save()

    tail = f' · {note}' if note else ''
    print(f'{CERT} {YEAR}-{rnd}회  신규 {add}건 · 수정 {upd}건 '
          f'(문항 {len(rows)}개 · 합계 {pts}점){tail}')
    return 0


def main():
    args = [a for a in sys.argv[1:] if a != '--apply']
    apply_ = '--apply' in sys.argv
    rounds = [int(a) for a in args] if args else sorted(ROUNDS)
    rc = 0
    for r in rounds:
        rc |= load_round(r, apply_)
    print('반영했다.' if apply_ else '(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
    return rc


if __name__ == '__main__':
    sys.exit(main())
