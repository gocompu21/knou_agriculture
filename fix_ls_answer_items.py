# -*- coding: utf-8 -*-
"""조경(산업)기사 실기에서 answer_text 로만 남아 있던 5건을 answer_items 로 옮긴다.

`build_rubric` 은 `answer_items` 가 비면 **답 전체를 한 덩어리 채점 포인트**로 만든다
(`gisa/essay_grading.py`). 뿌리분 문항은 ①②③ 세 가지를 묻는데 한 덩어리라
둘을 맞혀도 0점이거나 만점이거나 둘 중 하나였다. 항목을 가르면 배점이 나뉜다.

자연생태복원 실기 규칙을 그대로 따른다.
  - **항목 수 = 문제가 묻는 것의 수.** 뿌리분 3형태 → 3항목
  - **한 가지만 묻는 서술형은 ①② 없이 문장 하나.** 항목 하나에 문장을 그대로
  - **순서 나열은 한 항목.** 차례가 통째로 맞아야 맞는 답이라 쪼갤 수 없다

채점에 쓰지 않는 곁가지(개화 시기, 공통 조건)는 **「해설」(`reference`)로 옮긴다** —
채점 포인트 안에 두면 순서만 바르게 쓴 답안이 "월을 안 적었다"로 깎인다.

  python fix_ls_answer_items.py [--apply]
"""
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import GisaEssayQuestion          # noqa: E402

APPLY = '--apply' in sys.argv
GI, SI = '조경기사', '조경산업기사'

# (자격증, 연도, 회차, 번호) → (answer_items, reference 앞에 덧댈 글 또는 None)
FIX = {
    (GI, 2024, 1, 8): (
        ['㉡ → ㉠ → ㉣ → ㉤ → ㉢'],
        '생강나무 3월, 수수꽃다리 4월, 이팝나무 5~6월, 산수국 7~8월, 능소화 8~9월에 핀다.',
    ),
    (GI, 2025, 1, 9): (
        ['유기질 비료의 C/N 20:1은 탄소(C)와 질소(N)의 질량 비율이 20대 1이라는 뜻으로, '
         '퇴비 분해에 이상적인 비율이며, 미생물이 유기물을 효율적으로 분해하고 작물에 '
         '영양분이 원활히 공급되는 최적의 상태를 나타낸다.'],
        None,
    ),
    (GI, 2025, 2, 10): (
        ['㉢ → ㉣ → ㉡ → ㉠'],
        '산수유 3~4월, 이팝나무 5~6월, 쉬땅나무 6~7월, 금목서 9~10월에 핀다.',
    ),
    (SI, 2023, 2, 2): (
        ['① 일반수종(조개모양) : 깊이 A/2, 아래쪽을 A/4만큼 둥글게 깎아 낸 형태',
         '② 심근성 수종(팽이모양) : 위쪽 A/2, 아래쪽 A/2로 아래가 뾰족한 형태',
         '③ 천근성 수종(접시모양) : 깊이 A/2의 납작한 형태'],
        '세 형태 모두 분의 너비는 A다.',
    ),
    (SI, 2023, 4, 6): (
        ['건축·공공시설물 등의 물리적 환경을 비롯하여 행정·교육·복지 등의 사회적 '
         '환경 가치를 높이는 데 적용한다.'],
        None,
    ),
}

for (name, y, r, n), (items, ref_head) in FIX.items():
    q = GisaEssayQuestion.objects.get(certification__name=name, year=y, round=r, number=n)
    if q.answer_items == items:
        print(f'{name} {y}-{r} {n}번 — 이미 같다. 건너뛴다.')
        continue
    ref = q.reference or ''
    if ref_head and ref_head not in ref:
        ref = (ref_head + (' ' + ref if ref else '')).strip()
    per = float(q.points) / len(items)
    print(f'── {name} {y}-{r} {n}번 ({q.qtype}, {q.points}점 → 항목 {len(items)}개 × {per:.2f}점)')
    for it in items:
        print('  ', it)
    if ref_head:
        print('   「해설」', ref[:80], '…')
    if APPLY:
        q.answer_items = items
        q.answer_text = ''
        q.reference = ref
        q.save(update_fields=['answer_items', 'answer_text', 'reference'])

print('\n반영했다.' if APPLY else '\n미반영 — --apply 로 넣는다.')
