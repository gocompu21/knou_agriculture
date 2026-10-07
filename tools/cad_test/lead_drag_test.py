# -*- coding: utf-8 -*-
"""지시선 글 끌기 시험 — 시작점은 그대로, 꺾는 점·가로선·글만 따라오는가(대표님 2026-10).

    ../../../venv/Scripts/python.exe tools/cad_test/lead_drag_test.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad

doc = {'v': 1, 'sheet': 'a2-400', 'seq': 10, 'syms': {},
       'pts': [{'n': 1, 'x': 40, 'y': 60}, {'n': 2, 'x': 60, 'y': 60}],
       'ops': [{'id': 1, 't': 'line', 'a': 1, 'b': 2, 'ls': 'solid', 'w': 'p5', 'grp': 1, 'gname': '다각선', 'poly': True, 'tl': 0}]}
ok = True
def lead_pts(c):
    d = c.doc(); P = {p['n']: (p['x'], p['y']) for p in d['pts']}
    return [(P[o['a']], P[o['b']]) for o in d['ops'] if o.get('lead') and not o.get('leadGuide')]
with Cad(doc, ls={'cadLeadKind': 'plant', 'cadLeadType': 'ur', 'cadLeadArea': '', 'cadLeadFree': '0'}) as c:
    c.zoom(45, 52, 6)
    c.key('l'); c.click(40, 60)
    c.pg.fill('#fdCnt', '9'); c.pg.fill('#fdName', '갈대'); c.pg.keyboard.press('Tab'); c.pg.fill('#fdSpec', '4치포트')
    c.click(40, 50)
    t0 = c.texts(); L0 = lead_pts(c); print('그린 뒤', t0, L0)
    c.key('v')
    tx, ty = t0[0][1] + 0.6, t0[0][2] - 0.3            # 위 줄 글 위를 잡아
    c.drag([(tx, ty), (tx + 2, ty - 2), (tx + 4, ty - 5)])   # 오른쪽 위로 끈다
    t1 = c.texts(); L1 = lead_pts(c); print('끈 뒤', t1, L1)
    ok &= any(abs(a[0] - 40) < 1e-6 and abs(a[1] - 60) < 1e-6 for seg in L1 for a in seg)   # 시작점 그대로
    ok &= abs((t1[0][2] - t0[0][2]) + 5) < 0.6           # 글이 위로 약 5m
    ok &= abs(t1[0][1] - t0[0][1]) < 1e-6                # 곧은 형 — 좌우로는 안 간다
    leg = [s for s in L1 if abs(s[0][0] - s[1][0]) < 1e-6]; ok &= bool(leg)   # 세로선은 여전히 곧다
    c.pg.keyboard.press('Control+z'); c.pg.wait_for_timeout(300)
    ok &= abs(c.texts()[0][2] - t0[0][2]) < 1e-6         # 되돌리기
    print('페이지 오류', c.errors or '없음'); ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
