# -*- coding: utf-8 -*-
"""[eq] 자동 판정에서 빠진 조경 실기 답 2건을 손으로 맞춘다.

wrap_ls_eq.py 는 '한글이 35% 이하인 줄'만 수식으로 본다. 설명 문장이 상자에
들어가는 것을 막는 규칙인데, 라벨이 한글인 짧은 식은 함께 걸러진다.

  조경기사 2023-4 5번   '일 최대이용객 = 연간이용자수 × 최대일률 = 54,000 × 1/60'
                        → 한글 40%. 1/60 이 분수로 서지 않았다
  조경산업기사 2023-4 3번 ② 농약 희석량 공식 — 서술형이라 애초에 대상이 아니었다.
                        묻는 것이 둘이라 항목도 둘로 가른다

  python fix_ls_frac_rest.py [--apply]
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

FIX = {
    ('조경기사', 2023, 4, 5): [
        '계산)\n'
        '최대일 이용객은 연간 이용객에 최대일률을 곱한다.\n'
        '[eq]일 최대이용객 = 연간이용자수 × 최대일률\n'
        '  = 54,000 × 1/60 = **900명**[/eq]',
        '답) 최대일 이용객수 900명',
    ],
    ('조경산업기사', 2023, 4, 3): [
        '① 천적을 이용하는 방법은 생물학적 방제다.',
        # 항이 한글이면 qtext 의 'a / b' 규칙이 분수로 세우지 않는다(_FRAC_TERM).
        # 그런 자리는 [frac]분자|분모[/frac] 로 적어 준다.
        '② 물의 희석량\n'
        '[eq]희석량(ml, g) = 농약량 × ([frac]농약주성분농도(%)|추천농도(%)[/frac] − 1) × 비중[/eq]',
    ],
}

for key, items in FIX.items():
    name, y, r, n = key
    q = GisaEssayQuestion.objects.get(certification__name=name, year=y, round=r, number=n)
    if q.answer_items == items:
        print(f'{name} {y}-{r} {n}번 — 이미 같다. 건너뛴다.')
        continue
    print(f'── {name} {y}-{r} {n}번')
    for it in items:
        print(it)
    if APPLY:
        q.answer_items = items
        q.answer_text = ''
        q.save(update_fields=['answer_items', 'answer_text'])

print('\n반영했다.' if APPLY else '\n미반영 — --apply 로 넣는다.')
