# -*- coding: utf-8 -*-
"""[box] 안에 든 표를 마크다운 표로 바꾼다.

같은 Shannon 문제인데 회차마다 저장 형식이 달랐다 — 2023-3은 마크다운
표라 제대로 그려지고, 2017-3은 '구분 | A군집 | B군집' 이 글자 그대로,
2011-2는 파이프 기호까지 화면에 노출됐다. 데이터가 같으면 보이는 것도
같아야 한다.

[box]는 지문 박스이지 표 렌더러가 아니다. 표는 [box] 밖으로 꺼내
마크다운 표로 두면 _tables_anywhere 가 <table> 로 그려 준다.

pk 가 로컬 6 / 서버 3 으로 달라 (year, round, number) 로 찾는다.
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


def to_md_table(block):
    """박스 안 표 덩어리 → 마크다운 표. 표가 아니면 None."""
    rows = [l.strip() for l in block.strip().split('\n') if l.strip()]
    if len(rows) < 2:
        return None
    cells = []
    for r in rows:
        if set(r) <= set('|-: '):          # 이미 있는 구분행은 버리고 다시 만든다
            continue
        c = [x.strip() for x in r.strip('|').split('|')]
        if len(c) < 2:
            return None
        cells.append(c)
    if len(cells) < 2:
        return None
    width = max(len(c) for c in cells)
    cells = [c + [''] * (width - len(c)) for c in cells]
    out = ['| ' + ' | '.join(cells[0]) + ' |',
           '|' + '---|' * width]
    for c in cells[1:]:
        out.append('| ' + ' | '.join(c) + ' |')
    return '\n'.join(out)


def main():
    apply = '--apply' in sys.argv
    n = 0
    for q in Q.objects.filter(source='기출').order_by('-year', '-round'):
        text = q.text or ''
        new = text
        for m in re.finditer(r'\[box\](.*?)\[/box\]', text, re.S):
            tbl = to_md_table(m.group(1))
            if tbl:
                # 표는 박스 밖으로 — 박스는 지문용이지 표 렌더러가 아니다
                new = new.replace(m.group(0), '\n' + tbl)
        new = re.sub(r'\n{3,}', '\n\n', new).strip()
        if new == text:
            continue
        n += 1
        print(f'  {q.year}-{q.round} #{q.number} [{q.qtype}]')
        if apply:
            q.text = new
            q.save(update_fields=['text'])
    print(f'{"반영" if apply else "대상"} {n}건')
    if not apply:
        print('(--apply 로 반영)')


if __name__ == '__main__':
    main()
