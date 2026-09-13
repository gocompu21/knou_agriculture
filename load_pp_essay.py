# -*- coding: utf-8 -*-
"""식물보호산업기사 실기(필답형) 기출 문항을 DB에 넣는다.

**검정방법** (Q-net 종목별 상세정보, jmCd=2562 취득방법)
  · 실기 과목 : 식물보호실무
  · 검정방법 : **필답형 단독** (작업형이 없다 — 조경·자연생태복원과 다른 점)
  · 합격기준 : 100점 만점에 60점 이상
  → 20문항이므로 **문항당 5점**으로 잡으면 합계가 100점이 된다.

**출처와 저작권.** 문항 내용은 국가시험의 사실이지만, 복원본을 실어 파는
사이트(moducbt.com)의 **표현과 편집은 그쪽 저작물**이다. 그래서 이 프로젝트가
자연생태복원·조경 실기에서 해 온 대로 처리했다 —

  · 문제문 : 조사 정도만 바꿔 재서술 (수치·전문용어·묻는 개수는 그대로)
  · 답     : 다시 씀
  · 해설   : 원문에 없다. 배경과 까닭을 담아 새로 씀

  python load_pp_essay.py            # 검증만
  python load_pp_essay.py --apply    # DB 반영
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

CERT, CATEGORY, TOTAL = '식물보호산업기사', '산업기사', 100

# 회차 → 파일
ROUNDS = {
    (2023, 1): '_pp_2023_1.json',
}


def check(rows):
    bad = []
    nums = [r['number'] for r in rows]
    if nums != list(range(1, len(rows) + 1)):
        bad.append(f'문항 번호가 1~{len(rows)} 이 아니다: {nums}')
    if TOTAL % len(rows):
        bad.append(f'{len(rows)}문항으로는 {TOTAL}점이 고르게 나뉘지 않는다')
    for r in rows:
        n = r['number']
        if not r['text'].strip():
            bad.append(f'{n}번: 문제가 비었다')
        if not r.get('answer_items'):
            bad.append(f'{n}번: 답이 비었다')
        if len(r.get('reference', '')) < 120:
            bad.append(f'{n}번: 해설이 너무 짧다({len(r.get("reference", ""))}자)')
        if not r.get('notes'):
            bad.append(f'{n}번: 출처(notes)가 비었다')
    return bad


def load_round(year, rnd, path, apply_):
    rows = json.load(io.open(path, encoding='utf-8'))
    bad = check(rows)
    if bad:
        print(f'{year}-{rnd}회 검증 실패 — 넣지 않는다')
        for x in bad:
            print('  ', x)
        return 1

    pts = TOTAL / len(rows)          # 20문항이면 5점씩
    cert = Certification.objects.get(name=CERT, category=CATEGORY)
    have = {q.number: q for q in GisaEssayQuestion.objects.filter(
        certification=cert, source='기출', year=year, round=rnd)}

    add = upd = 0
    for r in rows:
        fields = dict(
            section='기출', qtype=r['qtype'], text=r['text'],
            answer_items=r['answer_items'], answer_text=r.get('answer_text', ''),
            reference=r['reference'], points=pts,
            notes=r['notes'], orig_number=r['number'],
        )
        q = have.get(r['number'])
        if q is None:
            add += 1
            if apply_:
                GisaEssayQuestion.objects.create(
                    certification=cert, source='기출', year=year, round=rnd,
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

    print(f'{CERT} {year}-{rnd}회  신규 {add}건 · 수정 {upd}건 '
          f'(문항 {len(rows)}개 × {pts:g}점 = {TOTAL}점)')
    return 0


def main():
    apply_ = '--apply' in sys.argv
    rc = 0
    for (year, rnd), path in sorted(ROUNDS.items()):
        rc |= load_round(year, rnd, path, apply_)
    print('반영했다.' if apply_ else '(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
    return rc


if __name__ == '__main__':
    sys.exit(main())
