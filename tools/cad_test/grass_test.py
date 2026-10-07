# -*- coding: utf-8 -*-
"""잔디 붓 — 문지르면 풀포기가 한 묶음으로 생기는가(대표님 2026-10)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
ok = True
with Cad(size=(1400, 900)) as c:
    c.zoom(50, 50, 6); c.key('j')
    c.drag([(30 + i * 1.0, 50 + (i % 3) * 0.3) for i in range(40)])
    g = [o for o in c.doc()['ops'] if o.get('grass')]
    print('포기', len(g), '묶음', {o['grp'] for o in g}, c.errors)
    ok &= len(g) > 10 and len({o['grp'] for o in g}) == 1 and not c.errors
    a, b = c.S(26, 42), c.S(74, 58)
    c.pg.screenshot(path=os.path.join(OUT, 'grass.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
