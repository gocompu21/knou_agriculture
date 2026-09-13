# -*- coding: utf-8 -*-
"""조경기사 실기 Chapter 01(구유형 적산) 문항의 그림을 그려 넣는다.

판독 단계에서 `[svg]ls-ch1-<번호>-<이름>[/svg]` 로 자리만 잡아 두었다. 이 스크립트가
그 자리를 실제 SVG 본문으로 바꾼다. 회차가 없는 묶음이라 `add_ls_figures.py` 의 키
규칙(`ls-연도-회차-자격증-번호`)을 쓸 수 없어 따로 둔다 — 여기서는 **문항 번호**로 찾는다.

  python add_ls_ch1_figures.py                # 무엇이 바뀔지만 보여 준다
  python add_ls_ch1_figures.py --apply        # DB 반영
  python add_ls_ch1_figures.py --html out.html --page  # 그림 + 원도 쪽을 나란히
  python add_ls_ch1_figures.py --only 7,13    # 일부만

**검수는 두 단계다. 둘째를 빠뜨리면 소용이 없다.**

  ① 브라우저로 띄워 본다 — 숫자·치수·라벨 잘림, 겹침, 넘침
  ② **원도(PDF 쪽)를 나란히 놓고 도형을 대조한다** — 곡선인가 각진 선인가,
     변의 수, 치수선이 붙은 자리

②를 건너뛰어 뿌리분 3형태(산기 2023-2 2번)를 통째로 틀린 적이 있다. 답에 적어 둔
'조개모양'이라는 **이름에 이끌려** 곡선으로 그렸는데 원도에는 곡선이 하나도 없었다.
화면에는 멀쩡히 나오므로 ①로는 절대 걸리지 않는다. `--page` 가 그 대조를 위해
교재 쪽 이미지를 그림 옆에 붙여 준다.

교재 쪽 ↔ PDF 쪽은 **PDF 쪽 = 교재 쪽 − 275** 다(PDF 78 = 교재 353).
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

from add_ls_figures import BR, G, G2, HATCH, INK, RED, dim_h, dim_v, elev, svg  # noqa: E402
from gisa.models import GisaEssayQuestion                                       # noqa: E402

CERT = '조경기사'
SOURCE = '적산'

FIG = {}          # 키 → SVG 본문
PAGE = {}         # 키 → 원도가 실린 PDF 쪽 (대조용)


def reg(key, page, body):
    FIG[key] = body
    PAGE[key] = page


# 문항 번호 → (문제문에 둘 그림, 답에 둘 그림)
#
# **그림이 곧 답인 문항은 문제문에 두면 안 된다.** "형태를 그리시오" 라고 묻는데
# 발문 아래에 답 그림이 붙어 있으면 풀어 볼 기회가 없다. 교재에서 그 그림이
# 「정답」 아래에 있는지 발문 아래에 있는지를 보고 가른다.
PLACE = {}


# ═══════════════════════════════════════════════════════════════════════════
#  그림
# ═══════════════════════════════════════════════════════════════════════════


def _dot(x, y, r=1.8):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}"/>'


def _lead(x1, y1, x2, y2, text, anchor='start', dx=4):
    """인출선 — 꺾인 선 끝에 글자. 원도가 재료명을 이렇게 단다."""
    return (f'<polyline points="{x1},{y1} {x2},{y2}" fill="none" stroke="{INK}" '
            f'stroke-width="0.7"/>{_dot(x1, y1, 1.5)}'
            f'<text x="{x2 + dx}" y="{y2 + 3.4}" text-anchor="{anchor}" '
            f'fill="{INK}" font-size="9">{text}</text>')


# ── 2번. 뿌리분 3형태 (접시분·보통분·조개분) — 답 ─────────────────────────
def _f2_rootball():
    """원도(교재 354쪽)에는 곡선이 없다. 셋 모두 너비 4d 의 직사각형에서
    아래를 각진 V자로 좁혀 내리고(보통분 d, 조개분 2d), 접시분만 V 가 없다.
    위에는 근원부(수간)를 가는 선 몇 줄로 그리고 그 너비를 d 로 잰다."""
    d = 18
    W, H = 4 * d, 2 * d
    TY, PITCH, X0 = 62, 124, 42
    b = []
    specs = [(0, None, '접시분(천근성수종)'),
             (d, 'd', '보통분(일반수종)'),
             (2 * d, '2d', '조개분(심근성수종)')]
    for i, (vee, vlab, title) in enumerate(specs):
        x1 = X0 + i * PITCH
        x2, cx = x1 + W, x1 + W / 2
        if vee:
            path = (f'M{x1} {TY} L{x1} {TY+H} L{cx} {TY+H+vee} '
                    f'L{x2} {TY+H} L{x2} {TY} Z')
            bottom = TY + H + vee
        else:
            path = f'M{x1} {TY} L{x1} {TY+H} L{x2} {TY+H} L{x2} {TY} Z'
            bottom = TY + H
        b.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
        # 근원부 — 가는 세로선 네 줄
        for k in range(4):
            sx = cx - d / 2 + k * d / 3
            b.append(f'<line x1="{sx}" y1="{TY}" x2="{sx}" y2="{TY-15}" '
                     f'stroke="{INK}" stroke-width="0.7"/>')
        b.append(dim_h(cx - d / 2, cx + d / 2, TY - 20, 'd', G))
        b.append(dim_v(TY, TY + H, x1 - 12, '2d', G))
        if vlab:
            b.append(dim_v(TY + H, bottom, x1 - 12, vlab, G))
        b.append(dim_h(x1, x2, bottom + 18, '4d', G))
        b.append(f'<text x="{cx}" y="{26}" text-anchor="middle" fill="{INK}" '
                 f'font-size="10.5" font-weight="700">{title}</text>')
    return svg(3 * PITCH + 10, 168, ''.join(b))


reg('ls-ch1-2-rootball', 79, _f2_rootball())


# ── 3번. 화강석판석 포장 단면도 — 답 ──────────────────────────────────────
def _f3_pavement():
    """위에서 아래로 판석 → 모르타르 → 와이어메쉬 → 콘크리트 → PE필름 →
    혼합골재 → 원지반. 얇은 층(PE필름 0.02mm)은 선 하나로 그리고, 두께 비는
    눈에 보이도록 조금 눌러 그렸다. 재료명은 원도처럼 위에 모아 인출선으로 잇는다.

    층 차례가 곧 답이다 — 여과·분리막이 어디 들어가는지를 묻는 문항이라
    PE필름을 콘크리트 **아래**, 혼합골재 **위**에 두는 것이 요점이다.
    """
    x1, x2 = 46, 312
    pats = ('<defs>'
            '<pattern id="c3a" width="6" height="6" patternTransform="rotate(45)" '
            'patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#8b968f" stroke-width="1.2"/></pattern>'
            '<pattern id="c3b" width="10" height="10" patternUnits="userSpaceOnUse">'
            '<circle cx="2" cy="3" r="1" fill="#9aa69e"/>'
            '<circle cx="7" cy="7" r="0.9" fill="#9aa69e"/>'
            '<path d="M4,8 l2.6,0 l-1.3,-2.4 z" fill="#b3bdb5"/></pattern>'
            '<pattern id="c3c" width="16" height="16" patternUnits="userSpaceOnUse">'
            '<path d="M0,16 L16,0 M0,0 L16,16" stroke="#9aa69e" stroke-width="1"/>'
            '</pattern>'
            '<pattern id="c3d" width="9" height="9" patternUnits="userSpaceOnUse">'
            '<path d="M0,4.5 L4.5,0 L9,4.5 M0,9 L4.5,4.5 L9,9" fill="none" '
            'stroke="#9aa69e" stroke-width="0.9"/></pattern></defs>')
    # (두께px, 채움, 치수라벨) — 위에서 아래로
    layers = [(16, 'url(#c3a)', '30'), (16, 'none', '30'),
              (40, 'url(#c3b)', '100'), (40, 'url(#c3c)', '100')]
    labels = ['THK 30 화강석 판석(300x300x30)', 'THK 30 모르타르', '#6 와이어메쉬',
              'THK 100 콘크리트 C종(1:3:6)', 'THK 0.02 PE필름(콘크리트 분리막)',
              'THK 100 혼합골재', '원지반 다짐']
    b = [pats]
    lx, ly0 = 162, 22
    for i, t in enumerate(labels):
        yy = ly0 + i * 13
        b.append(f'<line x1="{lx}" y1="{yy}" x2="{lx+8}" y2="{yy}" stroke="{INK}" '
                 f'stroke-width="0.8"/>'
                 f'<text x="{lx+12}" y="{yy+3.4}" fill="{INK}" font-size="9.5">{t}</text>')
    y = ly0 + len(labels) * 13 + 12
    for i, (h, fill, lab) in enumerate(layers):
        b.append(f'<rect x="{x1}" y="{y}" width="{x2-x1}" height="{h}" fill="{fill}" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
        b.append(dim_v(y, y + h, x1 - 13, lab, G))
        if i == 2:      # 콘크리트 윗면에 와이어메쉬
            b.append(f'<line x1="{x1+4}" y1="{y+3}" x2="{x2-4}" y2="{y+3}" '
                     f'stroke="{INK}" stroke-width="0.9" stroke-dasharray="7 4"/>')
        y += h
        if i == 2:      # 콘크리트 바로 아래가 분리막이다
            b.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" '
                     f'stroke-width="2.4"/>')
    b.append(f'<rect x="{x1}" y="{y}" width="{x2-x1}" height="28" '
             f'fill="url(#c3d)" stroke="{INK}" stroke-width="1.1"/>')
    y += 28
    b.append(f'<line x1="{lx+4}" y1="{ly0}" x2="{lx+4}" y2="{y}" stroke="{INK}" '
             f'stroke-width="0.7"/>')
    b.append(f'<text x="{(x1+x2)/2}" y="{y+24}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">화강석판석 포장 단면도　None Scale</text>')
    return svg(400, y + 36, ''.join(b))


reg('ls-ch1-3-pavement', 79, _f3_pavement())


# ── 6번. 이각지주목(문제 제시) / 삼각지주목(답) ───────────────────────────
def _ground(x1, x2, y, h=20):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" '
            f'stroke-width="1.3"/>'
            + ''.join(f'<line x1="{x}" y1="{y}" x2="{x-6}" y2="{y+h}" '
                      f'stroke="#9aa69e" stroke-width="0.8"/>'
                      for x in range(int(x1) + 6, int(x2), 11)))


def _trunk(cx, top, bottom, w=9):
    return (f'<path d="M{cx-w} {bottom} C{cx-w+2} {top+30} {cx-3} {top+20} {cx-3} {top} '
            f'M{cx+w} {bottom} C{cx+w-2} {top+30} {cx+3} {top+20} {cx+3} {top}" '
            f'fill="none" stroke="{BR}" stroke-width="1.4"/>')


def _f6_biangle():
    """문제가 참고하라고 준 이각지주목 — 단면도·평면도."""
    b = [_ground(20, 175, 150)]
    b.append(_trunk(98, 28, 150))
    # 이각 — 좌우 한 쌍
    for sx, ex in ((36, 84), (160, 112)):
        b.append(f'<line x1="{sx}" y1="{168}" x2="{ex}" y2="{62}" stroke="{INK}" '
                 f'stroke-width="2"/>')
    b.append(f'<rect x="{78}" y="{58}" width="{40}" height="6" fill="#fff" '
             f'stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<text x="{163}" y="{146}" fill="{INK}" font-size="9">F.L</text>')
    b.append(f'<text x="{98}" y="{192}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;단 면 도&gt;</text>')
    # 평면도 — 수관 테두리 안에 가로재 한 줄
    cx, cy = 285, 104
    b.append(f'<circle cx="{cx}" cy="{cy}" r="62" fill="none" stroke="{INK}" '
             f'stroke-width="1" stroke-dasharray="5 3"/>')
    b.append(f'<rect x="{cx-58}" y="{cy-7}" width="{116}" height="14" fill="#fff" '
             f'stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="13" ry="15" fill="#fff" '
             f'stroke="{BR}" stroke-width="1.4"/>')
    b.append(f'<text x="{cx}" y="{192}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;평 면 도&gt;</text>')
    return svg(360, 204, ''.join(b))


reg('ls-ch1-6-biangle', 80, _f6_biangle())


def _f6_stake():
    """답 — 삼각지주목. 원도는 단면도·평면도를 좌우로 놓지만, 재료명 인출선이
    길어 나란히 두면 글자가 손톱만 해진다. 위아래로 쌓아 각 그림을 크게 둔다."""
    b = []
    # ── 단면도 ──  1,500 = 150(위) + 1,100 + 250(묻힘)
    TOP, MEM, FL, BOT = 44, 57, 149, 174
    b.append(_ground(24, 186, FL))
    b.append(_trunk(105, 22, FL))
    for sx, ex in ((44, 86), (166, 124)):
        b.append(f'<line x1="{sx}" y1="{BOT}" x2="{ex}" y2="{TOP}" stroke="{INK}" '
                 f'stroke-width="2"/>')
    b.append(f'<rect x="{82}" y="{MEM-4}" width="{46}" height="8" fill="#fff" '
             f'stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<rect x="{99}" y="{MEM-6}" width="{12}" height="12" fill="{INK}"/>')
    b.append(dim_v(TOP, BOT, 18, '1,500', G))
    b.append(dim_v(TOP, MEM, 32, '150', G))
    b.append(dim_v(MEM, FL, 32, '1,100', G))
    b.append(dim_v(FL, BOT, 32, '250', G))
    b.append(f'<text x="{176}" y="{FL-3}" fill="{INK}" font-size="9">F.L</text>')
    b.append(_lead(105, MEM - 6, 196, 34, 'Ø6mm 새끼줄 감기'))
    b.append(_lead(124, MEM, 196, 48, '각재 45x45xL1,000'))
    b.append(_lead(90, MEM + 2, 196, 62, '철못 L=75'))
    b.append(_lead(150, 100, 196, 78, '각재 45x45xL1,500'))
    b.append(f'<text x="{105}" y="{198}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;단 면 도&gt;</text>')
    # ── 평면도 ── 가로재 셋이 정삼각형, 꼭짓점에서 비스듬한 각재가 뻗는다
    import math
    cx, cy, R = 100, 288, 44
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
           for a in (-90, 30, 150)]
    b.append(f'<circle cx="{cx}" cy="{cy}" r="70" fill="none" stroke="{INK}" '
             f'stroke-width="1" stroke-dasharray="5 3"/>')
    b.append('<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
             + f'" fill="none" stroke="{INK}" stroke-width="2"/>')
    for x, y in pts:
        ex, ey = cx + (x - cx) * 1.75, cy + (y - cy) * 1.75
        b.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                 f'stroke="{INK}" stroke-width="2"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#fff" stroke="{BR}" '
             f'stroke-width="1.4"/>')
    b.append(_lead(pts[1][0], pts[1][1], 196, 250, '각재 45x45xL1,000'))
    b.append(_lead(cx + 30, cy + 40, 196, 266, '각재 45x45xL1,500'))
    b.append(_lead(cx, cy - 11, 196, 282, 'Ø6mm 새끼줄 감기'))
    b.append(_lead(pts[2][0], pts[2][1], 196, 298, '철못 L=75'))
    b.append(f'<text x="{cx}" y="{372}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;평 면 도&gt;</text>')
    return svg(370, 384, ''.join(b))


reg('ls-ch1-6-stake', 81, _f6_stake())


# ── 7번. 등고선 평면 + 종단면 — 문제 제시 ─────────────────────────────────
def _f7_contour():
    """왼쪽은 A1~A6 등고선(20~70m), 오른쪽은 그 종단면. 정점 표고 74m 라
    맨 위 등고선(70)에서 꼭대기까지 4m 가 남는다 — 원도가 그 4 를 적어 둔다."""
    b = []
    cx, cy = 108, 132
    rings = [(88, 68), (74, 56), (60, 45), (46, 34), (31, 23), (17, 13)]
    names = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']
    lv = ['20', '30', '40', '50', '60', '70']
    for i, (rx, ry) in enumerate(rings):
        b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
        # 표고는 고리의 오른쪽 끝에, A 이름은 오른쪽 아래 비탈에 — 한자리에
        # 몰아 두면 안쪽 고리로 갈수록 글자가 겹쳐 읽히지 않는다
        b.append(f'<text x="{cx+rx+3:.0f}" y="{cy+3}" fill="{INK}" '
                 f'font-size="8.5">{lv[i]}</text>')
        b.append(f'<text x="{cx+rx*0.57:.0f}" y="{cy+ry*0.84+3:.0f}" '
                 f'text-anchor="middle" fill="{G}" font-size="8.5">{names[i]}</text>')
    # 종단면
    ox, base, step = 236, 214, 26
    for i, t in enumerate(lv):
        yy = base - i * step
        b.append(f'<line x1="{ox}" y1="{yy}" x2="{ox+130}" y2="{yy}" stroke="{INK}" '
                 f'stroke-width="0.9"/>')
        b.append(f'<text x="{ox-5}" y="{yy+3.4}" text-anchor="end" fill="{INK}" '
                 f'font-size="8.5">{t}</text>')
    apex = base - 5 * step - 11          # 70선에서 4m 더 위가 정점(74m)
    px = ox + 66                          # 꼭대기 자리
    b.append(f'<path d="M{ox} {base+10} C{ox+26} {base+2} {ox+45} {apex} {px} {apex} '
             f'C{px+21} {apex} {ox+106} {base+2} {ox+132} {base+10}" '
             f'fill="none" stroke="{INK}" stroke-width="1.5"/>')
    # 정점(74m)과 맨 위 등고선(70m) 사이 4m — 원뿔공식의 높이가 이 값이다.
    # 11px 밖에 안 되는 짧은 치수라 글자를 눕히면 선과 겹친다. 옆에 눕히지 않고 쓴다.
    b.append(f'<line x1="{px-14}" y1="{apex}" x2="{px-14}" y2="{base-5*step}" '
             f'stroke="{G}" stroke-width="0.8"/>'
             f'<line x1="{px-18}" y1="{apex}" x2="{px-10}" y2="{apex}" '
             f'stroke="{G}" stroke-width="0.8"/>'
             f'<line x1="{px-18}" y1="{base-5*step}" x2="{px-10}" y2="{base-5*step}" '
             f'stroke="{G}" stroke-width="0.8"/>'
             f'<text x="{px-21}" y="{apex+9}" text-anchor="end" fill="{G}" '
             f'font-size="8.5">4</text>')
    return svg(384, 244, ''.join(b))


reg('ls-ch1-7-contour', 81, _f7_contour())


# ── 공통: 네트워크 공정표 ─────────────────────────────────────────────────
def _network(nodes, edges, w, h, marks=None, cp=(), mark_pos=None):
    """결절점·화살선·소요일수. marks 가 있으면 각 결절점에 ET|LT 상자를 얹고,
    cp 에 든 변은 굵게 그린다(주공정선).

    mark_pos 로 상자 자리를 결절점마다 정한다('top' 기본, 'bottom'). 늘 위에
    두면 세로 화살선이나 소요일수 글자와 겹친다 — 원도도 ⑤ 만 아래에 둔다.
    화살촉은 userSpaceOnUse 라 선을 굵게 해도 부풀지 않는다.
    """
    b = ['<defs><marker id="nkarw" markerWidth="9" markerHeight="9" refX="8" '
         'refY="4.5" orient="auto" markerUnits="userSpaceOnUse">'
         '<path d="M0,0 L9,4.5 L0,9 z" fill="%s"/></marker></defs>' % INK]
    R = 11
    for a, z, lab, *rest in edges:
        dummy = bool(rest and rest[0])
        x1, y1 = nodes[a]
        x2, y2 = nodes[z]
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / d, dy / d
        sx, sy = x1 + ux * R, y1 + uy * R
        ex, ey = x2 - ux * (R + 4), y2 - uy * (R + 4)
        bold = (a, z) in cp
        b.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                 f'stroke="{INK}" stroke-width="{2.6 if bold else 1.2}" '
                 f'marker-end="url(#nkarw)"'
                 + (' stroke-dasharray="5 3"' if dummy else '') + '/>')
        if lab:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            b.append(f'<text x="{mx - uy * 11:.1f}" y="{my + ux * 11 + 3.4:.1f}" '
                     f'text-anchor="middle" fill="{INK}" font-size="10">{lab}</text>')
    for n, (x, y) in nodes.items():
        b.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="#fff" stroke="{INK}" '
                 f'stroke-width="1.3"/>'
                 f'<text x="{x}" y="{y + 3.6}" text-anchor="middle" fill="{INK}" '
                 f'font-size="10.5">{n}</text>')
        if marks and n in marks:
            te, tl = marks[n]
            bw = 17 if max(len(str(te)), len(str(tl))) < 3 else 22
            below = (mark_pos or {}).get(n) == 'bottom'
            bx = x - bw
            by = y + R + 4 if below else y - R - 19
            b.append(f'<rect x="{bx}" y="{by}" width="{bw * 2}" height="15" fill="#fff" '
                     f'stroke="{INK}" stroke-width="0.9"/>'
                     f'<line x1="{x}" y1="{by}" x2="{x}" y2="{by + 15}" stroke="{INK}" '
                     f'stroke-width="0.9"/>'
                     f'<text x="{x - bw / 2}" y="{by + 11}" text-anchor="middle" '
                     f'fill="{INK}" font-size="9.5">{te}</text>'
                     f'<text x="{x + bw / 2}" y="{by + 11}" text-anchor="middle" '
                     f'fill="{G}" font-size="9.5">{tl}</text>')
    return svg(w, h, ''.join(b))


# ── 13번. 삼각분할 격자 — 문제 제시 ───────────────────────────────────────
def _f13_grid():
    """6m × 5m 칸을 대각선으로 가른 삼각분할.

    **대각선 방향은 답의 계수표(1~8)에서 역산했다.** 한 꼭짓점에 모이는 삼각형
    수가 곧 그 점의 계수라, 계수가 맞으려면 대각선이 이 방향이어야 한다
    (Σh₁=0.4 · Σh₂=2.1 · Σh₃=1.2 · Σh₄=0.5 · Σh₅~₈=0.3 과 모두 들어맞는다).
    눈대중으로 그으면 문제가 통째로 달라진다.
    """
    CW, CH, X0, Y0 = 62, 50, 52, 52
    ev = [['0.40', '0.50', '0.30', '0.20', '0.30'],
          ['0.40', '0.30', '0.30', '0.30', '0.30'],
          ['0.30', '0.30', '0.20', '0.20', '0.40'],
          ['0.20', '0.30', '0.20']]
    # (띠, 칸) → 대각선 방향. '/' 는 오른쪽 위–왼쪽 아래, '\\' 는 왼쪽 위–오른쪽 아래
    diag = {(0, 0): '/', (0, 1): '/', (0, 2): '\\', (0, 3): '/',
            (1, 0): '/', (1, 1): '/', (1, 2): '/', (1, 3): '\\',
            (2, 0): '/', (2, 1): '\\'}
    cols = [4, 4, 2]                      # 띠마다 칸 수 (아래 띠는 왼쪽 둘만)
    b = []
    for band, nc in enumerate(cols):
        for c in range(nc):
            x, y = X0 + c * CW, Y0 + band * CH
            b.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" fill="none" '
                     f'stroke="{INK}" stroke-width="1.1"/>')
            if diag[(band, c)] == '/':
                b.append(f'<line x1="{x + CW}" y1="{y}" x2="{x}" y2="{y + CH}" '
                         f'stroke="{INK}" stroke-width="1"/>')
            else:
                b.append(f'<line x1="{x}" y1="{y}" x2="{x + CW}" y2="{y + CH}" '
                         f'stroke="{INK}" stroke-width="1"/>')
    for r, row in enumerate(ev):
        for c, v in enumerate(row):
            x, y = X0 + c * CW, Y0 + r * CH
            b.append(f'<circle cx="{x}" cy="{y}" r="2" fill="{INK}"/>')
            b.append(elev(x, y, v, dx=0 if c == 0 else 13, dy=-7))
    b.append(dim_h(X0, X0 + CW, Y0 - 26, '6m', G))
    b.append(dim_v(Y0, Y0 + CH, X0 - 24, '5m', G))
    b.append(f'<text x="{X0 + 4 * CW}" y="{Y0 + 3 * CH + 26}" text-anchor="end" '
             f'fill="#666" font-size="9.5">단위 : m</text>')
    return svg(X0 + 4 * CW + 26, Y0 + 3 * CH + 38, ''.join(b))


reg('ls-ch1-13-grid', 87, _f13_grid())


# ── 14번. 네트워크 공정표 — 문제(민 그림) / 답(TE·TL·주공정선) ────────────
_N14 = {1: (38, 122), 2: (150, 52), 3: (150, 122), 4: (150, 196),
        5: (270, 122), 6: (270, 52), 7: (376, 122)}
_E14 = [(1, 2, '5'), (2, 6, '4'), (6, 7, '4'), (1, 3, '5'), (3, 5, '3'),
        (5, 7, '8'), (1, 4, '10'), (4, 5, '16'), (4, 7, '3'), (5, 6, '7')]

reg('ls-ch1-14-network', 87, _network(_N14, _E14, 400, 232))
reg('ls-ch1-14-network-a', 87,
    _network(_N14, _E14, 400, 232,
             marks={1: (0, 0), 2: (5, 29), 3: (5, 23), 4: (10, 10),
                    5: (26, 26), 6: (33, 33), 7: (37, 37)},
             cp={(1, 4), (4, 5), (5, 6), (6, 7)},
             mark_pos={5: 'bottom'}))


# ── 16번. 인공지반 식재 단면 상세도 — 답 ──────────────────────────────────
def _f16_planting():
    """위에서 아래로 혼합객토(900) → 폴리펠트 여과층(7) → 자갈 배수층(300) →
    유공관(φ200) → 폴리피렌 차수매트(2) → 하부지반.

    바닥을 유공관 쪽으로 6% 기울여 물이 고이지 않게 하고, 차수매트는 그
    굴곡을 따라 끊김 없이 이어 그린다 — 평평하게 그리면 조건을 어긴 그림이다.
    """
    x1, x2 = 44, 306
    cx = (x1 + x2) / 2
    pats = ('<defs>'
            '<pattern id="p16a" width="9" height="9" patternUnits="userSpaceOnUse">'
            '<circle cx="2" cy="3" r="1" fill="#a8b0a6"/>'
            '<circle cx="6.5" cy="7" r="0.9" fill="#a8b0a6"/></pattern>'
            '<pattern id="p16b" width="13" height="13" patternUnits="userSpaceOnUse">'
            '<circle cx="4" cy="4" r="3" fill="none" stroke="#9aa69e" stroke-width="1"/>'
            '<circle cx="10" cy="10" r="2.4" fill="none" stroke="#9aa69e" '
            'stroke-width="1"/></pattern>'
            '<pattern id="p16c" width="9" height="9" patternUnits="userSpaceOnUse">'
            '<path d="M0,4.5 L4.5,0 L9,4.5 M0,9 L4.5,4.5 L9,9" fill="none" '
            'stroke="#9aa69e" stroke-width="0.9"/></pattern></defs>')
    TOP, SOIL, FELT, GRAV = 128, 66, 4, 34
    y1 = TOP + SOIL                 # 객토 아래 = 여과층
    y2 = y1 + FELT                  # 자갈층 위
    y3 = y2 + GRAV                  # 자갈층 아래(가장자리)
    sag = 15                        # 6% 물매로 가운데가 내려앉는 깊이
    b = [pats]
    b.append(f'<rect x="{x1}" y="{TOP}" width="{x2-x1}" height="{SOIL}" '
             f'fill="url(#p16a)" stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{FELT}" fill="#e6ece7" '
             f'stroke="{INK}" stroke-width="1.1"/>')
    # 자갈층 — 아래가 유공관 쪽으로 기운다
    b.append(f'<path d="M{x1} {y2} L{x2} {y2} L{x2} {y3} L{cx+26} {y3+sag} '
             f'L{cx-26} {y3+sag} L{x1} {y3} Z" fill="url(#p16b)" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    # 차수매트 — 굴곡을 따라 이어진다
    b.append(f'<path d="M{x1} {y3+7} L{cx-26} {y3+sag+7} L{cx+26} {y3+sag+7} '
             f'L{x2} {y3+7}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    b.append(f'<path d="M{x1} {y3+11} L{cx-26} {y3+sag+11} L{cx+26} {y3+sag+11} '
             f'L{x2} {y3+11} L{x2} {y3+40} L{x1} {y3+40} Z" fill="url(#p16c)" '
             f'stroke="{INK}" stroke-width="1.1"/>')
    b.append(f'<circle cx="{cx}" cy="{y3+sag-1}" r="9" fill="#fff" stroke="{INK}" '
             f'stroke-width="1.3"/>')
    for a in (-60, 0, 60, 120, 180, 240):
        import math
        ax, ay = cx + 9 * math.cos(math.radians(a)), y3 + sag - 1 + 9 * math.sin(math.radians(a))
        b.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="1.2" fill="{INK}"/>')
    # 6% 물매 표시
    for sx, ex in ((x1 + 26, cx - 30), (x2 - 26, cx + 30)):
        b.append(f'<line x1="{sx}" y1="{y3+4}" x2="{ex}" y2="{y3+sag+3}" stroke="{G}" '
                 f'stroke-width="0.9" marker-end="url(#arw)"/>')
    b.append(HATCH)
    b.append(f'<text x="{x1+50}" y="{y3+sag+18}" fill="{G}" font-size="9">6% 경사</text>')
    b.append(f'<text x="{x2-50}" y="{y3+sag+18}" text-anchor="end" fill="{G}" '
             f'font-size="9">6% 경사</text>')
    # 재료명 — 위에 모아 인출선으로 잇는다
    labels = ['THK 900 혼합토 객토층', 'THK 7 폴리펠트 여과층', 'THK 300 자갈 배수층',
              'φ200 유공관', 'THK 2 폴리피렌매트 차수층', '하부지반']
    lx = 150
    for i, t in enumerate(labels):
        yy = 20 + i * 13
        b.append(f'<line x1="{lx}" y1="{yy}" x2="{lx+8}" y2="{yy}" stroke="{INK}" '
                 f'stroke-width="0.8"/>'
                 f'<text x="{lx+12}" y="{yy+3.4}" fill="{INK}" font-size="9.5">{t}</text>')
    b.append(f'<line x1="{lx+4}" y1="20" x2="{lx+4}" y2="{y3+40}" stroke="{INK}" '
             f'stroke-width="0.7"/>')
    b.append(dim_v(TOP, y1, x1 - 13, '900', G))
    b.append(dim_v(y2, y3, x1 - 13, '300', G))
    b.append(dim_h(cx - 26, cx + 26, y3 + sag + 34, '600', G))
    b.append(f'<text x="{cx}" y="{y3+70}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">단면상세도　축척 1/20</text>')
    return svg(400, y3 + 82, ''.join(b))


reg('ls-ch1-16-planting', 89, _f16_planting())


# ── 19번. 종단 수준측량도 — 문제 제시 ─────────────────────────────────────
def _level_scene(w, h, ground, staffs, levels, reads, caption=None, cap_at='bottom'):
    """표척을 세우고 그 사이에 레벨을 놓은 측량도.

    ground  땅 윤곽 (x, y) 목록
    staffs  표척 x 좌표 목록 — 땅 위로 솟은 막대
    levels  레벨 (x, y) 목록 — 삼각대 위 망원경
    reads   (x, y, 글자) — 표척 읽은 값
    """
    b = []
    b.append('<polyline points="' + ' '.join(f'{x},{y}' for x, y in ground)
             + f'" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    b.append('<polygon points="' + ' '.join(f'{x},{y}' for x, y in ground)
             + f' {ground[-1][0]},{h} {ground[0][0]},{h}" fill="url(#gsoil)"/>')
    def gy(x):
        for (ax, ay), (bx, by) in zip(ground, ground[1:]):
            if ax <= x <= bx:
                return ay + (by - ay) * (x - ax) / (bx - ax)
        return ground[-1][1]
    for sx in staffs:
        b.append(f'<rect x="{sx-3}" y="{gy(sx)-86}" width="6" height="86" fill="#fff" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
    for lx, ly in levels:
        gyy = gy(lx)
        b.append(f'<line x1="{lx}" y1="{ly}" x2="{lx-11}" y2="{gyy}" stroke="{INK}" '
                 f'stroke-width="1"/>'
                 f'<line x1="{lx}" y1="{ly}" x2="{lx+11}" y2="{gyy}" stroke="{INK}" '
                 f'stroke-width="1"/>'
                 f'<line x1="{lx}" y1="{ly}" x2="{lx}" y2="{gyy}" stroke="{INK}" '
                 f'stroke-width="1"/>'
                 f'<rect x="{lx-11}" y="{ly-6}" width="22" height="9" fill="#fff" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
    for rx, ry, t in reads:
        b.append(f'<text x="{rx}" y="{ry}" text-anchor="middle" fill="{INK}" '
                 f'font-size="9.5">{t}</text>')
    if caption:
        # 측점 이름이 아래에 깔리므로 캡션을 바닥에 두면 겹친다 — 위로 뺀다
        if cap_at == 'top':
            b.append(f'<text x="{w-6}" y="18" text-anchor="end" fill="#666" '
                     f'font-size="9">{caption}</text>')
        else:
            b.append(f'<text x="{w/2}" y="{h-6}" text-anchor="middle" fill="#666" '
                     f'font-size="9">{caption}</text>')
    soil = ('<defs><pattern id="gsoil" width="7" height="7" patternUnits="userSpaceOnUse">'
            '<circle cx="2" cy="2" r="0.9" fill="#c3cbc4"/>'
            '<circle cx="5.5" cy="5" r="0.7" fill="#c3cbc4"/></pattern></defs>')
    return svg(w, h, soil + ''.join(b))


def _f19_level():
    """No.0 에서 No.5 까지 100m 를 재며 레벨을 세 번 옮긴 종단 수준측량도.

    표척 여덟 자루 가운데 **No.2 와 No.3+10 은 이기점(T.P)** 이라 전시·후시를
    함께 읽는다(2.354/1.906, 3.243/2.507). 나머지는 지나가며 읽은 중간점(I.P)이다.
    """
    XS = [30, 80, 130, 180, 235, 285, 340, 392]
    NAMES = ['No.0', 'No.1', 'No.1+12', 'No.2', 'No.3', 'No.3+10', 'No.4', 'No.5']
    g = [(16, 152), (60, 148), (110, 155), (160, 150), (210, 158), (260, 164),
         (310, 160), (360, 154), (410, 150)]
    levels = [(55, 118), (207, 124), (312, 121)]
    reads = [(30, 100, '2.390'), (80, 100, '1.675'), (130, 100, '3.064'),
             (180, 88, '2.354'), (180, 101, '1.906'),
             (235, 100, '2.358'),
             (285, 88, '3.243'), (285, 101, '2.507'),
             (340, 100, '1.643'), (392, 100, '1.807')]
    # 이름이 긴 이기점은 한 줄 내려 이웃과 겹치지 않게 한다
    marks = [(x, 194 if len(n) > 5 else 182, n) for x, n in zip(XS, NAMES)]
    return _level_scene(420, 206, g, XS, levels, reads + marks,
                        caption='단위 : m', cap_at='top')


reg('ls-ch1-19-level', 91, _f19_level())


PLACE.update({
    13: ('ls-ch1-13-grid', None),
    14: ('ls-ch1-14-network', 'ls-ch1-14-network-a'),
    16: (None, 'ls-ch1-16-planting'),
    19: ('ls-ch1-19-level', None),
})


PLACE.update({
    2: (None, 'ls-ch1-2-rootball'),
    3: (None, 'ls-ch1-3-pavement'),
    6: ('ls-ch1-6-biangle', 'ls-ch1-6-stake'),
    7: ('ls-ch1-7-contour', None),
})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--html', help='그림을 모아 볼 HTML 경로')
    ap.add_argument('--page', action='store_true',
                    help='--html 에 원도 쪽 이미지도 나란히 붙인다')
    ap.add_argument('--only', help='문항 번호 몇 개만 (쉼표로 구분)')
    args = ap.parse_args()

    only = None
    if args.only:
        only = {int(x) for x in args.only.replace(' ', '').split(',') if x}

    def pick(key):
        if only is None:
            return True
        m = re.match(r'ls-ch1-(\d+)-', key)
        return bool(m) and int(m.group(1)) in only

    keys = [k for k in FIG if pick(k)]

    if args.html:
        parts = ['<meta charset="utf-8"><style>body{font:14px system-ui;padding:16px;'
                 'background:#fff;max-width:900px}h3{margin:26px 0 4px;color:#1b4332;'
                 'font-size:15px}p{margin:2px 0 8px;color:#444;font-size:12.5px;'
                 'line-height:1.5}svg{border:1px solid #eee}'
                 'img{width:100%;border:1px solid #ddd;margin-top:6px}</style>']
        for k in keys:
            m = re.match(r'ls-ch1-(\d+)-', k)
            q = GisaEssayQuestion.objects.filter(
                certification__name=CERT, source=SOURCE, number=int(m.group(1))).first()
            t = re.sub(r'\[svg\].*?\[/svg\]', '', q.text, flags=re.S).strip() if q else ''
            parts.append(f'<h3>{k} <small style="color:#888;font-weight:400">'
                         f'(PDF {PAGE[k]}쪽 = 교재 {PAGE[k] + 275}쪽)</small></h3>'
                         f'<p>{t[:200]}</p>' + FIG[k])
            if args.page:
                parts.append(f'<div style="color:#888;font-size:12px;margin-top:8px">'
                             f'원도</div><img src="p{PAGE[k]:03d}.png">')
        io.open(args.html, 'w', encoding='utf-8').write('\n'.join(parts))
        print(f'{args.html} — 그림 {len(keys)}개')

    _BLOCK = re.compile(r'\n*\[svg\].*?\[/svg\]\n*', re.S)

    put = skip = 0
    for n in sorted(PLACE):
        if only is not None and n not in only:
            continue
        qkey, akey = PLACE[n]
        if (qkey and qkey not in FIG) or (akey and akey not in FIG):
            skip += 1
            continue
        q = GisaEssayQuestion.objects.filter(certification__name=CERT, source=SOURCE,
                                             number=n).first()
        if not q:
            print(f'  !! {n}번 문항이 없다')
            continue

        # 문제문 — 자리표시(또는 이미 넣어 둔 그림)를 통째로 갈아 끼운다.
        # 늘 통째로 바꾸므로 몇 번을 돌려도 결과가 같다.
        if qkey:
            block = '\n\n[svg]' + FIG[qkey] + '[/svg]'
            if _BLOCK.search(q.text):
                text = _BLOCK.sub(lambda m: block, q.text, count=1).strip()
            else:
                text = q.text.rstrip() + block
        else:
            # 그림이 곧 답인 문항 — 발문 아래에서 걷어낸다
            text = _BLOCK.sub('\n', q.text).strip()

        answer = q.answer_text
        if akey:
            ablock = '[svg]' + FIG[akey] + '[/svg]'
            if not answer.strip():
                answer = ablock
            elif '[svg]' in answer:
                answer = _BLOCK.sub(lambda m: '\n\n' + ablock, answer, count=1).strip()
            else:
                answer = answer.rstrip() + '\n\n' + ablock

        diff = [f for f, v in (('text', text), ('answer_text', answer))
                if getattr(q, f) != v]
        where = ' · '.join(x for x in (f'문제 {qkey}' if qkey else None,
                                       f'답 {akey}' if akey else None) if x)
        print(f'  {"넣음" if args.apply else "넣을 것"}: {n}번 — {where}'
              + (f' ({", ".join(diff)})' if diff else ' (그대로)'))
        if diff:
            put += 1
            if args.apply:
                q.text, q.answer_text = text, answer
                q.save(update_fields=diff)

    print(f'\n{put}건' + (' 반영했다.' if args.apply else ' (미반영 — --apply 로 넣는다)')
          + (f' · 아직 안 그린 문항 {skip}개' if skip else ''))


if __name__ == '__main__':
    main()
