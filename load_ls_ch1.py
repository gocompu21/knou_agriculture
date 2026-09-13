# -*- coding: utf-8 -*-
"""조경기사 실기 Chapter 01 기출문제 Ⅰ(구유형 적산) 81문항을 DB에 넣는다.

교재(PART 7 Chapter 01, 353~399쪽)는 2022년 개편 **이전** 유형의 기출을 회차
표시 없이 모아 둔 묶음이다. "수험생 기억에 의한 복원"이라 회차를 붙일 수 없어
source='기출'(회차별 90분 시험지)에 섞을 수 없다. 이미 있는 예상문제 경로
(영역 카드 → 정답 보며 학습)가 이 성격에 맞으므로 source='적산'으로 싣는다.

  python load_ls_ch1.py           # 검증만 (무엇이 바뀌는지 보여 준다)
  python load_ls_ch1.py --apply   # DB 반영

문항 번호는 교재 번호를 그대로 쓴다. 영역이 달라도 번호가 겹치지 않아
(1~81 이 통째로 유일) 교재와 대조하기 쉽다.
"""
import glob
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

CERT = '조경기사'
SOURCE = '적산'

# 배점 — 자연생태복원 실기와 같은 기준(계산·서술·표그림 4 / 열거 3 / 빈칸·단답 2).
# 조경 실기 필답은 합계 40점이지만 이 묶음은 회차 시험지가 아니라 영역별 학습용
# 이라 정규화하지 않는다. 유형별 배점이 그대로 채점 가중치가 된다.
POINTS = {'계산': 4, '서술': 4, '표그림': 4, '열거': 3, '빈칸': 2, '단답': 2}

# 영역 카드에 보일 순서. 토공 → 기계 → 인력 → 재료 → 식재 → 시설 → 측량 으로,
# 적산의 흐름(무엇을 얼마나 옮기나 → 무엇으로 얼마나 드나)을 따른다.
SECTIONS = ['토공량', '기계화 시공', '인력·기계 운반', '재료·적산',
            '수목식재', '포장·시설', '측량·적산일반']


def load():
    rows = []
    for path in sorted(glob.glob('_ls_ch1_*.json')):
        rows.extend(json.load(io.open(path, encoding='utf-8')))
    rows.sort(key=lambda r: r['number'])
    return rows


def check(rows):
    """넣기 전에 스스로 검사한다 — 번호 빠짐·중복, 낯선 영역·유형, 빈 답."""
    bad = []
    nums = [r['number'] for r in rows]
    miss = [n for n in range(1, 82) if n not in nums]
    if miss:
        bad.append(f'빠진 번호: {miss}')
    dup = sorted({n for n in nums if nums.count(n) > 1})
    if dup:
        bad.append(f'중복 번호: {dup}')
    for r in rows:
        n = r['number']
        if r['section'] not in SECTIONS:
            bad.append(f'{n}번: 낯선 영역 {r["section"]!r}')
        if r['qtype'] not in POINTS:
            bad.append(f'{n}번: 낯선 유형 {r["qtype"]!r}')
        if not r['text'].strip():
            bad.append(f'{n}번: 문제가 비었다')
        if not r.get('answer_items') and not r.get('answer_text', '').strip():
            bad.append(f'{n}번: 답이 비었다')
        if len(r.get('reference', '')) < 60:
            bad.append(f'{n}번: 해설이 너무 짧다({len(r.get("reference", ""))}자)')
    return bad


def main():
    apply_ = '--apply' in sys.argv
    rows = load()

    bad = check(rows)
    if bad:
        print('검증 실패 — 넣지 않는다')
        for b in bad:
            print('  ', b)
        return 1

    cert = Certification.objects.get(name=CERT, category='기사')
    have = {q.number: q for q in
            GisaEssayQuestion.objects.filter(certification=cert, source=SOURCE)}

    add = upd = 0
    for r in rows:
        fields = dict(
            section=r['section'],
            qtype=r['qtype'],
            text=r['text'],
            answer_items=r.get('answer_items', []),
            answer_text=r.get('answer_text', ''),
            reference=r.get('reference', ''),
            points=POINTS[r['qtype']],
            orig_number=r['number'],
        )
        q = have.get(r['number'])
        if q is None:
            add += 1
            if apply_:
                GisaEssayQuestion.objects.create(
                    certification=cert, source=SOURCE, year=None, round=None,
                    number=r['number'], **fields)
        else:
            changed = [k for k, v in fields.items() if getattr(q, k) != v]
            if changed:
                upd += 1
                if apply_:
                    for k, v in fields.items():
                        setattr(q, k, v)
                    q.save()

    print(f'{CERT} source={SOURCE}  신규 {add}건 · 수정 {upd}건 '
          f'(기존 {len(have)}건, 대상 {len(rows)}건)')
    if apply_:
        by_sec = {}
        for q in GisaEssayQuestion.objects.filter(certification=cert, source=SOURCE):
            by_sec[q.section] = by_sec.get(q.section, 0) + 1
        print('영역별:')
        for s in SECTIONS:
            print(f'  {s}: {by_sec.get(s, 0)}문항')
    else:
        print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
