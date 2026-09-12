# -*- coding: utf-8 -*-
"""조경(산업)기사 실기 문항의 그림을 자작 SVG로 그려 넣는다.

판독 단계에서는 [svg]키[/svg] 로 자리만 잡아 두었다. 이 스크립트가 그 자리를
실제 SVG 본문으로 바꾼다. qtext 필터가 [svg]…[/svg] 안의 <svg> 를 통과시킨다.

  python add_ls_figures.py            # 바뀔 문항만 보여 준다
  python add_ls_figures.py --apply    # DB 반영
  python add_ls_figures.py --html out.html   # 그림만 모아 확인용 HTML

제도(製圖)형 그림이라 수치·치수가 정확해야 한다. 생성 모델 대신 직접 그리는 이유다.
그린 뒤에는 반드시 브라우저로 띄워 눈으로 검수한다 — 숫자·치수·구도·라벨 잘림.
"""
import argparse
import io
import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import GisaEssayQuestion          # noqa: E402

F = ('font-family="\'Malgun Gothic\',\'Apple SD Gothic Neo\',sans-serif" '
     'font-size="11"')
INK, G, G2, BR, RED = '#222', '#1b4332', '#2d6a4f', '#8b6b3d', '#c62828'


def svg(w, h, body):
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'xmlns="http://www.w3.org/2000/svg" {F}>'
            f'<rect width="{w}" height="{h}" fill="#fff"/>{body}</svg>')


def dim_h(x1, x2, y, label, color=INK):
    """가로 치수선."""
    return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{x1}" y1="{y-4}" x2="{x1}" y2="{y+4}" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{x2}" y1="{y-4}" x2="{x2}" y2="{y+4}" stroke="{color}" stroke-width="0.8"/>'
            f'<text x="{(x1+x2)/2}" y="{y-5}" text-anchor="middle" fill="{color}">{label}</text>')


def dim_v(y1, y2, x, label, color=INK):
    """세로 치수선 — 라벨은 선 왼쪽에 눕혀 쓴다."""
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{x-4}" y1="{y1}" x2="{x+4}" y2="{y1}" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{x-4}" y1="{y2}" x2="{x+4}" y2="{y2}" stroke="{color}" stroke-width="0.8"/>'
            f'<text x="{x-6}" y="{(y1+y2)/2}" text-anchor="middle" fill="{color}" '
            f'transform="rotate(-90 {x-6} {(y1+y2)/2})">{label}</text>')


HATCH = ('<defs><pattern id="hx" width="7" height="7" patternTransform="rotate(45)" '
         'patternUnits="userSpaceOnUse">'
         '<line x1="0" y1="0" x2="0" y2="7" stroke="#8b968f" stroke-width="1.4"/>'
         '</pattern>'
         '<marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
         '<path d="M0,0 L8,4 L0,8 z" fill="#2d6a4f"/></marker></defs>')

FIG = {}

# ── 1. 점고법 4×4 격자 (20m×20m, 가운데 구획은 보존지역이라 제외) ──────────
def _grid_square():
    S, x0, y0 = 70, 62, 56
    elev = [['16', '16', '15', '15'],
            ['16', '16', '16', '14'],
            ['16', '15', '15', '14'],
            ['14', '15', '16', '15']]
    b = [HATCH]
    b.append(f'<rect x="{x0+S}" y="{y0+S}" width="{S}" height="{S}" fill="url(#hx)"/>')
    for i in range(4):
        b.append(f'<line x1="{x0}" y1="{y0+i*S}" x2="{x0+3*S}" y2="{y0+i*S}" '
                 f'stroke="{INK}" stroke-width="1.2"/>')
        b.append(f'<line x1="{x0+i*S}" y1="{y0}" x2="{x0+i*S}" y2="{y0+3*S}" '
                 f'stroke="{INK}" stroke-width="1.2"/>')
    for r in range(4):
        for c in range(4):
            x, y = x0 + c * S, y0 + r * S
            b.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{INK}"/>')
            b.append(f'<text x="{x}" y="{y-9}" text-anchor="middle" fill="{G}" '
                     f'font-weight="700">{elev[r][c]}</text>')
    b.append(dim_h(x0, x0 + S, y0 - 28, '20m'))
    b.append(dim_v(y0, y0 + S, x0 - 22, '20m'))
    b.append(f'<text x="{x0+1.5*S}" y="{y0+1.5*S+4}" text-anchor="middle" fill="#6b7770" '
             f'font-size="10">보존지역</text>')
    b.append(f'<text x="{x0+3*S}" y="{y0+3*S+26}" text-anchor="end" fill="#666" '
             f'font-size="10">단위 : m (계획고 15m)</text>')
    return svg(300, 306, ''.join(b))


