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

# ── 색 ─────────────────────────────────────────────────────────────────────
# 제도형 그림이라 알록달록하게 칠하지 않는다. 재료가 무엇인지 한눈에 갈리는
# 만큼만 쓴다 — 흙빛·잿빛·연녹·파랑 넷이면 거의 다 된다.
C_SOIL = '#ece0cb'        # 흙·원지반·되메우기
C_SOIL_L = '#f5eee0'      # 흙(옅게)
C_CONC = '#dde4ea'        # 콘크리트·구조체
C_STONE = '#e9e2d4'       # 석재·판석
C_GRAVEL = '#dfe6e0'      # 자갈·혼합골재
C_PLANT = '#dcead3'       # 객토·식재지반·성토
C_WATER = '#cfe3f0'       # 물·유공관
C_CUT = '#f4e0d2'         # 절토(깎는 자리)
C_WOOD = '#c9a97a'        # 각재·수간

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
        b.append(f'<path d="{path}" fill="{C_SOIL}" stroke="{INK}" stroke-width="1.5"/>')
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
            'patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="%s"/>'
            '<line x1="0" y1="0" x2="0" y2="6" stroke="#a8a08c" stroke-width="1.2"/>'
            '</pattern>'
            '<pattern id="c3b" width="10" height="10" patternUnits="userSpaceOnUse">'
            '<rect width="10" height="10" fill="%s"/>'
            '<circle cx="2" cy="3" r="1" fill="#8e9aa6"/>'
            '<circle cx="7" cy="7" r="0.9" fill="#8e9aa6"/>'
            '<path d="M4,8 l2.6,0 l-1.3,-2.4 z" fill="#aab4bd"/></pattern>'
            '<pattern id="c3c" width="16" height="16" patternUnits="userSpaceOnUse">'
            '<rect width="16" height="16" fill="%s"/>'
            '<path d="M0,16 L16,0 M0,0 L16,16" stroke="#93a394" stroke-width="1"/>'
            '</pattern>'
            '<pattern id="c3d" width="9" height="9" patternUnits="userSpaceOnUse">'
            '<rect width="9" height="9" fill="%s"/>'
            '<path d="M0,4.5 L4.5,0 L9,4.5 M0,9 L4.5,4.5 L9,9" fill="none" '
            'stroke="#b6a68a" stroke-width="0.9"/></pattern></defs>'
            % (C_STONE, C_CONC, C_GRAVEL, C_SOIL))
    # (두께px, 채움, 치수라벨) — 위에서 아래로
    layers = [(16, 'url(#c3a)', '30'), (16, C_CONC, '30'),
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
            '<rect width="9" height="9" fill="%s"/>'
            '<circle cx="2" cy="3" r="1" fill="#8fa885"/>'
            '<circle cx="6.5" cy="7" r="0.9" fill="#8fa885"/></pattern>'
            '<pattern id="p16b" width="13" height="13" patternUnits="userSpaceOnUse">'
            '<rect width="13" height="13" fill="%s"/>'
            '<circle cx="4" cy="4" r="3" fill="none" stroke="#8b998c" stroke-width="1"/>'
            '<circle cx="10" cy="10" r="2.4" fill="none" stroke="#8b998c" '
            'stroke-width="1"/></pattern>'
            '<pattern id="p16c" width="9" height="9" patternUnits="userSpaceOnUse">'
            '<rect width="9" height="9" fill="%s"/>'
            '<path d="M0,4.5 L4.5,0 L9,4.5 M0,9 L4.5,4.5 L9,9" fill="none" '
            'stroke="#b6a68a" stroke-width="0.9"/></pattern></defs>'
            % (C_PLANT, C_GRAVEL, C_SOIL))
    TOP, SOIL, FELT, GRAV = 128, 66, 4, 34
    y1 = TOP + SOIL                 # 객토 아래 = 여과층
    y2 = y1 + FELT                  # 자갈층 위
    y3 = y2 + GRAV                  # 자갈층 아래(가장자리)
    sag = 15                        # 6% 물매로 가운데가 내려앉는 깊이
    b = [pats]
    b.append(f'<rect x="{x1}" y="{TOP}" width="{x2-x1}" height="{SOIL}" '
             f'fill="url(#p16a)" stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{FELT}" fill="#cfd9d2" '
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
    b.append(f'<circle cx="{cx}" cy="{y3+sag-1}" r="9" fill="{C_WATER}" stroke="{INK}" '
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
            '<rect width="7" height="7" fill="%s"/>'
            '<circle cx="2" cy="2" r="0.9" fill="#bfae91"/>'
            '<circle cx="5.5" cy="5" r="0.7" fill="#bfae91"/></pattern></defs>' % C_SOIL)
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


# ── 20번. 터파기 평면도·단면도 — 문제 제시 ────────────────────────────────
def _f20_pit():
    """바닥 30m × 30m, 깊이 10m, 비탈 1 : 2 라 한쪽이 5m 씩 벌어져
    윗면이 40m × 40m 가 된다. 평면도의 모서리 사선이 그 비탈이다."""
    b = []
    # 평면도 — 바깥 40, 안쪽 30
    ox, oy, OS, IN = 44, 40, 108, 81
    ix, iy = ox + (OS - IN) / 2, oy + (OS - IN) / 2
    b.append(f'<rect x="{ox}" y="{oy}" width="{OS}" height="{OS}" fill="none" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<rect x="{ix}" y="{iy}" width="{IN}" height="{IN}" fill="{C_SOIL_L}" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    for a, z in (((ox, oy), (ix, iy)), ((ox + OS, oy), (ix + IN, iy)),
                 ((ox, oy + OS), (ix, iy + IN)), ((ox + OS, oy + OS), (ix + IN, iy + IN))):
        b.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{z[0]}" y2="{z[1]}" '
                 f'stroke="{INK}" stroke-width="1"/>')
    b.append(dim_v(oy, iy, ox - 14, '5m', G))
    b.append(dim_v(iy, iy + IN, ox - 14, '30m', G))
    b.append(dim_v(iy + IN, oy + OS, ox - 14, '5m', G))
    b.append(f'<text x="{ox + OS / 2}" y="{oy + OS + 22}" text-anchor="middle" '
             f'fill="{INK}" font-size="10">&lt;평 면 도&gt;</text>')
    # 단면도
    sx, sy, TW, BW, D = 216, 66, 130, 98, 74
    tl, tr = sx, sx + TW
    bl, br = sx + (TW - BW) / 2, sx + TW - (TW - BW) / 2
    b.append(HATCH)
    b.append(f'<path d="M{tl} {sy} L{bl} {sy+D} L{br} {sy+D} L{tr} {sy} Z" '
             f'fill="{C_SOIL_L}" stroke="{INK}" stroke-width="1.4"/>')
    b.append(f'<line x1="{tl-16}" y1="{sy}" x2="{tr+16}" y2="{sy}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    b.append(dim_h(tl, bl, sy - 14, '5m', G))
    b.append(dim_h(bl, br, sy - 14, '30m', G))
    b.append(dim_h(br, tr, sy - 14, '5m', G))
    b.append(dim_v(sy, sy + D, tl - 14, '10m', G))
    b.append(f'<text x="{tl+9}" y="{sy+D/2}" fill="{G}" font-size="9" '
             f'transform="rotate(63 {tl+9} {sy+D/2})">1:2</text>')
    b.append(f'<text x="{tr-9}" y="{sy+D/2}" text-anchor="end" fill="{G}" '
             f'font-size="9" transform="rotate(-63 {tr-9} {sy+D/2})">1:2</text>')
    b.append(f'<text x="{sx + TW / 2}" y="{sy + D + 26}" text-anchor="middle" '
             f'fill="{INK}" font-size="10">&lt;단 면 도&gt;</text>')
    return svg(384, 190, ''.join(b))


reg('ls-ch1-20-pit', 92, _f20_pit())


# ── 21번. 사각분할 + 삼각분할 격자 — 문제 제시 ────────────────────────────
def _f21_grid():
    """왼쪽 두 칸(A－B－F－G)은 사각분할, 오른쪽(B－C－D－E－F)은 삼각분할.

    **삼각분할 쪽 대각선은 답의 계수표(1·3·2 / 3·6·2 / 3·3 / 1)에서 역산했다.**
    한 꼭짓점에 모이는 삼각형 수가 곧 계수이고, Σh₁=16.12 · Σh₂=16.48 ·
    Σh₃=33.11 · Σh₆=8.02 와 모두 들어맞는 배치는 이 하나뿐이다.
    경계 D－E－F 는 직선 하나로, 오른쪽 아래를 비스듬히 잘라 낸다.
    """
    CW, CH, X0, Y0 = 58, 44, 62, 62
    ev = [['9.83', '8.96', '7.79', '8.33', '8.02'],
          ['9.13', '8.60', '8.99', '8.02', '8.46'],
          ['8.50', '8.31', '8.46', '7.33'],
          ['8.20', '8.61', '8.33']]
    def px(c): return X0 + c * CW
    def py(r): return Y0 + r * CH
    b = []
    # 사각분할 — 왼쪽 두 칸 × 세 줄, 대각선 없음
    for r in range(3):
        for c in range(2):
            b.append(f'<rect x="{px(c)}" y="{py(r)}" width="{CW}" height="{CH}" '
                     f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
    # 삼각분할 — 온전한 칸 셋에 '/' 대각선
    for r, c in ((0, 2), (0, 3), (1, 2)):
        b.append(f'<rect x="{px(c)}" y="{py(r)}" width="{CW}" height="{CH}" '
                 f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
        b.append(f'<line x1="{px(c+1)}" y1="{py(r)}" x2="{px(c)}" y2="{py(r+1)}" '
                 f'stroke="{INK}" stroke-width="1"/>')
    # 잘린 삼각형 둘 — 경계 D(4,1)→E(3,2)→F(2,3)
    b.append(f'<polygon points="{px(4)},{py(1)} {px(3)},{py(1)} {px(3)},{py(2)}" '
             f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
    b.append(f'<polygon points="{px(3)},{py(2)} {px(2)},{py(2)} {px(2)},{py(3)}" '
             f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
    b.append(f'<line x1="{px(4)}" y1="{py(1)}" x2="{px(2)}" y2="{py(3)}" '
             f'stroke="{INK}" stroke-width="1.5"/>')
    for r, row in enumerate(ev):
        for c, v in enumerate(row):
            b.append(f'<circle cx="{px(c)}" cy="{py(r)}" r="1.8" fill="{INK}"/>')
            b.append(elev(px(c), py(r), v, dx=16 if c < 4 else 18, dy=-6))
    for c in range(4):
        b.append(dim_h(px(c), px(c + 1), Y0 - 30, '30', G))
    for r in range(3):
        b.append(dim_v(py(r), py(r + 1), X0 - 16, '20', G))
    for name, (c, r), dx, dy in (('A', (0, 0), -6, -8), ('B', (2, 0), -6, -8),
                                 ('C', (4, 0), -8, -8), ('D', (4, 1), -8, -6),
                                 ('E', (3, 2), -9, -5), ('F', (2, 3), -8, 12),
                                 ('G', (0, 3), -6, 12)):
        b.append(f'<text x="{px(c)+dx}" y="{py(r)+dy}" text-anchor="end" fill="{INK}" '
                 f'font-size="10.5" font-weight="700">{name}</text>')
    b.append(f'<text x="{px(4)}" y="{py(3)+4}" text-anchor="end" fill="#666" '
             f'font-size="9">(단위 : m)</text>')
    return svg(px(4) + 42, py(3) + 34, ''.join(b))


reg('ls-ch1-21-grid', 93, _f21_grid())


# ── 24번. 기초 평면도·단면도 — 문제 제시 ──────────────────────────────────
def _f24_foundation():
    """터파기는 윗면 2,700 × 2,700 · 아랫면 1,900 × 1,900. 그 속의 구조체는
    밑판 1,500 각 → 절두각뿔(1,500→300) → 기둥 300 각으로 층이 셋이다."""
    b = []
    ox, oy, OS, IN = 46, 44, 104, 26
    ix = iy = None
    ix, iy = ox + (OS - IN) / 2, oy + (OS - IN) / 2
    b.append(f'<rect x="{ox}" y="{oy}" width="{OS}" height="{OS}" fill="none" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<rect x="{ix}" y="{iy}" width="{IN}" height="{IN}" fill="{C_CONC}" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    for a, z in (((ox, oy), (ix, iy)), ((ox + OS, oy), (ix + IN, iy)),
                 ((ox, oy + OS), (ix, iy + IN)), ((ox + OS, oy + OS), (ix + IN, iy + IN))):
        b.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{z[0]}" y2="{z[1]}" '
                 f'stroke="{INK}" stroke-width="1"/>')
    b.append(dim_h(ox, ox + OS, oy - 16, '1,500', G))
    b.append(dim_h(ix, ix + IN, iy - 8, '300', G))
    b.append(dim_v(oy, oy + OS, ox - 14, '1,500', G))
    b.append(f'<text x="{ox + OS / 2}" y="{oy + OS + 24}" text-anchor="middle" '
             f'fill="{INK}" font-size="10">&lt;평 면 도&gt;</text>')
    # 단면도 — 터파기 사다리꼴 속에 층 셋
    sx, GL, TW, BW, D = 214, 42, 132, 93, 84
    tl, tr = sx, sx + TW
    bl, br = sx + (TW - BW) / 2, sx + TW - (TW - BW) / 2
    b.append(f'<path d="M{tl} {GL} L{bl} {GL+D} L{br} {GL+D} L{tr} {GL} Z" '
             f'fill="{C_SOIL_L}" stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<line x1="{tl-14}" y1="{GL}" x2="{tr+14}" y2="{GL}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    b.append(f'<text x="{tl-16}" y="{GL-3}" text-anchor="end" fill="{INK}" '
             f'font-size="9">G.L</text>')
    cx = sx + TW / 2
    # 밑판(1,500 × 400) → 절두각뿔(200) → 기둥(300 × 400)
    pw, cw = 44, 10
    b.append(f'<rect x="{cx-pw}" y="{GL+D-22}" width="{pw*2}" height="22" fill="#eef2ee" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<path d="M{cx-pw} {GL+D-22} L{cx-cw} {GL+D-34} L{cx+cw} {GL+D-34} '
             f'L{cx+pw} {GL+D-22} Z" fill="#eef2ee" stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<rect x="{cx-cw}" y="{GL+D-56}" width="{cw*2}" height="22" fill="#eef2ee" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    b.append(dim_v(GL, GL + D - 56, tl - 14, '400', G))
    b.append(dim_v(GL + D - 56, GL + D - 22, tl - 14, '200', G))
    b.append(dim_v(GL + D - 22, GL + D, tl - 14, '400', G))
    b.append(dim_h(bl, br, GL + D + 18, '1,900', G))
    b.append(dim_h(tl, bl, GL - 14, '400', G))
    b.append(dim_h(br, tr, GL - 14, '400', G))
    b.append(f'<text x="{sx + TW / 2}" y="{GL + D + 44}" text-anchor="middle" '
             f'fill="{INK}" font-size="10">&lt;단 면 도&gt;</text>')
    return svg(384, 200, ''.join(b))


reg('ls-ch1-24-foundation', 94, _f24_foundation())


# ── 27번. 등고선 단면 (각주공식용) — 문제 제시 ────────────────────────────
def _f27_contour():
    """a1(0) 부터 a5(500m²) 까지 5m 간격 다섯 단면. 단면이 홀수 개라
    각주공식을 쓸 수 있다 — 그림이 그 조건을 보여 준다."""
    ox, base, step, half = 60, 196, 34, 118
    vals = ['500m²', '300m²', '100m²', '50m²', '']
    names = ['a5', 'a4', 'a3', 'a2', 'a1']
    widths = [1.0, 0.78, 0.5, 0.3, 0.05]
    b = []
    for i, (v, n, wf) in enumerate(zip(vals, names, widths)):
        y = base - i * step
        hw = half * wf / 2
        b.append(f'<line x1="{ox}" y1="{y}" x2="{ox+half}" y2="{y}" stroke="{INK}" '
                 f'stroke-width="1"/>')
        b.append(f'<text x="{ox-6}" y="{y+3.4}" text-anchor="end" fill="{INK}" '
                 f'font-size="9.5">{n}</text>')
        if v:
            b.append(f'<text x="{ox+half/2}" y="{y-5}" text-anchor="middle" fill="{INK}" '
                     f'font-size="9.5">{v}</text>')
        if i:
            b.append(dim_v(y, y + step, ox + half + 16, 'h', G))
    cx = ox + half / 2
    b.append(f'<path d="M{ox} {base} C{ox+18} {base-14} {ox+42} {base-4*step} '
             f'{cx} {base-4*step} C{ox+half-42} {base-4*step} {ox+half-18} {base-14} '
             f'{ox+half} {base}" fill="none" stroke="{INK}" stroke-width="1.5"/>')
    return svg(300, 226, ''.join(b))


reg('ls-ch1-27-contour', 96, _f27_contour())


# ── 9번. 통로박스 터파기 단면 — 문제 제시 ─────────────────────────────────
def _f9_box():
    """윗면 11m(3+5+3) · 아랫면 5m · 깊이 6m(여유 1m + 박스 5m), 비탈 1 : 0.5.
    깊이 6m 에 1:0.5 면 한쪽이 3m 씩 벌어져 윗면이 11m 가 된다 — 터파기양의
    양단면이 5 와 11 인 까닭이 이 그림에 있다."""
    SC = 13.5                          # 1m 당 px
    cx, top = 176, 52
    bw, tw, d = 5 * SC, 11 * SC, 6 * SC
    bl, br = cx - bw / 2, cx + bw / 2
    tl, tr = cx - tw / 2, cx + tw / 2
    b = [HATCH]
    b.append(f'<path d="M{tl} {top} L{bl} {top+d} L{br} {top+d} L{tr} {top} Z" '
             f'fill="{C_SOIL_L}" stroke="{INK}" stroke-width="1.4"/>')
    b.append(f'<line x1="{tl-20}" y1="{top}" x2="{tr+20}" y2="{top}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    for x in range(int(tl) + 4, int(tr), 9):
        b.append(f'<line x1="{x}" y1="{top}" x2="{x-5}" y2="{top+7}" '
                 f'stroke="#9aa69e" stroke-width="0.7"/>')
    # 통로박스 — 5m 각, 벽 두께를 빗금으로 보인다
    box = 5 * SC
    by = top + d - box
    b.append(f'<rect x="{bl}" y="{by}" width="{box}" height="{box}" '
             f'fill="url(#hx)" stroke="{INK}" stroke-width="1.4"/>')
    b.append(f'<rect x="{bl+9}" y="{by+9}" width="{box-18}" height="{box-18}" '
             f'fill="#fff" stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<text x="{cx}" y="{by+box/2+3.6}" text-anchor="middle" fill="{INK}" '
             f'font-size="9.5">통로박스</text>')
    b.append(dim_h(bl, br, top - 16, '5m', G))
    b.append(dim_v(top, by, tl - 16, '1m', G))
    b.append(dim_v(by, top + d, tl - 16, '5m', G))
    b.append(f'<text x="{tl+16}" y="{top+d/2}" fill="{G}" font-size="9" '
             f'transform="rotate(63 {tl+16} {top+d/2})">1:0.5</text>')
    b.append(f'<text x="{tr-16}" y="{top+d/2}" text-anchor="end" fill="{G}" '
             f'font-size="9" transform="rotate(-63 {tr-16} {top+d/2})">1:0.5</text>')
    return svg(352, top + d + 26, ''.join(b))


reg('ls-ch1-9-box', 84, _f9_box())


# ── 28번. 횡단면 Ⅰ·Ⅱ — 문제 제시 ─────────────────────────────────────────
def _f28_section():
    """두 횡단면의 꼭짓점을 **답의 면적 계산식에서 역산했다.**

    Ⅰ : 46×16 − 14×2 − ½(32×2 + 14×4.67 + 14×9.33 + 24×16) = 386.0m²
    Ⅱ : 44×16 − 18×1.25 − ½(26×1.25 + 18×6.75 + 12×8 + 24×16) = 364.5m²

    빼는 삼각형의 밑변·높이가 곧 꼭짓점 좌표라, 비탈 1:1.5 와도 모두
    들어맞는다(Ⅰ 왼쪽 14m 에 9.33m, 오른쪽 24m 에 16m).
    """
    SC = 3.5                            # 1m 당 px
    def one(ox, name, tops, bots, depth, dleft, dmid):
        """tops (왼쪽 구간, 오른쪽 구간) · bots (왼·가운데·오른) · depth 전체 깊이"""
        w = sum(tops)
        kink = tops[0]                  # 윗면이 꺾이는 자리
        b0 = bots[0]                    # 바닥 왼쪽 끝
        b1 = bots[0] + bots[1]          # 바닥 오른쪽 끝
        X = lambda m: ox + m * SC       # noqa: E731
        Y = lambda m: 66 + m * SC       # noqa: E731
        p = [(X(0), Y(dleft)), (X(kink), Y(dmid)), (X(w), Y(0)),
             (X(b1), Y(depth)), (X(b0), Y(depth))]
        s = ['<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in p)
             + f'" fill="{C_CUT}" stroke="{INK}" stroke-width="1.5"/>']
        s.append(f'<line x1="{X(0)-6}" y1="{Y(0)}" x2="{X(w)+6}" y2="{Y(0)}" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
        # 가운데 깊이 표시 — 기준선에서 윗면 꺾임까지
        s.append(f'<line x1="{X(kink)}" y1="{Y(0)}" x2="{X(kink)}" y2="{Y(dmid)}" '
                 f'stroke="{INK}" stroke-width="0.9"/>')
        s.append(f'<text x="{X(kink)+8}" y="{Y(dmid)+4}" fill="{INK}" '
                 f'font-size="9">{dmid}m</text>')
        # 위·아래 치수줄
        s.append(dim_h(X(0), X(kink), Y(0) - 30, f'{tops[0]}m', G))
        s.append(dim_h(X(kink), X(w), Y(0) - 30, f'{tops[1]}m', G))
        yy = Y(depth) + 24
        s.append(dim_h(X(0), X(b0), yy, f'{bots[0]}m', G))
        s.append(dim_h(X(b0), X(b1), yy, f'{bots[1]}m', G))
        s.append(dim_h(X(b1), X(w), yy, f'{bots[2]}m', G))
        # 비탈 표기
        s.append(f'<text x="{X(b0/2)-4}" y="{Y((dleft+depth)/2)}" fill="{G}" '
                 f'font-size="8.5" transform="rotate(34 {X(b0/2)-4} '
                 f'{Y((dleft+depth)/2)})">1:1.5</text>')
        s.append(f'<text x="{X((b1+w)/2)}" y="{Y(depth/2)}" fill="{G}" '
                 f'font-size="8.5" transform="rotate(-34 {X((b1+w)/2)} '
                 f'{Y(depth/2)})">1:1.5</text>')
        s.append(f'<text x="{X(w/2)}" y="{Y(depth*0.62)}" text-anchor="middle" '
                 f'fill="{INK}" font-size="12" font-weight="700">{name}</text>')
        return ''.join(s)

    b = [one(30, 'Ⅰ', (14, 32), (14, 8, 24), 16, 6.67, 2),
         one(232, 'Ⅱ', (18, 26), (12, 8, 24), 16, 8, 1.25)]
    return svg(400, 66 + 16 * SC + 40, ''.join(b))


reg('ls-ch1-28-section', 96, _f28_section())


# ── 29번. 절·성토 종단 모식도 — 문제 제시 ─────────────────────────────────
def _f29_fill():
    """가운데 언덕을 깎아 좌우 두 웅덩이(A·B)를 메운다. 언덕은 위가 점성토
    6,000m³, 아래가 사질토 7,000m³ 로 두 켜다 — 어느 흙을 어디에 쓰는지가
    문제의 전부라 켜를 갈라 그린다."""
    b = []
    GL = 118                                  # 계획고
    b.append(f'<line x1="20" y1="{GL}" x2="380" y2="{GL}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    b.append(f'<text x="378" y="{GL-6}" text-anchor="end" fill="{INK}" '
             f'font-size="9.5">계획고</text>')
    # A 지역 — 왼쪽 웅덩이(파선)
    b.append(f'<path d="M40 {GL} C60 {GL+44} 110 {GL+44} 130 {GL}" fill="none" '
             f'stroke="{INK}" stroke-width="1.2" stroke-dasharray="5 3"/>')
    b.append(f'<text x="85" y="{GL+26}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">A</text>')
    b.append(f'<text x="85" y="{GL+58}" text-anchor="middle" fill="{INK}" '
             f'font-size="9">사질토 성토 : 3,500m³</text>')
    # 가운데 언덕 — 아래 사질토, 위 점성토
    hill = f'M130 {GL} C150 {GL-36} 168 {GL-74} 200 {GL-74} C232 {GL-74} 250 {GL-36} 270 {GL}'
    b.append(f'<path d="{hill} Z" fill="{C_CUT}" stroke="{INK}" stroke-width="1.4"/>')
    # 켜 경계는 언덕 안에서만 그린다 — 윤곽보다 길게 그으면 밖으로 삐져나온다
    b.append(f'<path d="M162 {GL-46} C182 {GL-56} 218 {GL-56} 238 {GL-46}" fill="none" '
             f'stroke="{INK}" stroke-width="1.1"/>')
    b.append(f'<text x="200" y="{GL-62}" text-anchor="middle" fill="{INK}" '
             f'font-size="9">점성토 : 6,000m³</text>')
    b.append(f'<text x="200" y="{GL-26}" text-anchor="middle" fill="{INK}" '
             f'font-size="9">사질토 : 7,000m³</text>')
    # B 지역 — 오른쪽 웅덩이
    b.append(f'<path d="M270 {GL} C290 {GL+44} 340 {GL+44} 360 {GL}" fill="none" '
             f'stroke="{INK}" stroke-width="1.2" stroke-dasharray="5 3"/>')
    b.append(f'<text x="315" y="{GL+26}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">B</text>')
    b.append(f'<text x="315" y="{GL+58}" text-anchor="middle" fill="{INK}" '
             f'font-size="9">점성토 성토 : 4,000m³</text>')
    return svg(400, GL + 74, ''.join(b))


reg('ls-ch1-29-fill', 97, _f29_fill())


# ── 30번. 공기–공비 곡선 (M.C.X) — 문제 제시 ──────────────────────────────
def _f30_cpm():
    """공기를 줄이면 공비가 오른다. 오른쪽 아래 끝 F 가 표준점(표준공기 C,
    표준비용 B), 왼쪽 위 끝 E 가 특급점(특급공기 D, 특급비용 A)이다.
    두 점을 잇는 기울기가 비용구배이며, 26번 M.C.X 가 쓰는 값이 바로 그것이다."""
    OX, OY, W, H = 78, 214, 216, 168      # 원점과 축 길이
    ex, ey = OX + 74, OY - 124            # 특급점 E
    fx, fy = OX + 152, OY - 72            # 표준점 F
    b = []
    b.append(f'<line x1="{OX}" y1="{OY}" x2="{OX}" y2="{OY-H}" stroke="{INK}" '
             f'stroke-width="1.3" marker-end="url(#arw)"/>')
    b.append(f'<line x1="{OX}" y1="{OY}" x2="{OX+W}" y2="{OY}" stroke="{INK}" '
             f'stroke-width="1.3" marker-end="url(#arw)"/>')
    b.append(HATCH)
    b.append(f'<text x="{OX-4}" y="{OY-H-4}" text-anchor="middle" fill="{INK}" '
             f'font-size="9.5">공비</text>')
    b.append(f'<text x="{OX+W+6}" y="{OY+4}" fill="{INK}" font-size="9.5">공기</text>')
    b.append(f'<path d="M{OX+30} {OY-152} C{OX+56} {OY-128} {ex} {ey} {ex} {ey} '
             f'C{ex+34} {ey+34} {fx-26} {fy+6} {fx} {fy} '
             f'C{fx+24} {fy+5} {fx+44} {fy+11} {OX+W-16} {fy+15}" '
             f'fill="none" stroke="{INK}" stroke-width="1.6"/>')
    for x, y, n in ((ex, ey, 'E'), (fx, fy, 'F')):
        b.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="{INK}"/>'
                 f'<text x="{x+6}" y="{y-6}" fill="{INK}" font-size="10.5" '
                 f'font-weight="700">{n}</text>')
        b.append(f'<line x1="{OX}" y1="{y}" x2="{x}" y2="{y}" stroke="#9aa69e" '
                 f'stroke-width="0.8" stroke-dasharray="4 3"/>')
        b.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{OY}" stroke="#9aa69e" '
                 f'stroke-width="0.8" stroke-dasharray="4 3"/>')
    # 세로 치수 A(특급비용)·B(표준비용)
    b.append(dim_v(ey, OY, OX - 34, 'A', G))
    b.append(dim_v(fy, OY, OX - 16, 'B', G))
    # 가로 치수 D(특급공기)·C(표준공기)
    b.append(dim_h(OX, ex, OY + 20, 'D', G))
    b.append(dim_h(OX, fx, OY + 40, 'C', G))
    return svg(340, OY + 56, ''.join(b))


reg('ls-ch1-30-cpm', 98, _f30_cpm())


# ── 32번. 독립기초 평면도·단면도 — 문제 제시 ──────────────────────────────
def _f32_footing():
    """1,700 각(600+500+600) 기초 10개소. 평면도에 가로근·세로근 D16@200 과
    대각선근 D16-3 을, 단면도에 밑판 300 + 절두각뿔 400 을 그린다.
    경사면 기울기가 0.4/0.6 로 tan30° 를 넘어 거푸집을 계상해야 하는데,
    그 기울기가 곧 이 단면의 모양이다."""
    b = []
    ox, oy, S = 44, 44, 108
    a, mid = S * 600 / 1700, S * 500 / 1700
    b.append(f'<rect x="{ox}" y="{oy}" width="{S}" height="{S}" fill="none" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    ix, iy = ox + a, oy + a
    b.append(f'<rect x="{ix}" y="{iy}" width="{mid}" height="{mid}" fill="{C_CONC}" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    for p, q in (((ox, oy), (ix, iy)), ((ox + S, oy), (ix + mid, iy)),
                 ((ox, oy + S), (ix, iy + mid)), ((ox + S, oy + S), (ix + mid, iy + mid))):
        b.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" '
                 f'stroke="{INK}" stroke-width="1"/>')
    # 배근 — 오른쪽 절반에만 그려 도형을 가리지 않는다(원도와 같다)
    for i in range(1, 9):
        t = ox + S / 2 + (S / 2) * i / 9
        b.append(f'<line x1="{t:.1f}" y1="{oy}" x2="{t:.1f}" y2="{oy+S}" '
                 f'stroke="#9aa69e" stroke-width="0.6"/>')
        t2 = oy + (S) * i / 9
        b.append(f'<line x1="{ox+S/2}" y1="{t2:.1f}" x2="{ox+S}" y2="{t2:.1f}" '
                 f'stroke="#9aa69e" stroke-width="0.6"/>')
    for k in range(3):
        d = 10 + k * 9
        b.append(f'<line x1="{ox+S/2+d}" y1="{oy}" x2="{ox+S}" y2="{oy+S-d}" '
                 f'stroke="{G2}" stroke-width="0.9"/>')
    for t, yy in (('D16-3', oy + 16), ('D16@200', oy + 46), ('D16@200', oy + 80)):
        b.append(f'<line x1="{ox+S}" y1="{yy}" x2="{ox+S+10}" y2="{yy}" stroke="{INK}" '
                 f'stroke-width="0.7"/>'
                 f'<text x="{ox+S+13}" y="{yy+3.4}" fill="{INK}" font-size="9">{t}</text>')
    b.append(dim_h(ox, ox + S, oy - 26, '1,700', G))
    b.append(dim_h(ox, ix, oy - 12, '600', G))
    b.append(dim_h(ix, ix + mid, oy - 12, '500', G))
    b.append(dim_h(ix + mid, ox + S, oy - 12, '600', G))
    b.append(dim_v(oy, oy + S, ox - 14, '1,700', G))
    b.append(f'<text x="{ox+S/2}" y="{oy+S+22}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;평 면 도&gt;</text>')
    # 단면도
    sx, sy, W2 = 246, 60, 108
    aa, mm = W2 * 600 / 1700, W2 * 500 / 1700
    H1, H2 = 26, 34                        # 밑판 300 · 절두각뿔 400
    cl, cr = sx + aa, sx + aa + mm
    b.append(f'<path d="M{sx} {sy+H2} L{cl} {sy} L{cr} {sy} L{sx+W2} {sy+H2} Z" '
             f'fill="{C_CONC}" stroke="{INK}" stroke-width="1.3"/>')
    b.append(f'<rect x="{sx}" y="{sy+H2}" width="{W2}" height="{H1}" fill="{C_CONC}" '
             f'stroke="{INK}" stroke-width="1.3"/>')
    b.append(dim_h(sx, sx + W2, sy - 26, '1,700', G))
    b.append(dim_h(sx, cl, sy - 12, '600', G))
    b.append(dim_h(cl, cr, sy - 12, '500', G))
    b.append(dim_h(cr, sx + W2, sy - 12, '600', G))
    b.append(dim_v(sy, sy + H2, sx + W2 + 14, '400', G))
    b.append(dim_v(sy + H2, sy + H2 + H1, sx + W2 + 14, '300', G))
    b.append(dim_v(sy, sy + H2 + H1, sx + W2 + 36, '700', G))
    b.append(f'<text x="{sx+W2/2}" y="{sy+H2+H1+24}" text-anchor="middle" fill="{INK}" '
             f'font-size="10">&lt;단 면 도&gt;</text>')
    return svg(400, 190, ''.join(b))


reg('ls-ch1-32-footing', 98, _f32_footing())


# ── 33번. 승강식 수준측량도 — 문제 제시 ───────────────────────────────────
def _f33_level():
    """A 와 C 는 **머리 위 구조물**이라 표척을 거꾸로 세워 읽는다(−3.10, −2.56,
    −4.21). 그래서 야장에서 빼면 오히려 더해져 A 가 가장 높다(77.15m).
    그 사실이 그림에 드러나야 문제가 풀린다 — 위쪽 구조물과 거꾸로 선 표척을
    함께 그린다."""
    b = ['<defs><pattern id="p33" width="6" height="6" patternUnits="userSpaceOnUse">'
         '<rect width="6" height="6" fill="%s"/>'
         '<circle cx="1.6" cy="1.6" r="0.8" fill="#bfae91"/>'
         '<circle cx="4.4" cy="4.4" r="0.7" fill="#bfae91"/></pattern></defs>' % C_SOIL]
    # 머리 위 구조물 — 왼쪽이 높고 오른쪽이 한 단 낮다
    b.append(f'<path d="M28 14 L212 14 L246 40 L378 40 L378 0 L28 0 Z" '
             f'fill="url(#p33)" stroke="{INK}" stroke-width="1.3"/>')
    # 땅 — 계단식, 오른쪽으로 내려간다
    b.append(f'<path d="M28 168 L58 168 L58 150 L196 150 L196 166 L238 166 L238 182 '
             f'L286 182 L286 196 L332 196 L332 210 L378 210 L378 226 L28 226 Z" '
             f'fill="url(#p33)" stroke="{INK}" stroke-width="1.3"/>')
    def staff(x, y1, y2):
        return (f'<rect x="{x-3}" y="{min(y1,y2)}" width="6" height="{abs(y2-y1)}" '
                f'fill="#fff" stroke="{INK}" stroke-width="1.1"/>')
    def tripod(x, y, gy):
        return (f'<line x1="{x}" y1="{y}" x2="{x-10}" y2="{gy}" stroke="{INK}" '
                f'stroke-width="1"/><line x1="{x}" y1="{y}" x2="{x+10}" y2="{gy}" '
                f'stroke="{INK}" stroke-width="1"/>'
                f'<line x1="{x}" y1="{y}" x2="{x}" y2="{gy}" stroke="{INK}" '
                f'stroke-width="1"/>'
                f'<rect x="{x-11}" y="{y-6}" width="22" height="9" fill="#fff" '
                f'stroke="{INK}" stroke-width="1.1"/>')
    b.append(staff(60, 150, 88))          # B.M — 땅에서 위로
    b.append(staff(118, 14, 88))          # A — 구조물에서 거꾸로
    b.append(staff(198, 150, 88))         # B
    b.append(staff(252, 40, 112))         # C — 아래 구조물에서 거꾸로
    b.append(staff(340, 196, 112))        # D
    b.append(tripod(156, 92, 150))
    b.append(tripod(298, 116, 182))
    for x, y, t, an in ((66, 84, '1.75', 'start'), (124, 84, '3.10', 'start'),
                        (192, 84, '1.49', 'end'), (246, 108, '2.56', 'end'),
                        (258, 108, '4.21', 'start'), (334, 108, '4.20', 'end')):
        b.append(f'<text x="{x}" y="{y}" text-anchor="{an}" fill="{INK}" '
                 f'font-size="9.5">{t}</text>')
    for x, y, t, an in ((62, 180, 'B.M', 'start'), (118, 26, 'A', 'middle'),
                        (198, 146, 'B', 'middle'), (252, 52, 'C', 'middle'),
                        (340, 208, 'D', 'middle')):
        b.append(f'<text x="{x}" y="{y}" text-anchor="{an}" fill="{INK}" '
                 f'font-size="10" font-weight="700">{t}</text>')
    return svg(400, 236, ''.join(b))


reg('ls-ch1-33-level', 99, _f33_level())


# ── 35번. 소광장 정지계획 — 문제 제시 ─────────────────────────────────────
def _f35_grading():
    """부지 10,000 × 5,000, 위쪽 두 모서리가 45.5m. 아래로 2% 물매를 주므로
    5m 에 0.1m 가 내려가 A·B 는 45.4m 가 된다. 파선이 기존 등고선(40~46)이다."""
    b = []
    L, R, T, B_ = 118, 268, 96, 172
    for i, lv in enumerate(range(46, 39, -1)):
        y = 88 + i * 27
        b.append(f'<path d="M34 {y+10} C90 {y+2} 150 {y-6} 214 {y-8} '
                 f'C268 {y-10} 320 {y-4} 374 {y+2}" fill="none" stroke="{INK}" '
                 f'stroke-width="1" stroke-dasharray="6 4"/>')
        b.append(f'<text x="28" y="{y+13}" text-anchor="end" fill="{INK}" '
                 f'font-size="9.5">{lv}</text>')
    b.append(f'<rect x="{L}" y="{T}" width="{R-L}" height="{B_-T}" fill="{C_PLANT}" '
             f'fill-opacity="0.9" stroke="{INK}" stroke-width="1.6"/>')
    for x in (L + 12, R - 12):
        b.append(f'<rect x="{x-14}" y="{T+3}" width="28" height="13" fill="#fff" '
                 f'stroke="{INK}" stroke-width="0.9"/>'
                 f'<text x="{x}" y="{T+13}" text-anchor="middle" fill="{INK}" '
                 f'font-size="9">45.5</text>')
    cx = (L + R) / 2
    b.append(f'<line x1="{cx}" y1="{T+22}" x2="{cx}" y2="{B_-10}" stroke="{INK}" '
             f'stroke-width="1.2" marker-end="url(#arw)"/>')
    b.append(HATCH)
    b.append(f'<text x="{cx+5}" y="{(T+B_)/2}" fill="{INK}" font-size="9.5">2%</text>')
    b.append(f'<text x="{L+3}" y="{B_+12}" fill="{INK}" font-size="10" '
             f'font-weight="700">A</text>')
    b.append(f'<text x="{R-3}" y="{B_+12}" text-anchor="end" fill="{INK}" '
             f'font-size="10" font-weight="700">B</text>')
    b.append(dim_h(L, R, T - 14, '10,000', G))
    b.append(dim_v(T, B_, R + 20, '5,000', G))
    return svg(400, 286, ''.join(b))


reg('ls-ch1-35-grading', 100, _f35_grading())


# ── 37번. 횡단면적 — 문제 제시 ────────────────────────────────────────────
def _f37_area():
    """꼭짓점을 **답의 계산식에서 역산했다** —
    A = (5.0×3.0 + 6.0×4.0) − ½(2.0×1.0 + 5.0×2.0 + 3.0×4.0 + 6.0×1.0) = 24m².
    빼는 네 삼각형의 밑변·높이가 곧 좌표라 (0,1)·(5,3)·(11,4)·(8,0)·(2,0) 하나로
    풀린다. 바닥 눈금은 중심선에서 잰 거리(5.0·3.0·0.0·3.0·6.0)다."""
    SC, OX, BASE = 24, 60, 178
    X = lambda m: OX + m * SC          # noqa: E731
    Y = lambda m: BASE - m * SC        # noqa: E731
    pts = [(0, 1), (5, 3), (11, 4), (8, 0), (2, 0)]
    b = ['<polygon points="' + ' '.join(f'{X(x)},{Y(y)}' for x, y in pts)
         + f'" fill="{C_CUT}" stroke="{INK}" stroke-width="1.6"/>']
    b.append(f'<line x1="{X(-0.6)}" y1="{BASE}" x2="{X(11.6)}" y2="{BASE}" '
             f'stroke="{INK}" stroke-width="1"/>')
    # 중심선과 좌우 끝의 세로 보조선
    for m, top in ((0, 1), (5, 3), (11, 4)):
        b.append(f'<line x1="{X(m)}" y1="{Y(top)}" x2="{X(m)}" y2="{BASE}" '
                 f'stroke="#9aa69e" stroke-width="0.8" stroke-dasharray="4 3"/>')
    b.append(f'<line x1="{X(5)}" y1="{Y(3)}" x2="{X(5)}" y2="{BASE}" stroke="{INK}" '
             f'stroke-width="1"/>')
    for m, t, an in ((0, '1.0', 'end'), (5, '3.0', 'middle'), (11, '4.0', 'start')):
        top = dict(((0, 1), (5, 3), (11, 4)))[m]
        b.append(f'<text x="{X(m) + (-5 if an == "end" else 5 if an == "start" else 0)}" '
                 f'y="{Y(top) - 6}" text-anchor="{an}" fill="{INK}" '
                 f'font-size="9.5">{t}</text>')
    for m, t in ((0, '5.0'), (2, '3.0'), (5, '0.0'), (8, '3.0'), (11, '6.0')):
        b.append(f'<line x1="{X(m)}" y1="{BASE}" x2="{X(m)}" y2="{BASE+6}" '
                 f'stroke="{INK}" stroke-width="0.9"/>')
        b.append(f'<text x="{X(m)}" y="{BASE+19}" text-anchor="middle" fill="{INK}" '
                 f'font-size="9.5">{t}</text>')
    b.append(f'<text x="{X(11.8)}" y="{BASE+19}" fill="#666" font-size="9">(단위 m)</text>')
    return svg(X(13.6), BASE + 32, ''.join(b))


reg('ls-ch1-37-area', 101, _f37_area())


# ── 38번. 네트워크 공정표 — 답(작성 결과) ─────────────────────────────────
_N38 = {1: (36, 124), 3: (146, 58), 2: (146, 124), 4: (146, 192),
        5: (246, 124), 6: (322, 124), 7: (380, 124)}
_E38 = [(1, 3, 'A/3'), (1, 2, 'B/2'), (1, 4, 'C/4'), (2, 5, 'E/2'),
        (3, 5, '', True), (4, 5, '', True),
        (3, 6, 'F/3'), (5, 6, 'G/3'), (4, 6, 'D/5'), (6, 7, 'H/5')]

reg('ls-ch1-38-network', 102,
    _network(_N38, _E38, 404, 234,
             marks={1: (0, 0), 2: (2, 4), 3: (3, 6), 4: (4, 4),
                    5: (4, 6), 6: (9, 9), 7: (14, 14)},
             cp={(1, 4), (4, 6), (6, 7)},
             mark_pos={2: 'bottom', 4: 'bottom', 5: 'bottom'}))


# ── 40번. 등고선 + 도로 단면 — 문제 제시 ──────────────────────────────────
def _f40_road():
    """왼쪽은 A1~A5 등고선(20m 간격), 오른쪽은 만들려는 도로의 단면.
    윗면 6m · 높이 3m · 비탈 1 : 2 라 한쪽이 6m 씩 벌어져 아랫변이 18m 가
    된다 — 단면적 (18+6)/2 × 3 = 36m² 가 그림에서 바로 읽힌다."""
    b = []
    cx, cy = 104, 128
    rings = [(84, 62), (66, 48), (49, 35), (32, 23), (16, 12)]
    for i, (rx, ry) in enumerate(rings):
        b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" '
                 f'stroke="{INK}" stroke-width="1.1"/>')
        b.append(f'<text x="{cx-rx+7:.0f}" y="{cy+3}" text-anchor="middle" fill="{G}" '
                 f'font-size="8.5">A{i+1}</text>')
    # 도로 단면 — 윗변 6m, 아랫변 18m, 높이 3m
    SC = 7.4
    sx, base = 228, 190
    tw, bw, h = 6 * SC, 18 * SC, 3 * SC * 2.2
    mx = sx + bw / 2
    b.append(f'<path d="M{sx} {base} L{mx-tw/2} {base-h} L{mx+tw/2} {base-h} '
             f'L{sx+bw} {base} Z" fill="{C_PLANT}" stroke="{INK}" stroke-width="1.4"/>')
    b.append(dim_h(mx - tw / 2, mx + tw / 2, base - h - 14, '6m', G))
    b.append(f'<line x1="{mx}" y1="{base-h}" x2="{mx}" y2="{base}" stroke="{INK}" '
             f'stroke-width="0.9" marker-end="url(#arw)"/>')
    b.append(HATCH)
    b.append(f'<text x="{mx+6}" y="{base-h/2}" fill="{INK}" font-size="9.5">3m</text>')
    # 비탈 1 : 2 — 원도처럼 작은 직각삼각형으로 보인다
    for sgn, ox in ((1, sx + 16), (-1, sx + bw - 16)):
        b.append(f'<path d="M{ox} {base-14} l{18*sgn} 0 l0 -14 Z" fill="none" '
                 f'stroke="{INK}" stroke-width="0.9"/>')
        b.append(f'<text x="{ox+9*sgn}" y="{base-4}" text-anchor="middle" fill="{INK}" '
                 f'font-size="8.5">2</text>')
        b.append(f'<text x="{ox+20*sgn}" y="{base-20}" text-anchor="middle" fill="{INK}" '
                 f'font-size="8.5">1</text>')
    return svg(400, 214, ''.join(b))


reg('ls-ch1-40-road', 103, _f40_road())


# ── 41번. 저수지 등고선 — 문제 제시 ───────────────────────────────────────
def _f41_reservoir():
    """오른쪽 곧은 선이 댐이고, 등고선(85~120m)이 거기에 잘려 반쪽 고리가 된다.
    단면이 여덟(짝수)이라 각주공식만으로는 안 되고 양단면평균법을 덧대야 한다."""
    b = []
    dam = 320
    lv = [120, 115, 110, 105, 100, 95, 90, 85]
    for i, v in enumerate(lv):
        rx = 232 - i * 27
        ry = 104 - i * 12
        cy = 128
        b.append(f'<path d="M{dam} {cy-ry} A{rx} {ry} 0 0 0 {dam} {cy+ry}" '
                 f'fill="none" stroke="{INK}" stroke-width="1.1"/>')
        b.append(f'<text x="{dam-rx+6:.0f}" y="{cy-ry*0.42:.0f}" text-anchor="middle" '
                 f'fill="{INK}" font-size="8.5">{v}</text>')
    b.append(f'<line x1="{dam}" y1="14" x2="{dam}" y2="242" stroke="{INK}" '
             f'stroke-width="3"/>')
    b.append(f'<text x="{dam+8}" y="{130}" fill="{INK}" font-size="9.5">댐</text>')
    return svg(360, 256, ''.join(b))


reg('ls-ch1-41-reservoir', 103, _f41_reservoir())


# ── 43번. 단곡선 노선측량도 — 문제 제시 ───────────────────────────────────
def _f43_curve():
    """두 접선 A－P 와 P－B 가 교점 P 에서 만나고, 그 사이를 곡선이 잇는다.
    B.C 와 E.C 에서 접선과 맞닿으므로 **조절점을 P 로 둔 2차 베지에**가 곧
    그 곡선이다(접선에 접하는 포물선). C·D 는 접선 위의 측점으로, 거기서 잰
    30°·70° 로 교각 I = 100° 를 구한다."""
    import math
    A, P, B = (34, 224), (206, 30), (386, 236)
    C = (132, 134)
    D = (284, 118)
    BC = (96, 174)
    EC = (330, 182)
    b = []
    for p, q in ((A, P), (P, B), (C, D)):
        b.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" '
                 f'stroke="{INK}" stroke-width="1.2"/>')
    b.append(f'<path d="M{BC[0]} {BC[1]} Q{P[0]} {P[1]} {EC[0]} {EC[1]}" fill="none" '
             f'stroke="{INK}" stroke-width="2"/>')
    def ang(at, to1, to2, r, label, dx, dy):
        a1 = math.degrees(math.atan2(to1[1] - at[1], to1[0] - at[0]))
        a2 = math.degrees(math.atan2(to2[1] - at[1], to2[0] - at[0]))
        p1 = (at[0] + r * math.cos(math.radians(a1)), at[1] + r * math.sin(math.radians(a1)))
        p2 = (at[0] + r * math.cos(math.radians(a2)), at[1] + r * math.sin(math.radians(a2)))
        return (f'<path d="M{p1[0]:.1f} {p1[1]:.1f} A{r} {r} 0 0 1 {p2[0]:.1f} '
                f'{p2[1]:.1f}" fill="none" stroke="{G}" stroke-width="1"/>'
                f'<text x="{at[0]+dx}" y="{at[1]+dy}" fill="{G}" font-size="9">{label}</text>')
    b.append(ang(C, P, D, 26, '30°', 14, -4))
    b.append(ang(D, C, P, 26, '70°', -26, 6))
    for pt, t, dx, dy, an in ((A, 'A', -6, 10, 'end'), (P, 'P', -8, -4, 'end'),
                              (B, 'B', 8, 6, 'start'), (C, 'C', -9, 3, 'end'),
                              (D, 'D', 8, -4, 'start'), (BC, 'B.C', -2, 18, 'middle'),
                              (EC, 'E.C', 4, 18, 'middle')):
        b.append(f'<circle cx="{pt[0]}" cy="{pt[1]}" r="2.2" fill="{INK}"/>'
                 f'<text x="{pt[0]+dx}" y="{pt[1]+dy}" text-anchor="{an}" fill="{INK}" '
                 f'font-size="10" font-weight="700">{t}</text>')
    # 교각 I — P 에서 두 접선이 이루는 꺾임각
    b.append(ang(P, A, B, 30, 'I', 12, 34))
    # 조건(A－C 471.021m 등)은 문제문의 [box] 에 이미 있다 — 그림에 또 적으면
    # B 라벨과 겹치기만 하고 보태는 것이 없다.
    return svg(400, 252, ''.join(b))


reg('ls-ch1-43-curve', 104, _f43_curve())


PLACE.update({
    38: (None, 'ls-ch1-38-network'),
    40: ('ls-ch1-40-road', None),
    41: ('ls-ch1-41-reservoir', None),
    43: ('ls-ch1-43-curve', None),
})



PLACE.update({
    32: ('ls-ch1-32-footing', None),
    33: ('ls-ch1-33-level', None),
    35: ('ls-ch1-35-grading', None),
    37: ('ls-ch1-37-area', None),
})



PLACE.update({
    9: ('ls-ch1-9-box', None),
    28: ('ls-ch1-28-section', None),
    29: ('ls-ch1-29-fill', None),
    30: ('ls-ch1-30-cpm', None),
})



PLACE.update({
    20: ('ls-ch1-20-pit', None),
    21: ('ls-ch1-21-grid', None),
    24: ('ls-ch1-24-foundation', None),
    27: ('ls-ch1-27-contour', None),
})



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
