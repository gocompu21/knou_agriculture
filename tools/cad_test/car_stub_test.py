# -*- coding: utf-8 -*-
"""차량동선에서 직각으로 짧게 갈라지는 길 — 네모를 길 위에서 끌기 시작하면 길에 직각으로 뻗는다(대표님 2026-10)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
# 1:400 · 폭 13mm = 5.2m 가로 길(y=50) 하나
doc = {'v': 1, 'sheet': 'a2-400', 'seq': 10, 'syms': {}, 'pts': [],
       'ops': [{'id': 1, 't': 'free', 'pts': [[20, 50], [70, 50]], 'ls': 'solid', 'w': 'p9', 'arrow': {'kind': 'carb', 'both': False, 'none': True, 'wmm': 13, 'seed': 3}, 'tl': 0}]}
ok = True
with Cad(doc, size=(1400, 900), ls={'cadAwKind': 'carb'}) as c:
    c.zoom(50, 52, 5); c.key('a')
    c.pg.select_option('#fawK', 'carb') if c.pg.locator('#fawK').count() else None
    c.pg.select_option('#fawM', 'box'); c.pg.wait_for_timeout(200)
    c.drag([(60, 52.4), (62, 56), (64.5, 61)])          # 길 아래 변에서 아래로 3m(폭 4.5m보다 짧다)
    o = [x for x in c.doc()['ops'] if x.get('arrow') and x['id'] != 1]
    print(o and o[-1]['pts'], o and o[-1]['arrow'].get('wmm'), c.errors)
    if o:
        (x0, y0), (x1, y1) = o[-1]['pts'][0], o[-1]['pts'][-1]
        ok &= abs(x0 - x1) < 1e-6 and abs(y1 - y0) > 2      # 세로로 뻗음
    else: ok = False
    a, b = c.S(50, 44), c.S(75, 66)
    c.pg.screenshot(path=os.path.join(OUT, 'car_stub.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
    ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
