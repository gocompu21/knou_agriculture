# -*- coding: utf-8 -*-
"""면적형 수종 지시선 — 체크 없이 부들·갈대 + 25 를 넣어도 '부들-25/㎡' / 규격은 같은 자리에서(대표님 2026-10)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
doc = {'v': 1, 'sheet': 'a2-400', 'seq': 10, 'syms': {},
       'pts': [{'n': 1, 'x': 40, 'y': 60}, {'n': 2, 'x': 60, 'y': 60}],
       'ops': [{'id': 1, 't': 'line', 'a': 1, 'b': 2, 'ls': 'solid', 'w': 'p5', 'grp': 1, 'gname': '다각선', 'poly': True, 'tl': 0}]}
ok = True
with Cad(doc, ls={'cadLeadKind': 'plant', 'cadLeadType': 'ur', 'cadLeadArea': ''}) as c:
    c.zoom(45, 55, 6); c.key('l'); c.click(40, 60)
    c.pg.fill('#fdCnt', '25'); c.pg.fill('#fdName', '부들'); c.pg.keyboard.press('Tab'); c.pg.fill('#fdSpec', '4치포트')
    c.click(40, 50)
    t = c.texts(); print(t)
    ok &= [x[0] for x in t] == ['부들-25/㎡', '4치포트'] and abs(t[0][1] - t[1][1]) < 1e-6
    print('페이지 오류', c.errors or '없음'); ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
