# -*- coding: utf-8 -*-
"""조경기사 실기 2026년 2회 필답형 12문항을 DB에 넣는다.

출처는 **수험생이 직접 응시하고 복원한 것**이다(사용자 제공). 회차 배점 합계가
40점으로 딱 맞아 시험지 한 벌이 통째로 복원된 것으로 본다.

복원본을 그대로 옮기지 않고 아래를 손봤다 — 무엇을 왜 고쳤는지는 문항마다
`notes` 에 남겨 두었다.

  · 3번 '들꿩나무' → **덜꿩나무**(Viburnum erosum). 들꿩은 새 이름이고 그런
    수종은 없다 — 복원 과정의 받아쓰기 오기로 보았다
  · 5번 발문의 '고덕도'는 뜻이 잡히지 않아, 확인되는 사실(센노 리큐의 다도
    계승 · 쇼군가 다도 지도 · 작정)로 발문을 다시 썼다
  · 10번 답에서 **이윤을 뺐다.** 제비율로 산정하는 것은 맞지만 이윤은
    간접공사비가 아니라 원가 위에 붙는 별도 비목이다
  · 4번은 법정 조경면적 비율이 복원본에 없어 2/3 규정만 적용했다. 조례 비율이
    함께 주어졌다면 50% 상한이 걸려 답이 달라진다 — 해설에 적어 두었다

  python load_ls_2026_2.py           # 검증만
  python load_ls_2026_2.py --apply   # DB 반영
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

CERT, YEAR, ROUND = '조경기사', 2026, 2
TOTAL = 40


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open('_ls_2026_2.json', encoding='utf-8'))

    bad = []
    pts = sum(r['points'] for r in rows)
    if pts != TOTAL:
        bad.append(f'배점 합계가 {pts}점이다 — 조경기사 필답은 {TOTAL}점이어야 한다')
    nums = [r['number'] for r in rows]
    if nums != list(range(1, len(rows) + 1)):
        bad.append(f'문항 번호가 1~{len(rows)} 이 아니다: {nums}')
    for r in rows:
        n = r['number']
        if not r['text'].strip():
            bad.append(f'{n}번: 문제가 비었다')
        if not r.get('answer_items'):
            bad.append(f'{n}번: 답이 비었다')
        if len(r.get('reference', '')) < 80:
            bad.append(f'{n}번: 해설이 너무 짧다({len(r.get("reference", ""))}자)')
    if bad:
        print('검증 실패 — 넣지 않는다')
        for x in bad:
            print('  ', x)
        return 1

    cert = Certification.objects.get(name=CERT, category='기사')
    have = {q.number: q for q in GisaEssayQuestion.objects.filter(
        certification=cert, source='기출', year=YEAR, round=ROUND)}

    add = upd = 0
    for r in rows:
        fields = dict(
            section='기출', qtype=r['qtype'], text=r['text'],
            answer_items=r['answer_items'], answer_text=r.get('answer_text', ''),
            reference=r['reference'], points=r['points'],
            notes=r.get('notes', ''), orig_number=r['number'],
        )
        q = have.get(r['number'])
        if q is None:
            add += 1
            if apply_:
                GisaEssayQuestion.objects.create(
                    certification=cert, source='기출', year=YEAR, round=ROUND,
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

    print(f'{CERT} {YEAR}-{ROUND}회  신규 {add}건 · 수정 {upd}건 '
          f'(문항 {len(rows)}개 · 합계 {pts}점)')
    print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)' if not apply_ else '반영했다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