FIG['ls-2023-1-si-1-grid'] = _grid_square()

# ── 2. 점고법 ㄱ자 격자 (2m×2m, 계획고 40m) ────────────────────────────────
def _grid_ell():
    S, x0, y0 = 68, 58, 58
    top = ['40.0', '40.6', '41.5']
    mid = ['39.4', '41.5', '39.6', '38.0']
    bot = ['39.5', '40.0', '41.0', '39.0']
    b = []
    for c in range(2):
        b.append(f'<rect x="{x0+c*S}" y="{y0}" width="{S}" height="{S}" fill="none" '
                 f'stroke="{INK}" stroke-width="1.2"/>')
    for c in range(3):
        b.append(f'<rect x="{x0+c*S}" y="{y0+S}" width="{S}" height="{S}" fill="none" '
                 f'stroke="{INK}" stroke-width="1.2"/>')
    for c, v in enumerate(top):
        x = x0 + c * S
        b.append(f'<circle cx="{x}" cy="{y0}" r="2.2" fill="{INK}"/>')
        b.append(f'<text x="{x}" y="{y0-9}" text-anchor="middle" fill="{G}" font-weight="700">{v}</text>')
    for c, v in enumerate(mid):
        x = x0 + c * S
        b.append(f'<circle cx="{x}" cy="{y0+S}" r="2.2" fill="{INK}"/>')
        b.append(f'<text x="{x}" y="{y0+S-9}" text-anchor="middle" fill="{G}" font-weight="700">{v}</text>')
    for c, v in enumerate(bot):
        x = x0 + c * S
        b.append(f'<circle cx="{x}" cy="{y0+2*S}" r="2.2" fill="{INK}"/>')
        b.append(f'<text x="{x}" y="{y0+2*S+16}" text-anchor="middle" fill="{G}" font-weight="700">{v}</text>')
    b.append(dim_h(x0, x0 + S, y0 - 30, '2m'))
    b.append(dim_v(y0, y0 + S, x0 - 20, '2m'))
    b.append(f'<text x="{x0+4*S-8}" y="{y0+2*S+36}" text-anchor="end" fill="#666" '
             f'font-size="10">단위 : m (계획고 40m)</text>')
    return svg(340, 236, ''.join(b))


FIG['ls-2023-1-gi-10-grid'] = _grid_ell()

# ── 3. 사각뿔대 터파기 — 위가 넓고 아래가 좁은 구덩이 ──────────────────────
# 등각으로 보되, 아랫면이 윗면 '안쪽 아래'에 오도록 해야 구덩이로 읽힌다.
def _frustum():
    # 윗면 4000(가로) × 3000(세로), 아랫면 3000 × 2000, 깊이 2000
    TL, TR = (58, 62), (238, 62)          # 윗면 뒤쪽 두 점
    TR2, TL2 = (286, 104), (106, 104)     # 윗면 앞쪽 두 점 (오른쪽 아래로 밀림)
    BL, BR = (112, 150), (232, 150)       # 아랫면 뒤쪽
    BR2, BL2 = (264, 178), (144, 178)     # 아랫면 앞쪽
    p = lambda *pts: ' '.join(f'{x},{y}' for x, y in pts)      # noqa: E731
    b = [
        f'<polygon points="{p(TL, TR, TR2, TL2)}" fill="#f2f7f2" stroke="{INK}" stroke-width="1.3"/>',
        f'<polygon points="{p(BL, BR, BR2, BL2)}" fill="#e4ece4" stroke="{INK}" stroke-width="1.3"/>',
        # 옆면 네 모서리
        f'<line x1="{TL[0]}" y1="{TL[1]}" x2="{BL[0]}" y2="{BL[1]}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{TR[0]}" y1="{TR[1]}" x2="{BR[0]}" y2="{BR[1]}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{TR2[0]}" y1="{TR2[1]}" x2="{BR2[0]}" y2="{BR2[1]}" stroke="{INK}" stroke-width="1.2"/>',
        f'<line x1="{TL2[0]}" y1="{TL2[1]}" x2="{BL2[0]}" y2="{BL2[1]}" stroke="{INK}" stroke-width="1.2"/>',
        # 치수
        dim_h(TL[0], TR[0], 44, '4000', G),
        f'<text x="264" y="82" fill="{G}" font-weight="700">3000</text>',
        f'<text x="188" y="168" text-anchor="middle" fill="{G}" font-weight="700">3000</text>',
        f'<text x="252" y="196" fill="{G}" font-weight="700">2000</text>',
        dim_v(62, 150, 36, '2000', G),
        f'<text x="300" y="210" text-anchor="end" fill="#666" font-size="10">단위 : mm</text>',
    ]
    return svg(310, 220, ''.join(b))


