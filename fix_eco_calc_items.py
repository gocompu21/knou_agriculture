# -*- coding: utf-8 -*-
"""자연생태복원 계산 문항 중 [eq] 없이 남아 있던 2건을 같은 꼴로 맞춘다.

나머지 37건은 '계산)/답)' + [eq] 인데 이 둘만 answer_text 에 식이 통짜로 있고
answer_items 에는 결과만 있었다. 화면에서 식이 분수로 서지 않는다.
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
    9: ['계산)\n'
        '양단면평균법은 양 끝 단면적의 평균에 두 단면 사이의 거리를 곱한다.\n'
        '[eq]V = (A_{1} + A_{2}) / 2 × L\n'
        '  = (40 + 30) / 2 × 10 = 35 × 10 = **350m^{3}**[/eq]',
        '답) 토사량 350m^{3}'],
    10: ['계산)\n'
         '합리식에서 유역면적은 ha, 강우강도는 mm/hr 로 넣고 1/360 을 곱해 m^{3}/s 를 얻는다.\n'
         '[eq]Q = (1 / 360) × C × I × A\n'
         '  = (1 / 360) × 0.5 × 80 × 18 = 720 / 360 = **2.0m^{3}/s**[/eq]',
         '답) 최대유량 2.0m^{3}/s'],
}

for q in GisaEssayQuestion.objects.filter(
        certification__name='자연생태복원기사', qtype='계산', year__isnull=True).order_by('number'):
    items = FIX.get(q.number)
    if not items or '[eq]' in '\n'.join(q.answer_items or []):
        continue
    print(f'--- {q.number}번 ---')
    for it in items:
        print(it)
    if APPLY:
        q.answer_items = items
        q.answer_text = ''
        q.save(update_fields=['answer_items', 'answer_text'])
print('반영했다.' if APPLY else '미반영 — --apply 로 넣는다.')
