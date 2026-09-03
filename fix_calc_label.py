# -*- coding: utf-8 -*-
"""계산 문항 답 항목의 라벨을 '계산)' '답)' 형태로 바꾼다.

  계산\n…   →  계산)\n…
  답 : …    →  답) …
"""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q


def relabel(items):
    out = []
    for s in items:
        # 앞서 잘못 붙어 중복된 '계산)\n계산' 을 하나로 정리한다
        s = re.sub(r'^(?:계산\)?\s*\n)+', '', s)
        s = re.sub(r'^답\s*[):：]\s*', '', s)
        out.append(s)
    if len(out) == 2:
        body, ans = out
        out = ['계산)\n' + body.strip(), '답) ' + ans.strip()]
    return out


def main():
    apply = '--apply' in sys.argv
    n = 0
    for q in Q.objects.filter(source='기출', qtype='계산'):
        items = list(q.answer_items or [])
        new = relabel(items)
        if new == items:
            continue
        n += 1
        print(f'  {q.year}-{q.round} #{q.number}')
        if apply:
            q.answer_items = new
            q.save(update_fields=['answer_items'])
    print(f'{"반영" if apply else "대상"} {n}건')
    if not apply:
        print('(--apply 로 반영)')


if __name__ == '__main__':
    main()