FIG['ls-2023-4-si-8-frustum'] = _frustum()

# ── 4. 벽면녹화 3형태 — 세 방식이 한눈에 갈리도록 ──────────────────────────
def _wall():
    b = [HATCH]
    for i, kind in enumerate(['stick', 'twine', 'hang']):
        ox = 14 + i * 112
        wx = ox + 58                      # 벽체 왼쪽 면
        b.append(f'<rect x="{wx}" y="26" width="16" height="132" fill="#e9e9e4" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
        b.append(f'<line x1="{ox+6}" y1="158" x2="{ox+94}" y2="158" stroke="{INK}" stroke-width="1.4"/>')
        b.append(f'<rect x="{ox+6}" y="158" width="88" height="11" fill="url(#hx)"/>')
        if kind == 'stick':               # 흡착등반형 — 벽면에 딱 붙어 오른다
            b.append(f'<line x1="{wx-2}" y1="152" x2="{wx-2}" y2="36" stroke="{G2}" '
                     f'stroke-width="2.4" marker-end="url(#arw)"/>')
            for y in (60, 82, 104, 126, 146):
                b.append(f'<ellipse cx="{wx-9}" cy="{y}" rx="7" ry="4.5" fill="{G}"/>')
                b.append(f'<line x1="{wx-3}" y1="{y}" x2="{wx-1}" y2="{y}" stroke="{G2}" stroke-width="1"/>')
            b.append(f'<text x="{ox+50}" y="186" text-anchor="middle" fill="#555" font-size="10">'
                     f'벽면에 직접 부착</text>')
        elif kind == 'twine':             # 권만등반형 — 보조재를 감고 오른다
            for y in range(40, 156, 14):  # 보조재(격자)
                b.append(f'<line x1="{wx-20}" y1="{y}" x2="{wx-2}" y2="{y}" stroke="{BR}" stroke-width="1"/>')
            for x in (wx - 18, wx - 10, wx - 4):
                b.append(f'<line x1="{x}" y1="34" x2="{x}" y2="156" stroke="{BR}" stroke-width="1"/>')
            b.append(f'<path d="M{wx-6} 154 C {wx-26} 136, {wx-2} 118, {wx-22} 100 '
                     f'C {wx-2} 82, {wx-26} 64, {wx-8} 42" fill="none" stroke="{G2}" '
                     f'stroke-width="2.4" marker-end="url(#arw)"/>')
            for y in (70, 96, 124, 148):
                b.append(f'<ellipse cx="{wx-26}" cy="{y}" rx="7" ry="4.5" fill="{G}"/>')
            b.append(f'<text x="{ox+50}" y="186" text-anchor="middle" fill="#555" font-size="10">'
                     f'보조재를 감고 오름</text>')
        else:                             # 하수형 — 위에서 아래로 늘어뜨린다
            b.append(f'<rect x="{wx-14}" y="14" width="44" height="13" fill="#d5d5cd" '
                     f'stroke="{INK}" stroke-width="1"/>')
            b.append(f'<text x="{wx+8}" y="10" text-anchor="middle" fill="#555" font-size="9">플랜터</text>')
            b.append(f'<path d="M{wx-6} 28 C {wx-22} 60, {wx-4} 92, {wx-18} 132" fill="none" '
                     f'stroke="{G2}" stroke-width="2.4" marker-end="url(#arw)"/>')
            for y in (52, 78, 104, 126):
                b.append(f'<ellipse cx="{wx-22}" cy="{y}" rx="7" ry="4.5" fill="{G}"/>')
            b.append(f'<text x="{ox+50}" y="186" text-anchor="middle" fill="#555" font-size="10">'
                     f'위에서 늘어뜨림</text>')
        b.append(f'<text x="{ox+50}" y="208" text-anchor="middle" fill="{INK}" font-size="13">'
                 f'( {"㉠㉡㉢"[i]} )</text>')
    return svg(348, 218, ''.join(b))


FIG['ls-2023-1-si-2-wall'] = _wall()

# ── 5. 뿌리분 3형태 (조개·팽이·접시) ───────────────────────────────────────
def _rootball():
    A, b = 80, []
    # 문제문·답이 '일반수종' 이라 그림도 같은 말을 쓴다 — 그림만 '보통수종' 이면
    # 세 형태를 짝지을 때 한 박자 걸린다.
    labels = ['① 일반수종 (조개모양)', '② 심근성 (팽이모양)', '③ 천근성 (접시모양)']
    for i, kind in enumerate(['clam', 'top', 'dish']):
        ox = 34 + i * 118                 # 왼쪽에 치수선 자리를 넉넉히
        x1, x2, ty = ox, ox + A, 52
        half = A / 2
        b.append(f'<line x1="{x1-10}" y1="{ty}" x2="{x2+10}" y2="{ty}" stroke="{INK}" stroke-width="1.3"/>')
        if kind == 'clam':
            d = (f'M{x1} {ty} L{x1} {ty+half} Q{x1+A/2} {ty+half+A/4+10} {x2} {ty+half} '
                 f'L{x2} {ty} Z')
            b.append(dim_v(ty, ty + half, x1 - 14, 'A/2', G))
            b.append(dim_v(ty + half, ty + half + A / 4, x1 - 14, 'A/4', G))
        elif kind == 'top':
            d = f'M{x1} {ty} L{x1} {ty+half} L{x1+A/2} {ty+A} L{x2} {ty+half} L{x2} {ty} Z'
            b.append(dim_v(ty, ty + half, x1 - 14, 'A/2', G))
            b.append(dim_v(ty + half, ty + A, x1 - 14, 'A/2', G))
        else:
            d = (f'M{x1} {ty} L{x1} {ty+half*0.4} Q{x1+A/2} {ty+half+8} {x2} {ty+half*0.4} '
                 f'L{x2} {ty} Z')
            b.append(dim_v(ty, ty + half, x1 - 14, 'A/2', G))
        b.append(f'<path d="{d}" fill="#efe6d8" stroke="{BR}" stroke-width="1.6"/>')
        b.append(f'<line x1="{x1+A/2}" y1="{ty}" x2="{x1+A/2}" y2="{ty-18}" stroke="{BR}" stroke-width="3"/>')
        b.append(dim_h(x1, x2, ty - 26, 'A', G))
        b.append(f'<text x="{x1+A/2}" y="{ty+A+34}" text-anchor="middle" fill="{INK}" '
                 f'font-size="10">{labels[i]}</text>')
    return svg(388, 200, ''.join(b))


FIG['ls-2023-2-si-2-rootball'] = _rootball()

# ── 6. 천공시비 ────────────────────────────────────────────────────────────
FIG['ls-2024-3-gi-1-fert'] = svg(330, 210, ''.join([
    HATCH,
    f'<ellipse cx="165" cy="60" rx="78" ry="38" fill="#e8f1e8" stroke="{G2}" stroke-width="1.3"/>',
    f'<rect x="160" y="60" width="10" height="72" fill="{BR}"/>',
    f'<line x1="40" y1="132" x2="290" y2="132" stroke="{INK}" stroke-width="1.4"/>',
    f'<rect x="40" y="132" width="250" height="14" fill="url(#hx)"/>',
    ''.join(f'<rect x="{x-3}" y="132" width="6" height="16" fill="#fff" stroke="{INK}" '
            f'stroke-width="1"/>' for x in (96, 120, 144, 186, 210, 234)),
    dim_h(165, 243, 176, 'R', G),
    dim_h(165, 204, 196, '1/2 R', G),
    f'<line x1="165" y1="132" x2="165" y2="200" stroke="#999" stroke-width="0.8" stroke-dasharray="4 3"/>',
    f'<line x1="243" y1="98" x2="243" y2="180" stroke="#999" stroke-width="0.8" stroke-dasharray="4 3"/>',
]))

# ── 7. 단곡선 — 교각 I 를 뚜렷하게 ────────────────────────────────────────
def _curve():
    B = (86, 186)
    P = (152, 44)      # B→P 접선 방향 (방위각 BP)
    E = (258, 92)      # 곡선 끝점 (방위각 BE 방향)
    O = (196, 220)     # 곡선 중심
    b = [
        f'<line x1="{B[0]}" y1="{B[1]}" x2="{B[0]}" y2="26" stroke="#aaa" stroke-width="1"/>',
        f'<polygon points="{B[0]},20 {B[0]-4},30 {B[0]+4},30" fill="#aaa"/>',
        f'<text x="{B[0]}" y="14" text-anchor="middle" fill="#666">N</text>',
        f'<line x1="{B[0]}" y1="{B[1]}" x2="{P[0]}" y2="{P[1]}" stroke="{INK}" stroke-width="1.4"/>',
        f'<text x="{P[0]+4}" y="{P[1]-4}" fill="{INK}" font-weight="700">P</text>',
        f'<line x1="{B[0]}" y1="{B[1]}" x2="{E[0]}" y2="{E[1]}" stroke="{INK}" stroke-width="1.4"/>',
        f'<text x="{E[0]+6}" y="{E[1]-2}" fill="{INK}" font-weight="700">E</text>',
        f'<circle cx="{B[0]}" cy="{B[1]}" r="3" fill="{INK}"/>',
        f'<text x="{B[0]-14}" y="{B[1]+6}" fill="{INK}" font-weight="700">B</text>',
        f'<path d="M{B[0]} {B[1]} Q 150 116 {E[0]} {E[1]}" fill="none" stroke="{G}" stroke-width="2.4"/>',
        f'<circle cx="{O[0]}" cy="{O[1]}" r="3" fill="{INK}"/>',
        f'<text x="{O[0]-12}" y="{O[1]+5}" text-anchor="middle" fill="{INK}" font-weight="700">O</text>',
        f'<line x1="{O[0]}" y1="{O[1]}" x2="{B[0]}" y2="{B[1]}" stroke="{G2}" stroke-width="1" stroke-dasharray="5 3"/>',
        f'<line x1="{O[0]}" y1="{O[1]}" x2="{E[0]}" y2="{E[1]}" stroke="{G2}" stroke-width="1" stroke-dasharray="5 3"/>',
        f'<text x="{(O[0]+E[0])/2+8}" y="{(O[1]+E[1])/2}" fill="{G2}" font-weight="700">R</text>',
        # 교각 I — 두 접선(BP·BE) 사이 각을 큰 호로
        f'<path d="M{B[0]+30} {B[1]-64} A 72 72 0 0 1 {B[0]+68} {B[1]-32}" fill="none" '
        f'stroke="{RED}" stroke-width="1.2"/>',
        f'<text x="{B[0]+64}" y="{B[1]-58}" fill="{RED}" font-weight="700">I</text>',

    ]
    return svg(330, 240, ''.join(b))


FIG['ls-2024-3-gi-12-curve'] = _curve()

# ── 8. 수준측량 단면 — 읽음값을 표척 옆으로 빼 겹치지 않게 ─────────────────
def _level():
    b = []
    b.append('<path d="M26 172 C 76 154, 116 180, 164 154 S 246 182, 306 160" fill="none" '
             f'stroke="{INK}" stroke-width="1.4"/>')
    pts = [(44, 170), (106, 166), (168, 154), (230, 172), (292, 162)]
    for i, (x, y) in enumerate(pts, 1):
        b.append(f'<rect x="{x-3}" y="{y-78}" width="6" height="78" fill="#fff" '
                 f'stroke="{INK}" stroke-width="1"/>')
        for k in range(1, 5):
            b.append(f'<line x1="{x-3}" y1="{y-78+k*16}" x2="{x+3}" y2="{y-78+k*16}" '
                     f'stroke="{INK}" stroke-width="0.7"/>')
        b.append(f'<text x="{x}" y="{y+16}" text-anchor="middle" fill="{INK}" '
                 f'font-weight="700">{i}</text>')
    for lx, ly in ((74, 120), (198, 112)):
        b.append(f'<rect x="{lx-13}" y="{ly-7}" width="26" height="11" fill="#dfe7df" '
                 f'stroke="{INK}" stroke-width="1"/>')
        b.append(f'<line x1="{lx}" y1="{ly+4}" x2="{lx}" y2="{ly+30}" stroke="{INK}" stroke-width="1"/>')
        b.append(f'<line x1="{lx-9}" y1="{ly+34}" x2="{lx+9}" y2="{ly+34}" stroke="{INK}" stroke-width="1"/>')
    b.append(f'<line x1="44" y1="120" x2="168" y2="120" stroke="#bbb" stroke-width="0.8" stroke-dasharray="4 3"/>')
    b.append(f'<line x1="168" y1="112" x2="292" y2="112" stroke="#bbb" stroke-width="0.8" stroke-dasharray="4 3"/>')
    # 읽음값 — 표척 좌우로 빼되 위아래로도 어긋나게 두어 서로 붙지 않게 한다
    reads = [(44, '1.95', 'end', -9, 114, G), (106, '2.05', 'start', 9, 154, INK),
             (168, '1.30', 'end', -9, 102, INK), (168, '1.35', 'end', -9, 136, G),
             (230, '1.90', 'start', 9, 152, INK), (292, '2.00', 'end', -9, 102, INK)]
    for x, v, anchor, dx, y, col in reads:
        b.append(f'<text x="{x+dx}" y="{y}" text-anchor="{anchor}" fill="{col}" '
                 f'font-weight="700">{v}</text>')
    b.append(f'<text x="318" y="200" text-anchor="end" fill="#666" font-size="10">'
             f'단위 : m · 초록 = 후시(B.S), 검정 = 전시(F.S)</text>')
    return svg(330, 208, ''.join(b))


FIG['ls-2025-1-gi-2-level'] = _level()

# ── 9. 수간주사 두 방식 ────────────────────────────────────────────────────
def _injection():
    b = [HATCH,
         f'<line x1="16" y1="172" x2="304" y2="172" stroke="{INK}" stroke-width="1.4"/>',
         f'<rect x="16" y="172" width="288" height="12" fill="url(#hx)"/>']
    for ox in (72, 216):                       # 수간 두 그루
        b.append(f'<path d="M{ox} 172 L{ox+2} 40 L{ox+28} 40 L{ox+30} 172 Z" fill="#efe6d8" '
                 f'stroke="{BR}" stroke-width="1.5"/>')
        for k in range(5):                     # 세로 결
            b.append(f'<path d="M{ox+5+k*5} 168 C {ox+7+k*5} 130, {ox+4+k*5} 90, {ox+7+k*5} 46" '
                     f'fill="none" stroke="{BR}" stroke-width="0.6" opacity="0.6"/>')
    # 왼쪽 — 주입기를 수간에 직접 꽂는다
    for y in (104, 134):
        b.append(f'<line x1="46" y1="{y}" x2="74" y2="{y+6}" stroke="{INK}" stroke-width="2"/>')
        b.append(f'<rect x="26" y="{y-8}" width="22" height="12" rx="2" fill="#dfe7df" '
                 f'stroke="{INK}" stroke-width="1"/>')
        b.append(f'<circle cx="74" cy="{y+6}" r="2.6" fill="{RED}"/>')
    b.append(f'<text x="87" y="200" text-anchor="middle" fill="{INK}" font-size="11">'
             f'주입기를 수간에 꽂는 방식</text>')
    # 오른쪽 — 약액 용기를 높이 매달아 관으로 넣는다
    b.append(f'<line x1="182" y1="44" x2="252" y2="44" stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<line x1="196" y1="44" x2="196" y2="52" stroke="{INK}" stroke-width="1"/>')
    b.append(f'<path d="M186 52 h20 l-3 30 h-14 z" fill="#e8f1e8" stroke="{G2}" stroke-width="1.2"/>')
    b.append(f'<path d="M196 82 C 196 112, 206 122, 218 130" fill="none" stroke="{G2}" stroke-width="1.8"/>')
    b.append(f'<circle cx="218" cy="130" r="2.6" fill="{RED}"/>')
    b.append(f'<text x="231" y="200" text-anchor="middle" fill="{INK}" font-size="11">'
             f'약액을 매달아 넣는 방식</text>')
    return svg(320, 212, ''.join(b))


FIG['ls-2025-3-gi-11-injection'] = _injection()


_KEY = re.compile(r'^ls-(\d{4})-(\d)-(gi|si)-(\d+)-')
_BLOCK = re.compile(r'\[svg\].*?\[/svg\]', re.DOTALL)
CERT = {'gi': '조경기사', 'si': '조경산업기사'}


def refresh(apply_):
    """이미 넣은 그림을 지금 코드의 그림으로 갈아 끼운다.

    `[svg]키[/svg]` 자리표시는 한 번 넣으면 사라지므로, 그림을 고쳐도 위의 넣기
    경로로는 다시 들어가지 않는다. 다행히 키에 `ls-연도-회차-자격증-번호` 가 들어
    있어 어느 문항의 그림인지 알 수 있다 — 그 문항의 `[svg]…[/svg]` 덩어리를
    통째로 바꾼다. 한 문항에 그림이 둘이면 어느 것인지 가릴 수 없어 건너뛴다.
    """
    n = 0
    for k, svg in FIG.items():
        m = _KEY.match(k)
        if not m:
            print(f'  !! 키에서 문항을 못 읽는다: {k}')
            continue
        year, rnd, cert, num = int(m.group(1)), int(m.group(2)), CERT[m.group(3)], int(m.group(4))
        q = GisaEssayQuestion.objects.filter(certification__name=cert, year=year,
                                             round=rnd, number=num).first()
        if not q:
            print(f'  !! 문항 없음: {k}')
            continue
        blocks = _BLOCK.findall(q.text or '')
        if len(blocks) != 1:
            print(f'  !! [svg] 덩어리가 {len(blocks)}개라 건너뛴다: {k}')
            continue
        new = q.text.replace(blocks[0], f'[svg]{svg}[/svg]')
        if new == q.text:
            continue
        n += 1
        print(f'  {"갈아 끼움" if apply_ else "바뀔 것"}: {k} ({cert} {year}-{rnd} {num}번)')
        if apply_:
            q.text = new
            q.save(update_fields=['text'])
    print(f'\n{n}건' + (' 반영했다.' if apply_ else ' (미반영 — --apply 로 넣는다)'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--refresh', action='store_true',
                    help='이미 넣은 그림을 지금 코드의 그림으로 갈아 끼운다')
    ap.add_argument('--html', help='그림만 모아 볼 HTML 경로')
    args = ap.parse_args()

    if args.refresh:
        refresh(args.apply)
        return

    if args.html:
        parts = ['<meta charset="utf-8"><style>body{font:14px system-ui;padding:18px}'
                 'figure{margin:0 0 30px}figcaption{color:#555;margin-bottom:6px}'
                 'svg{width:100%;max-width:720px;height:auto}</style>']
        for k, s in FIG.items():
            parts.append(f'<figure><figcaption>{k}</figcaption>{s}</figure>')
        io.open(args.html, 'w', encoding='utf-8').write('\n'.join(parts))
        print(f'{args.html} — 그림 {len(FIG)}개')

    done = 0
    for q in GisaEssayQuestion.objects.filter(certification__name__startswith='조경',
                                              text__contains='[svg]'):
        for k in re.findall(r'\[svg\]([\w-]+)\[/svg\]', q.text):
            if k not in FIG:
                print(f'  !! 그림 없음: {k} ({q.year}-{q.round} {q.number}번)')
                continue
            if args.apply:
                q.text = q.text.replace(f'[svg]{k}[/svg]', f'[svg]{FIG[k]}[/svg]')
                q.save(update_fields=['text'])
            print(f'  {"넣음" if args.apply else "넣을 것"}: {k} '
                  f'({q.certification.name} {q.year}-{q.round} {q.number}번)')
            done += 1
    print(f'\n{done}건' + (' 반영했다.' if args.apply else ' (미반영 — --apply 로 넣는다)'))


if __name__ == '__main__':
    main()
