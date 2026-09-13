# -*- coding: utf-8 -*-
"""조경산업기사 2023-2회 2번(뿌리분 3형태) — 그림을 답으로 옮기고 다시 그린다.

두 가지를 고친다.

① **그림이 곧 답이다.** 문제가 "뿌리분의 형태를 그리고 크기의 비율도
   기입하시오" 라고 묻는데 그림이 문제문에 붙어 있어 답을 미리 보여 줬다.
   표·계산식처럼 항목으로 쪼갤 수 없는 답은 `answer_text` 에 둔다(학습·목록
   화면 모두 answer_text 를 qtext 로 렌더한다).

② **도형이 교재와 다르다.** 교재 원도는 곡선이 하나도 없다 — 셋 모두 너비 A
   의 직사각형에서 아래를 **각진 V자**로 좁혀 내리고, 천근성만 V 없이 납작한
   직사각형이다. 이름('조개모양'·'접시모양')에 이끌려 Q 곡선과 둥근 사발로
   그렸던 것을 바로잡는다. 답 항목의 '둥글게' 서술도 함께 고친다.

  python fix_ls_rootball.py           # 검증만
  python fix_ls_rootball.py --apply   # DB 반영
"""
import os
import re
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from add_ls_figures import FIG            # noqa: E402
from gisa.models import GisaEssayQuestion  # noqa: E402

KEY = 'ls-2023-2-si-2-rootball'
ITEMS = [
    '① 일반수종 : 너비 A, 위쪽 A/2 는 수직으로 내리고 그 아래를 A/4 깊이의 V자로 '
    '좁혀 내린 형태 (전체 깊이 3A/4)',
    '② 심근성 수종 : 너비 A, 위쪽 A/2 는 수직으로 내리고 그 아래를 A/2 깊이의 V자로 '
    '좁혀 내린 형태 (전체 깊이 A)',
    '③ 천근성 수종 : 너비 A, 깊이 A/2 의 납작한 직사각형 형태',
]


def main():
    apply_ = '--apply' in sys.argv
    q = GisaEssayQuestion.objects.get(
        certification__name='조경산업기사', source='기출',
        year=2023, round=2, number=2)

    # ① 문제문에서 그림을 걷어낸다 (앞뒤 빈 줄까지)
    text = re.sub(r'\n*\[svg\].*?\[/svg\]\n*', '\n', q.text, flags=re.S).strip()
    # ② 답 자리에 새로 그린 그림을 둔다
    answer_text = '[svg]%s[/svg]' % FIG[KEY]

    changes = []
    if text != q.text:
        changes.append('문제문에서 그림을 걷어냄')
    if answer_text != q.answer_text:
        changes.append('답에 그림을 넣음(새로 그린 것)')
    if ITEMS != q.answer_items:
        changes.append('답 항목 서술을 교재 도형에 맞춤')

    if not changes:
        print('바뀔 것이 없다.')
        return 0

    print('조경산업기사 2023-2 2번')
    for c in changes:
        print('  -', c)
    print()
    print('[문제문]');  print(text)
    print('\n[답 항목]')
    for a in ITEMS:
        print(' ', a)
    print(f'\n[답 그림] {KEY} — {len(answer_text)}자')

    if apply_:
        q.text, q.answer_text, q.answer_items = text, answer_text, ITEMS
        q.save(update_fields=['text', 'answer_text', 'answer_items'])
        print('\n반영했다.')
    else:
        print('\n(미반영 — --apply 로 넣는다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
