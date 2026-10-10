# -*- coding: utf-8 -*-
"""길 끝(화살촉) 곁에서 직각으로 갈라지는 짧은 길 — ㄱ자로 뭉치지 않고 T자로 붙는가(대표님 2026-10)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
doc = {'v': 1, 'sheet': 'a2-400', 'seq': 10, 'syms': {}, 'pts': [],
       'ops': [{'id': 1, 't': 'free', 'pts': [[20, 50], [64, 50]], 'ls': 'solid', 'w': 'p9', 'arrow': {'kind': 'carb', 'both': False, 'none': False, 'wmm': 13, 'seed': 3}, 'tl': 0}]}
ok = True
with Cad(doc, size=(1400, 900)) as c:
    c.zoom(55, 46, 5); c.key('a')
    c.pg.select_option('#fawK', 'carb'); c.pg.select_option('#fawM', 'box'); c.pg.wait_for_timeout(200)
    c.drag([(55, 47.6), (57, 45), (59.5, 41)])
    o = [x for x in c.doc()['ops'] if x.get('arrow') and x['id'] != 1]
    print(o and (o[-1]['pts'], o[-1]['arrow']), c.errors)
    ok &= bool(o) and o[-1]['arrow'].get('tee') and not c.errors
    a, b = c.S(40, 34), c.S(72, 56)
    c.pg.screenshot(path=os.path.join(OUT, 'car_stub_end.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
