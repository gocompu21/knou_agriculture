# -*- coding: utf-8 -*-
"""2026-1회 식물보호기사 실기 20문항에 주제(topic_key·topic_group)를 붙인다.

**`tag_essay_frequency` 를 다시 돌리지 않는다.** 그 명령은 군집을 처음부터 다시
만들어 `topic_key` 를 새로 매기는데, 식물보호는 쪽집게 노트의 학습 자료가
주제키로 묶여 있어 통째로 끊긴다(그래서 LOCKED 다). 회차 하나가 늘었을 뿐이므로
여기서는 **손으로 이어 붙인다** —

  · 이미 있는 주제에 드는 문항은 그 주제의 `topic_key` 를 그대로 받는다
  · 새 주제는 기존 방식과 같은 규칙으로 키를 만든다(md5(text[:80])[:16])
  · `freq_rounds`·`freq_note` 는 **건드린 주제만** 다시 센다. 모수는 기사·산업기사를
    합친 묶음의 시험지 수다(`essay_topics.siblings`)

    python load_ppg2026_topics.py            # 무엇이 바뀌는지만 보여 준다
    python load_ppg2026_topics.py --apply    # DB 반영
"""
import hashlib
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from gisa.models import Certification, GisaEssayQuestion  # noqa: E402
from gisa.essay_topics import siblings  # noqa: E402

YEAR, RND = 2026, 1

# 급수 → {문항번호: (기존 주제키 또는 None, 주제 분류)}
#   None 이면 이 문항의 발문으로 새 키를 만든다.
MAPS = {}

MAPS['식물보호기사'] = {
    1:  ('18e9160aba35b609', 11),   # 「농약관리법」 정의 — 25-3 방제업과 같은 조문
    2:  ('5765453b76d8142a', 5),    # 배액 조제 계산 (시험지 18장)
    3:  ('8dcc81d387aeb13c', 5),    # 성분명 → 농약 갈래 고르기 (17장)
    4:  ('d8fafaeda3e3b87f', 1),    # 새눈무늬병 동정
    5:  ('da982ae295721b2a', 2),    # 매미나방 동정
    6:  (None, 2),                  # [신규] 더듬이 세 마디
    7:  (None, 2),                  # [신규] 입틀의 방향 — 전구식·하구식·후구식
    8:  (None, 4),                  # [신규] 불임충 방사법의 전제 조건
    9:  ('7da6b58569b4f207', 3),    # 해충 밀도 조사법(표본·축차조사)
    10: (None, 1),                  # [신규] 병원체가 내는 화학물질
    11: (None, 1),                  # [신규] 식물체의 방어 반응
    12: (None, 1),                  # [신규] 기주특이적 독소
    13: ('72f45b57094d79cd', 6),    # 강산성 토양의 양분 유효도
    14: ('afcfdc60bd60a766', 8),    # 고립상태·군락상태
    15: ('6f23aaa80c8bd8cd', 8),    # 온도계수
    16: ('9e33bd66fac0debb', 7),    # 관개법(고랑관개·다공관관개)
    17: ('0c52f7c292a1966a', 9),    # 지연형·장해형 냉해
    18: ('2c9387f2a5ff9530', 9),    # 내동성 요인
    19: ('274735515d9daa60', 9),    # 풍해의 재배적 대책 (9장)
    20: (None, 9),                  # [신규] 풍해의 뜻
}

MAPS['식물보호산업기사'] = {
    1:  ('5765453b76d8142a', 5),    # 배액 조제 계산
    2:  ('8dcc81d387aeb13c', 5),    # 성분명 → 농약 갈래 고르기
    3:  ('2b9f4d8972a7c14c', 1),    # 다릅나무 회색무늬병(Stagonospora) — 23-2 와 같은 문항
    4:  ('0ee038f273601812', 2),    # 호랑나비(Papilio xuthus) 동정
    5:  ('7f0dcaf2291aa7c6', 5),    # 농약의 잔류성 — 23-1 과 같은 문항
    6:  ('a9e03c6163017900', 3),    # 해충 조사법(흡충기·쓸어잡기)
    7:  ('5c5bd297eb214ea0', 4),    # 물리적 방제법 — 23-2 와 같은 문항
    8:  ('6267d971d246dd6a', 4),    # 기계적 방제법(포살·유살)
    9:  ('6520479b5d38278a', 4),    # 기생성·포식성 천적
    10: (None, 1),                  # [신규] 곰팡이의 유성포자
    11: ('029f633fb8a99f31', 1),    # 병원체의 종류·크기 — 가장 작은 것은 바이로이드
    12: ('f35d0ce76f847ffd', 3),    # 식물병 진단법
    13: ('3271bd3374c8711d', 8),    # 굴광현상
    14: ('7ebb2230a895fdad', 8),    # 이산화탄소 보상점·포화점
    15: ('9e33bd66fac0debb', 7),    # 관개법(살수·점적)
    16: (None, 7),                  # [신규] 영양번식
    17: ('483de2086f8a5633', 10),   # 피소(볕뎀) — 원본은 [신규]로 보았으나 25-3 과 같은 주제
    18: ('2c9387f2a5ff9530', 9),    # 내동성을 크게 하는 요인
    19: (None, 8),                  # [신규] 불화수소에 강한 식물
    20: ('d2b03aa9a58bf983', 6),    # 질산화작용
}


def sheet_label(cert_id, short, year, rnd):
    return '%s%d-%d' % (short.get(cert_id, ''), year, rnd)


def main():
    apply_ = '--apply' in sys.argv
    pool = list(Certification.objects.filter(name__in=siblings('식물보호기사')))
    short = {c.id: ('기사' if c.name.endswith('보호기사') else '산기') for c in pool}

    touched = set()
    for cert_name, mapping in MAPS.items():
        cert = Certification.objects.get(name=cert_name)
        rows = {q.number: q for q in GisaEssayQuestion.objects.filter(
            certification=cert, source='기출', year=YEAR, round=RND)}
        missing = [n for n in mapping if n not in rows]
        if missing:
            print(f'{cert_name}: DB 에 없는 문항 {missing}'
                  ' — load_pp_essay.py 를 먼저 돌릴 것')
            return 1
        print(f'=== {cert_name}')
        for n, (key, group) in sorted(mapping.items()):
            q = rows[n]
            if key is None:
                key = hashlib.md5(q.text[:80].encode('utf-8')).hexdigest()[:16]
                tag = '신규'
            else:
                tag = '기존'
            print(f'{n:>2}번 {tag} {key} g{group} | {q.text[:36]}')
            touched.add(key)
            if apply_:
                q.topic_key, q.topic_group = key, group
                q.save(update_fields=['topic_key', 'topic_group'])

    if not apply_:
        print('\n(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
        return 0

    # 건드린 주제만 회차 수를 다시 센다
    print()
    for key in sorted(touched):
        qs = GisaEssayQuestion.objects.filter(certification__in=pool,
                                              source='기출', topic_key=key)
        sheets = sorted({(q.certification_id, q.year, q.round) for q in qs},
                        reverse=True)
        note = ' '.join(sheet_label(c, short, y, r) for c, y, r in sheets[:14])
        if len(sheets) > 14:
            note += f' 외 {len(sheets) - 14}'
        before = qs.first().freq_rounds
        qs.update(freq_rounds=len(sheets), freq_note=note[:200])
        print(f'{key} {before} → {len(sheets)}장  {note}')
    print('\n반영했다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
