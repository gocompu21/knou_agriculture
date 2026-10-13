# -*- coding: utf-8 -*-
"""동선 화살표 '점 찍기'가 '자유곡선'처럼 매끄럽게 굽는지(대표님 2026-10).

맞춤 배율(확대하지 않음) 빈 A2 1:400 에서 같은 S자·ㄱ자 길을
왼쪽은 점 찍기(곡선 체크), 오른쪽은 자유곡선(손으로 그은 듯 떨림 섞어 끌기)으로 그려 나란히 찍는다.
보행동선 2m · 주동선 · 산책동선 2m. 곡선을 끈 점 찍기는 곧은 꺾은선인지도 본다.
    python tools/cad_test/arrow_pts_free_test.py [--port 8099] [--tag 이름] [--pw m2|'']
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)
port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 8099
PW = sys.argv[sys.argv.index('--pw') + 1] if '--pw' in sys.argv else 'm2'   # 보행·산책동선 띠 폭('' = 그린 대로 → 13mm)
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'now'
ok = True
S_PTS = [(0, 0), (12, -6), (24, 0), (36, 6), (48, 0)]          # S자(물결)
L_PTS = [(0, -6), (0, 6), (24, 6)]                            # ㄱ자(꺾임 하나)
Z_PTS = [(0, 0), (16, 0), (16, 10), (34, 10)]                 # ㄹ자(꺾임 둘)


def hand(P, seed=1):
    """찍은 점을 손으로 따라 그은 것처럼 — 0.3m 간격 꺾은선 + 작은 떨림(꺾인 자리는 손이 조금 둥글린다)."""
    rnd = random.Random(seed); out = []
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        d = math.hypot(x1 - x0, y1 - y0); n = max(2, int(d / 0.3))
        for i in range(n):
            t = i / n; out.append((x0 + (x1 - x0) * t + rnd.uniform(-0.08, 0.08), y0 + (y1 - y0) * t + rnd.uniform(-0.08, 0.08)))
    out.append(P[-1]); return out


def ring(H, h):
    """손으로 그은 중심선 → 그 둘레를 대충 두른 윤곽(보행·산책동선 자유곡선은 윤곽을 그린다)."""
    def off(sg):
        o = []
        for i, q in enumerate(H):
            a, b = H[max(0, i - 3)], H[min(len(H) - 1, i + 3)]
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
            o.append((q[0] - dy / L * h * sg, q[1] + dx / L * h * sg))
        return o
    A, B = off(1), off(-1)[::-1]
    return A + B + [A[0]]


def setk(c, kind, mode, pw='', curve=True):
    c.pg.select_option('#fawK', kind); c.pg.select_option('#fawM', mode); c.pg.wait_for_timeout(80)
    if c.pg.is_visible('#fawPW'): c.pg.select_option('#fawPW', pw)
    (c.pg.check if curve else c.pg.uncheck)('#fawC'); c.pg.wait_for_timeout(150)


def last(c):
    a = [o for o in c.doc()['ops'] if o.get('arrow')]
    return a[-1] if a else None


def resample(pts, step):
    out = [pts[0]]; acc = 0
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1]); t = step - acc
        while t <= d:
            out.append((a[0] + (b[0] - a[0]) * t / d, a[1] + (b[1] - a[1]) * t / d)); t += step
        acc = d - (t - step)
    return out


def max_turn(pts, step=1.0):
    """중심선을 1m(1:400 종이 2.5mm) 간격으로 다시 찍어 이웃 마디 사이 가장 큰 꺾임(도) — 각지면 크다."""
    pts = resample(pts, step); m = 0
    for a, b, d in zip(pts, pts[1:], pts[2:]):
        u = (b[0] - a[0], b[1] - a[1]); v = (d[0] - b[0], d[1] - b[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-9 or lv < 1e-9: continue
        m = max(m, math.degrees(math.acos(max(-1, min(1, (u[0] * v[0] + u[1] * v[1]) / lu / lv)))))
    return m


METHODS = [('pts', '점 찍기'), ('fpts', '자유곡선(점 찍기)'), ('free', '자유곡선(끌기)')]
with Cad(None, port=port, size=(1440, 900)) as c:
    c.key('a')
    blocks = [('ped', PW, 12), ('main', '', 62), ('stroll', PW, 112)]
    res = []
    for kind, pw, y0 in blocks:
        for mi, (mode, mname) in enumerate(METHODS):
            for j, (name, P) in enumerate([('S', S_PTS), ('L', L_PTS), ('Z', Z_PTS)]):
                Q = [(15 + j * 60 + x, y0 + mi * 16 + y) for x, y in P]
                setk(c, kind, mode, pw)
                if mode == 'free':
                    c.drag(hand(Q, seed=j + 1) if kind == 'main' else ring(hand(Q, seed=j + 1), 1.0))   # 보행·산책동선 자유곡선(끌기)은 띠 윤곽을 대충 두른다
                else:
                    for q in Q: c.click(*q, wait=100)
                    c.key('Enter')
                o = last(c); t = max_turn(o['pts']) if o else 999
                res.append((kind, mname, name, len(o['pts']) if o else 0, round(t, 1), o and o['arrow'].get('wmm')))
                if mode == 'fpts': ok &= bool(o) and t < 25 and (kind == 'main' or abs(o['arrow']['wmm'] - (13 if not PW else int(PW[1:]) / 0.4)) < 0.05)
                if mode == 'pts': ok &= bool(o) and len(o['pts']) > len(P)   # 기존 점 찍기(곡선) 그대로 — Catmull 10등분
    print(*res, sep=chr(10))
    c.key('Escape'); c.pg.mouse.move(5, 5); c.pg.wait_for_timeout(200)
    c.shot(os.path.join(OUT, f'arrow_pts_free_{tag}_fit.png'))
    for kind, pw, y0 in blocks:
        a, b = c.S(8, y0 - 9), c.S(200, y0 + 42)
        c.pg.screenshot(path=os.path.join(OUT, f'arrow_pts_free_{tag}_{kind}.png'), clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]})
    for kind, pw, y0 in blocks:                           # 자세히(확대) — 모양 비교용
        c.zoom(100, y0 + 16, 3)
        c.shot(os.path.join(OUT, f'arrow_pts_free_{tag}_{kind}_zoom.png'))
        c.pg.mouse.move(*c.S(100, y0 + 16))
        for _ in range(3): c.pg.mouse.wheel(0, 300); c.pg.wait_for_timeout(80)
        c.pg.wait_for_timeout(200)
    print('오류', c.errors); ok &= not c.errors

with Cad(None, port=port, size=(1440, 900)) as c:
    c.key('a'); res = []
    # 곡선 끔 — 점 찍기는 찍은 점 그대로(곧은 꺾은선), 자유곡선(점 찍기)는 곡선 칸과 상관없이 매끄럽게
    for mode in ('pts', 'fpts'):
        setk(c, 'ped', mode, 'm2', curve=False)
        y = 20 if mode == 'pts' else 50
        for q in [(15, y), (15, y + 16), (39, y + 16)]: c.click(*q, wait=100)
        c.key('Enter')
        o = last(c); res.append(('곡선 끔', mode, len(o['pts']), round(max_turn(o['pts']), 1)))
        ok &= len(o['pts']) == 3 if mode == 'pts' else max_turn(o['pts']) < 20
    # 차량동선을 고르면 자유곡선(점 찍기)는 숨고 점 찍기로 돌아간다
    c.pg.select_option('#fawK', 'carb'); c.pg.wait_for_timeout(100)
    hid = c.pg.evaluate("document.querySelector('#fawM option[value=fpts]').hidden")
    res.append(('차량동선에서 숨김', hid)); ok &= hid
    # 미리보기 = 결과(자유곡선 점 찍기, 보행동선 2m): 넷째 점에 마우스를 둔 미리보기와 확정을 같은 자리에서 찍는다
    setk(c, 'ped', 'fpts', 'm2')
    for q in [(80, 30), (92, 24), (104, 30)]: c.click(*q, wait=100)
    c.pg.mouse.move(*c.S(116, 36)); c.pg.wait_for_timeout(200)
    a, b = c.S(74, 16), c.S(124, 44)
    clip = {'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]}
    c.pg.screenshot(path=os.path.join(OUT, f'arrow_pts_free_{tag}_preview.png'), clip=clip)
    c.click(116, 36, wait=100); c.key('Enter'); c.pg.mouse.move(5, 5); c.pg.wait_for_timeout(200)
    c.pg.screenshot(path=os.path.join(OUT, f'arrow_pts_free_{tag}_commit.png'), clip=clip)
    print(*res, sep=chr(10)); print('오류', c.errors); ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
