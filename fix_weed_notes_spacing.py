"""잡초 카드 교수 메모의 띄어쓰기를 바로잡는다.

원본 슬라이드에서 한 낱말이 줄바꿈으로 쪼개져 있던 것을, 텍스트로 옮길 때
줄바꿈을 공백으로 바꾸면서 '가장자리 에' 처럼 낱말 가운데가 벌어졌다.
아래 목록은 원본 글자 층과 대조해 눈으로 가려낸 것이다 — 낱말이 쪼개진
곳만 붙이고, 원래 낱말 사이 공백('검은 갈색' 등)은 손대지 않는다.

  python fix_weed_notes_spacing.py            # 확인만
  python fix_weed_notes_spacing.py --apply    # DB 반영
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from exam.models import WeedCard  # noqa: E402

SUBJECT_PK = 51

# 카드번호: [(고칠 것, 바뀔 것), ...]
FIXES = {
    1:   [('포자식물이므 로', '포자식물이므로')],
    7:   [('있는 지 먼저 확 인하여', '있는지 먼저 확인하여')],
    8:   [('구부러 져 있다', '구부러져 있다')],
    11:  [('‘로제트 형’', '‘로제트형’')],
    13:  [('바로 붙 어 있다', '바로 붙어 있다'),
          ('어긋나 기로 난다', '어긋나기로 난다'),
          ('꽃대 에 꽃이', '꽃대에 꽃이'),
          ('(갈 퀴손', '(갈퀴손')],
    18:  [('갈고리 모양 의 가시', '갈고리 모양의 가시')],
    20:  [('끝이 둔 a 하고', '끝이 둔하고')],
    22:  [('‘고 맙다’해서', '‘고맙다’해서')],
    28:  [('윗 쪽 은 평평하다', '윗쪽은 평평하다')],
    29:  [('잎을 가 지고 있음', '잎을 가지고 있음')],
    31:  [('3~7개 정 도 핀다', '3~7개 정도 핀다'),
          ('포인 트', '포인트')],
    32:  [('검은 색 이다', '검은 색이다')],
    33:  [('가장자리 에 톱니부분', '가장자리에 톱니부분')],
    34:  [('입모양의 차 이로', '입모양의 차이로')],
    35:  [('적다(듬 성듬성', '적다(듬성듬성')],
    36:  [('꽃차례(하늘 을 향해)', '꽃차례(하늘을 향해)')],
    46:  [('꽃이 잎 보다 낮거나', '꽃이 잎보다 낮거나')],
    57:  [('‘털진 득찰’', '‘털진득찰’')],
    62:  [('벼도 같 이 쓰러짐', '벼도 같이 쓰러짐')],
    105: [('작 으면 민들레', '작으면 민들레')],
}


def main():
    apply = '--apply' in sys.argv
    n_card, n_fix, miss = 0, 0, []
    for card_no, pairs in sorted(FIXES.items()):
        c = WeedCard.objects.get(subject_id=SUBJECT_PK, card_no=card_no)
        text = c.notes
        for old, new in pairs:
            if old not in text:
                miss.append((card_no, c.name, old))
                continue
            text = text.replace(old, new)
            n_fix += 1
            print(f'  {card_no:4d} {c.name:10s} "{old}" → "{new}"')
        if text != c.notes:
            n_card += 1
            if apply:
                c.notes = text
                c.save(update_fields=['notes'])
    print(f'\n{n_card}개 카드 / {n_fix}곳', '반영함' if apply else '(--apply 로 반영)')
    if miss:
        print('원문에 없어 건너뜀:', miss)


main()
