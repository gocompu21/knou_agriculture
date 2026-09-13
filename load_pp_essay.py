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

  python load_pp_essay.py                  # 두 자격증 모두 검증만
  python load_pp_essay.py --apply          # DB 반영
  python load_pp_essay.py 기사 --apply      # 식물보호기사만
  python load_pp_essay.py 산업기사 --apply   # 식물보호산업기사만
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

TOTAL = 100

# **문항당 배점은 5점으로 고정한다.** 실제 시험이 20문항 100점이므로 한 문항이
# 5점이다. 합계를 문항 수로 나누면(TOTAL/len) 복원이 덜 된 회차에서 배점이
# 부풀어 오른다 — 24-3회는 19문항만 복원돼 있어 5.26점씩이 되어 버린다.
PER_ITEM = 5

# 자격증 → (급수, 회차 → 파일). **파일 앞머리를 급수별로 갈라 두었다** —
# `_pp_` 는 산업기사, `_ppg_` 는 기사다. 같은 연도·회차가 두 자격증에 모두
# 있으므로 이름이 겹치면 엉뚱한 회차를 싣게 된다.
CERTS = {
    '식물보호산업기사': ('산업기사', {
        (2023, 1): '_pp_2023_1.json',
        (2023, 2): '_pp_2023_2.json',
        (2023, 4): '_pp_2023_4.json',
        (2024, 1): '_pp_2024_1.json',
        (2024, 2): '_pp_2024_2.json',
        (2024, 3): '_pp_2024_3.json',
        (2025, 1): '_pp_2025_1.json',
        (2025, 2): '_pp_2025_2.json',
        (2025, 3): '_pp_2025_3.json',
    }),
    '식물보호기사': ('기사', {
        (2023, 1): '_ppg_2023_1.json',
        (2023, 2): '_ppg_2023_2.json',
        (2023, 3): '_ppg_2023_3.json',
        (2024, 1): '_ppg_2024_1.json',
        (2024, 2): '_ppg_2024_2.json',
        (2024, 3): '_ppg_2024_3.json',
        (2025, 1): '_ppg_2025_1.json',
        (2025, 2): '_ppg_2025_2.json',
        (2025, 3): '_ppg_2025_3.json',
    }),
}


def check(rows):
    bad = []
    # **번호는 실제 시험지의 것을 그대로 쓴다.** 복원본이 한 문항을 통째로
    # 놓친 회차(24-2회 19번은 물음이 깨져 있다)에서 번호를 당겨 메우면,
    # 다른 수험 자료와 대조할 때 번호가 어긋난다. 그래서 1~N 연속이 아니라
    # '겹치지 않고 1~20 안에 있는가'만 본다.
    nums = [r['number'] for r in rows]
    if sorted(nums) != nums or len(set(nums)) != len(nums):
        bad.append(f'문항 번호가 겹치거나 차례가 아니다: {nums}')
    if nums and (nums[0] < 1 or nums[-1] > TOTAL // PER_ITEM):
        bad.append(f'문항 번호가 1~{TOTAL // PER_ITEM} 범위를 벗어난다: {nums}')
    if len(rows) * PER_ITEM > TOTAL:
        bad.append(f'{len(rows)}문항 × {PER_ITEM}점이 {TOTAL}점을 넘는다')
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


def load_round(cert_name, category, year, rnd, path, apply_):
    rows = json.load(io.open(path, encoding='utf-8'))
    bad = check(rows)
    if bad:
        print(f'{cert_name} {year}-{rnd}회 검증 실패 — 넣지 않는다')
        for x in bad:
            print('  ', x)
        return 1

    pts = PER_ITEM
    cert = Certification.objects.get(name=cert_name, category=category)
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

    total = len(rows) * pts
    gap = [n for n in range(1, TOTAL // PER_ITEM + 1)
           if n not in {r['number'] for r in rows}]
    tail = '' if total == TOTAL else (
        f'  ← {TOTAL - total}점 모자람(복원 미완'
        + (f', 빠진 번호 {gap}' if gap else '') + ')')
    print(f'{cert_name} {year}-{rnd}회  신규 {add}건 · 수정 {upd}건 '
          f'(문항 {len(rows)}개 × {pts:g}점 = {total}점){tail}')
    return 0


def main():
    apply_ = '--apply' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--apply']
    # '기사'는 '산업기사'의 부분 문자열이라 in 으로 고르면 둘 다 걸린다.
    # 급수 이름이 정확히 같은 것만 고른다.
    picked = {n: v for n, v in CERTS.items() if not args or v[0] in args}
    if not picked:
        print(f'그런 급수가 없다: {args} (쓸 수 있는 값: '
              f'{", ".join(v[0] for v in CERTS.values())})')
        return 1
    rc = 0
    for cert_name, (category, rounds) in picked.items():
        for (year, rnd), path in sorted(rounds.items()):
            rc |= load_round(cert_name, category, year, rnd, path, apply_)
    print('반영했다.' if apply_ else '(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
    return rc


if __name__ == '__main__':
    sys.exit(main())
