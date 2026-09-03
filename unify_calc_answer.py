# -*- coding: utf-8 -*-
"""같은 주제의 계산 문항은 답 형식도 같아야 한다.

'1.5배 도달 연수'는 다섯 회차가 같은 계산인데 답이 제각각이었다 —
저장 위치(answer_items vs answer_text), 변수(n·t·x), 유니코드 첨자(ˣ·₀),
수식 박스 유무가 모두 달랐다. 채점 포인트 4단계로 통일한다.

회차마다 주는 로그값이 달라 ②만 갈린다 — ln1.5를 직접 주지 않는 회차는
ln3 − ln2 유도를 넣는다.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

BASE = [
    "① 계산식 : 초기 개체수를 N₀, n년 후를 N이라 하면 N = N₀(1 + r)^n 이므로, "
    "1.5배를 넘는 조건은 다음과 같다.\n[eq]1.01^n > 1.5[/eq]",
    "② 양변에 자연로그를 취한다.\n[eq]n × ln1.01 > ln1.5[/eq]",
    "③ 값을 대입한다.\n[eq]n > ln1.5 / ln1.01 = 0.4055 / 0.00995 ≒ 40.75[/eq]",
    "④ 답 : 40.75년을 넘어야 하므로 **41년**이다.",
]
DERIVE = ("② 양변에 자연로그를 취한다. ln1.5는 주어진 값에서 ln3 − ln2 로 유도한다."
          "\n[eq]n × ln1.01 > ln1.5 = ln3 − ln2 = 0.4055[/eq]")

# (연도, 회차, 문항번호) → ln1.5 유도가 필요한 회차인가.
# pk 는 로컬 6 / 서버 3 으로 달라 회차로 찾는다.
TARGETS = [((2024, 2, 2), True), ((2020, 3, 2), False), ((2018, 2, 4), False),
           ((2015, 1, 5), True), ((2005, 3, 4), False)]


def main():
    for (year, rnd, num), derive in TARGETS:
        q = Q.objects.filter(source='기출', year=year, round=rnd,
                             number=num, qtype='계산').first()
        if not q:
            print(f'  건너뜀: {year}-{rnd} #{num} 없음')
            continue
        items = list(BASE)
        if derive:
            items[1] = DERIVE
        q.answer_items = items
        q.answer_text = ''          # 풀이는 items 로 일원화
        q.save(update_fields=['answer_items', 'answer_text'])
        print(f'  통일 {q.year}-{q.round} #{q.number} ({len(items)}항목)')


if __name__ == '__main__':
    main()
