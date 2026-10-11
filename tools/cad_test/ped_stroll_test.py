# -*- coding: utf-8 -*-
"""보행동선 띠 폭 1~7m · 산책동선(한 줄 · 사다리) · 공간 고르면 묶음 전체(대표님 2026-10).

맞춤 배율(확대하지 않음) 빈 A2 1:400 에서 네모·자유곡선 윤곽·한쪽 변·점 찍기로 그려 찍고,
공간을 그려 선택 도구로 바깥 줄을 누르면 안쪽 줄까지 함께 골라지는지 본다.
    python tools/cad_test/ped_stroll_test.py [--port 8117]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)
port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 8099
ok = True


def last_arrow(c):
    a = [o for o in c.doc()['ops'] if o.get('arrow')]
    return a[-1] if a else None


def setk(c, kind, mode, pw=''):
    c.pg.select_option('#fawK', kind); c.pg.select_option('#fawM', mode); c.pg.select_option('#fawPW', pw); c.pg.wait_for_timeout(150)


with Cad(None, port=port, size=(1440, 900)) as c:
    c.key('a')
    res = []
    # 네모 — 보행동선 1·4·7m, 산책동선 그린 대로·4m (긴 쪽 40m 가로, 세로 5m 로 끌기)
    for i, (kind, pw, want) in enumerate([('ped', 'm1', 1), ('ped', 'm4', 4), ('ped', 'm7', 7), ('stroll', '', 5), ('stroll', 'm4', 4)]):
        y = 20 + i * 12
        setk(c, kind, 'box', pw)
        c.drag([(20, y), (40, y + 2.5), (60, y + 5)])
        o = last_arrow(c); W = o and o['arrow']['wmm'] * 0.4
        res.append((kind, pw, o and o['arrow']['kind'], round(W or 0, 2)))
        ok &= bool(o) and o['arrow']['kind'] == kind and abs(W - want) < 0.05
    # 자유곡선 윤곽 — 산책동선(그린 대로 ≈ 4m), 보행동선 고른 폭 2m
    for j, (kind, pw) in enumerate([('stroll', ''), ('ped', 'm2')]):
        y = 90 + j * 14
        setk(c, kind, 'free', pw)
        ring = [(75 + t, y) for t in range(0, 41, 2)] + [(115, y + 2), (115, y + 4)] + [(115 - t, y + 4) for t in range(0, 41, 2)] + [(75, y + 2), (75, y + 0.3)]
        c.drag(ring)
        o = last_arrow(c); res.append(('outline', kind, pw, o and o['arrow']['kind'], o and round(o['arrow']['wmm'] * 0.4, 2)))
        ok &= bool(o) and o['arrow']['kind'] == kind and (pw != 'm2' or abs(o['arrow']['wmm'] * 0.4 - 2) < 0.05)
    # 한쪽 변 — 산책동선, 3m 고정
    setk(c, 'stroll', 'edge', 'm3')
    c.drag([(75, 130), (90, 131), (110, 128)]); c.key('Enter')
    c.click(95, 136)
    o = last_arrow(c); res.append(('edge', o and o['arrow'].get('kind'), o and o['arrow'].get('edge'), o and round(o['arrow']['wmm'] * 0.4, 2)))
    ok &= bool(o) and o['arrow']['kind'] == 'stroll' and o['arrow'].get('edge') and abs(o['arrow']['wmm'] * 0.4 - 3) < 0.05
    # 점 찍기 — 산책동선 5m, 한쪽 방향
    setk(c, 'stroll', 'pts', 'm5'); c.pg.uncheck('#fawB')
    for q in [(75, 150), (95, 145), (115, 152)]: c.click(*q)
    c.key('Enter')
    o = last_arrow(c); res.append(('pts', o and o['arrow']['kind'], o and o['arrow']['both'], o and round(o['arrow']['wmm'] * 0.4, 2)))
    ok &= bool(o) and o['arrow']['kind'] == 'stroll' and abs(o['arrow']['wmm'] * 0.4 - 5) < 0.05
    print(*res, sep='\n')
    c.shot(os.path.join(OUT, 'ped_stroll_fit.png'))
    a, b = c.S(15, 12), c.S(120, 160)
    c.pg.screenshot(path=os.path.join(OUT, 'ped_stroll_area.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
    # 공간 — 네모로 그리고 선택 도구로 바깥 줄을 누른다
    c.key('Escape'); c.key('k')
    c.drag([(130, 20), (145, 30), (160, 40)])
    sp = [o for o in c.doc()['ops'] if o.get('space')]
    c.key('v'); c.click(130, 30)                         # 바깥 줄 왼쪽 변
    red = c.pg.evaluate("[...document.querySelectorAll('#cadSvg [stroke]')].filter(e => /c62828|e53935|d32f2f|f00|red/i.test(e.getAttribute('stroke'))).length")
    a, b = c.S(125, 15), c.S(165, 45)
    c.pg.screenshot(path=os.path.join(OUT, 'space_select.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
    c.key('Delete')
    left = [o for o in c.doc()['ops'] if o.get('space')]
    print('공간 줄', len(sp), '→ 지운 뒤', len(left), '빨간 줄', red)
    ok &= len(sp) >= 2 and len(left) == 0
    print('오류', c.errors); ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
