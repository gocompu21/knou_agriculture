# -*- coding: utf-8 -*-
"""401 생태공원 — 입체평면도 모델.

좌표는 **`make_grid401_svg.py` 에서 그대로 가져온다**(사진을 편 뒤 구역별로 읽어
검증해 둔 값이다). 428 과 달리 도면을 눈으로 다시 읽지 않는다.
x 는 서(0)에서 동(90), y 는 북(0)에서 남(60) 으로 잰 m.
블렌더 좌표는 X=x, Y=60-y (북쪽이 +Y), Z=표고(절대값 71 안팎).

    blender -b -P make401.py -- --out r01.png [--top|--bird] [--max] [--threads N]
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

# ─────────────────────────────────────────────────────────────────
# 치수 (m) — 도면에서 읽은 값. 고칠 것은 여기만
# ─────────────────────────────────────────────────────────────────
W, D = 90.0, 60.0                      # 부지 가로(동서) · 세로(남북)

# ── 표고 (절대) — 성운 답안 도면의 계획고 ─────────────────────────
Z_NE_PLAZA = 72.2                      # 북동 진입광장
Z_DECK     = 72.0                      # 목재데크광장 · 관찰로
Z_SE_PLAZA = 71.6                      # 남동 진입광장
Z_MOUND    = 72.6                      # 마운딩 꼭대기
# 수면은 도면에 계획고가 없다(401 에는 단면도가 없다). 주변 지반 71 에 맞춰 가정한다
Z_POND     = 70.8                      # 저수지구 수면
Z_MARSH    = 71.0                      # 습지지구 수면
Z_STREAM   = 70.9                      # 실개천 수면
Z_BASIN    = 70.3                      # 못 바닥

# ── 등고선 (표고, 점) — SVG 생성기의 곡선을 그대로 옮긴 것 ────────
CONTOURS = [
    (73.0, [(-4, 50), (-2.3, 52), (-0.5, 54.5), (1.2, 57), (3, 59.5), (5, 62)]),
    (72.0, [(-2.2, -4.8), (-1.5, -2), (0, 1), (1.2, 4), (1.8, 8), (2, 12), (1.7, 16), (1, 19.5), (-0.3, 23), (-1.2, 27),
            (-1.5, 31), (-1.3, 35), (-0.6, 38.5), (0.3, 40), (2, 43), (4, 46), (6.5, 48.8), (9, 50.5), (11, 51.8),
            (13.5, 53.5), (15.5, 55.5), (17, 58), (18.5, 60.5), (19.8, 62)]),
    (71.0, [(8.6, -5), (8.2, -2), (8.6, 0.5), (9.5, 3.5), (10.2, 7), (10.8, 11), (10.8, 15), (10.6, 19), (10.8, 23),
            (11.3, 27), (12.5, 31), (14, 35), (16, 39), (18.5, 42.5), (21.5, 45), (25, 47.5), (29, 50), (32, 53.5),
            (34.5, 57.5), (36.5, 61.5)]),
    (71.0, [(47.5, -5), (46.8, -1.5), (46.7, 2), (48, 5), (49.8, 7.2), (52, 8.8), (54.3, 10.5), (56, 13), (57.5, 16),
            (59, 19), (61, 22), (61.8, 25.5), (61.5, 29), (61, 33), (60.5, 37), (60.2, 41), (60.2, 45), (60, 50),
            (59.6, 55), (59.9, 59), (61, 62)]),
    (72.0, [(68, -5), (67.5, -2.5), (68.5, 0), (71, 2.5), (74, 5), (76.5, 8), (78.5, 11.5), (80.5, 15), (82.5, 18.5),
            (84.5, 22), (85.8, 26), (86.2, 30), (86.5, 33.5), (87.5, 36), (89.5, 37.8), (91.5, 39.5), (93, 41.5)]),
]
# 등고선만으로는 가운데 분지가 얼마나 패였는지 알 수 없다 — 못 바닥을 점으로 박아 준다
SPOTS = [(26, 9, 70.5), (20, 14, 70.6), (32, 15, 70.6), (44, 27, 70.8), (30, 30, 70.9),
         (86, 10, Z_NE_PLAZA), (73, 56, Z_SE_PLAZA),
         # 마운딩 — 꼭대기 하나로는 IDW 가 퍼져 버린다. 능선 셋을 세우고 **바깥에 72.0 을 둘러** 판다
         (79.5, 33, Z_MOUND), (79.5, 37, Z_MOUND), (79.5, 41, Z_MOUND),
         (74.5, 30, 72.0), (74.5, 37, 72.0), (74.5, 45, 72.0), (84.5, 30, 72.0), (84.5, 37, 72.0),
         (84.5, 45, 72.0), (79.5, 24, 72.0), (79.5, 51, 72.0)]

# ── 물가 (닫힌 도형) ──────────────────────────────────────────────
POND = [(14.7, 1.6), (16, 1), (19, 0.8), (22, 1), (25, 2.2), (27.5, 3.4), (30, 3.6), (32, 2.6), (34, 2.2), (36, 2.6),
        (38, 3.6), (39.4, 5.5), (40, 7.5), (39.8, 9), (38, 14), (37.6, 15.5), (36.5, 17), (35.3, 18.3), (34.8, 19.3),
        (35, 19.6), (33, 20.2), (32.6, 19.5), (31.9, 19.3), (31.3, 19.8), (30.8, 20.2), (23.2, 20.2), (21.5, 19.9),
        (19.5, 19), (17.5, 17.2), (15.5, 14.5), (14, 11), (13.2, 8), (12.9, 5.5), (13.2, 3.2), (14, 2)]
MARSH = [(34.9, 21.4), (35.2, 23), (34.9, 25.5), (35.3, 27.2), (36.8, 28.3), (38.5, 28.2), (40, 27.6), (41.5, 27.2),
         (42.6, 27.8), (43.2, 29.5), (42.8, 31.5), (43.5, 32.8), (45, 33.2), (47, 33), (49.5, 31.8), (51.5, 29.5),
         (52.4, 27), (52, 25), (51, 23.8), (49.5, 22.9), (47.5, 22.6), (46.5, 21.5), (45, 21.2), (43.5, 21.8),
         (42.3, 22.6), (41, 23.5), (39.5, 23.6), (38, 22.8), (36.6, 20.9)]
# 실개천 — 부지 북쪽 경계를 스치며 지나간다(도면에서는 대부분 부지 밖)
STREAM = [(5, -1.7), (7, -0.6), (9, 0.8), (11, 2), (12.5, 2.5), (13.5, 2.2), (14.7, 1.6), (15.8, 0.6), (18.7, -1.7),
          (22, -2.8), (26.7, -3.2), (32, -3.2), (36, -3.2), (38.7, -3), (42.7, -1.7), (46.7, -1), (50.7, -1.3),
          (55.3, -3), (59.3, -3.9), (65.3, -4.1), (72, -3.9), (78.7, -3.9), (84, -5), (88, -6.3)]
STREAM_W = 2.2

# ── 포장 구역 (x0, x1, y0, y1) ────────────────────────────────────
NE_PLAZA = (82.0, 90.0, 6.0, 13.0)     # 북동 진입광장 (동쪽 ENT)
EAST_WALK = (72.0, 90.0, 13.0, 18.0)   # 진입 통로
MEET     = (64.0, 72.0, 13.0, 25.0)    # 모임광장
SPINE    = (67.0, 72.0, 25.0, 52.0)    # 남북 보행로 (소형고압블럭)
SE_PLAZA = (67.0, 79.0, 52.0, 60.0)    # 남동 진입광장 (남쪽 ENT)
REST     = (50.0, 58.0, 40.0, 48.0)    # 휴게공간 8 x 8 (지형 평탄화용 사각 범위)
# 도면의 휴게공간은 **북서 모서리가 45° 로 잘린 오각형**이고, 그 잘린 변에서
# 관찰로로 2m 폭 사선 진입로가 나간다(P39 · P40 과 두 사선)
REST_POLY = [(51.4, 40.0), (58.0, 40.0), (58.0, 48.0), (50.0, 48.0), (50.0, 41.5)]
LINK = [(50.4, 38.8), (48.7, 39.9), (50.0, 41.5), (51.4, 40.0)]   # 관찰로 변 → 휴게공간 변
# 포장면 계획고 — 지형을 여기에 맞춰 평탄하게 깎는다(안 깎으면 지형이 포장을 덮는다)
# 진입광장과 동측 통로를 **같은 72.2 로** 둔다. 다르게 두면 경계에 30cm 단차가 생겨
# 포장이 두 조각으로 갈라져 보이고, 경계에 걸친 수목보호대가 반쯤 묻힌다
FLATS = [(NE_PLAZA, Z_NE_PLAZA), (EAST_WALK, Z_NE_PLAZA), (MEET, 72.00),
         (SPINE, 71.80), (SE_PLAZA, Z_SE_PLAZA), (REST, 71.65)]

# ── 관찰로 (목재데크) — 바깥선 · 안선 ─────────────────────────────
# 본선에서 **조류관찰소 접근로(지그재그)를 뺐다** — 안선과 길이 비례로 짝지을 때 띠가
# 접혀 뒤집힌 면이 생겨 검게 나온다. 접근로는 SPUR 로 따로 깐다
RO_OUT = [(64, 13), (48.6, 6.5), (44.6, 11.6), (42, 16.2), (35, 19.6), (33, 20.2),
          (23.2, 20.2), (19.2, 30.1), (26.2, 41.7), (40, 39.7), (46, 41.6), (48.7, 39.9), (50.4, 38.8), (53.5, 36.8),
          (54.8, 30.5), (64, 25)]
SPUR = [(45.6, 11.9), (42.6, 11.6)]      # 관찰로 → 조류관찰소
# **관찰소 벽에 닿기 전에 끊는다** — x=42 까지 밀면 동쪽 벽 상자와 면이 겹쳐 새까맣다
RO_IN  = [(64, 23.2), (53.6, 29.4), (52.2, 35.6), (45.8, 39.9), (40, 37.9), (27.3, 39.8), (21.2, 29.8), (24.2, 22.2),
          (33, 22.2), (43.5, 17.5), (49, 9.4), (64, 15.3)]

# ── 시설물 (도면 시설물 수량표) ───────────────────────────────────
BIRD_HIDE = (38.0, 42.0, 9.0, 14.0)    # 조류관찰소 5.0 x 4.0
PERGOLA   = (53.0, 57.0, 43.0, 47.0)   # 파고라 4.0 x 4.0
DECKS = [(27.6, 19.2, 3.1, 2.0, 0.0), (54.4, 12.7, 3.0, 2.0, 23.0), (23.6, 26.2, 3.0, 2.0, -68.5),
         (22.2, 36.6, 3.0, 2.0, 59.0), (43.3, 38.0, 3.0, 2.0, 19.0)]     # 관찰데크 5 (cx, cy, w, h, 각도)
GRATES = [(85.0, 8.0), (85.0, 13.2), (70.0, 54.8), (75.0, 54.8), (67.0, 18.0)]   # 수목보호대 2 x 2, 5개
BENCHES = [(50.75, 43.05, 90.0), (50.75, 45.45, 90.0), (55.0, 41.2, 0.0), (55.0, 47.0, 0.0),
           (68.5, 22.0, 90.0), (68.5, 28.0, 90.0), (70.5, 54.0, 0.0), (76.5, 54.0, 0.0)]   # 평의자 1.8 x 0.4, 8개
BINS = [(52.0, 46.5), (69.5, 20.0)]                                     # 휴지통 Ø0.6
SIGNS = [(64.2, 15.6), (64.2, 17.9), (64.2, 20.2), (82.4, 10.3), (67.6, 54.5), (69.5, 44.0)]   # 안내판 0.6 x 1.9
BIG_SIGN = (73.0, 57.5)                                                 # 종합안내판

# ── 마운딩 (닫힌 도형, 72.0 → 72.6) ──────────────────────────────
MOUND_OUT = [(78, 27.5), (80.5, 27.2), (82, 28.5), (82.5, 31), (82.3, 35), (82.5, 39), (82.2, 43), (81, 46.5),
             (79.5, 48.5), (77.5, 48), (76.5, 45), (76.6, 41), (76.8, 37), (76.6, 33), (76.8, 30), (77.3, 28.2)]
MOUND_IN  = [(78, 29.5), (79.8, 28.8), (81, 30.5), (81.2, 34), (81.3, 38), (81, 42), (80, 44.6), (78.6, 44.5),
             (77.9, 42), (78, 38), (78.2, 34), (77.8, 31.5)]

# ── 기존수림 (서쪽) · 산림지구 ────────────────────────────────────
WOOD_EDGE = [(9.6, 2.6), (11.4, 4.8), (12.4, 8), (12.2, 11), (11.6, 14), (12.2, 17.5), (12.8, 21), (12.4, 24.5),
             (11.2, 27.5), (11.2, 30.8), (12.8, 32.4), (14.8, 34.8), (15.4, 38), (17, 41.6), (20, 41.9), (22, 41.4),
             (24, 42.8), (25.3, 45.4), (26.7, 48.7), (28.3, 52), (29.3, 55.4), (30.7, 58.7), (30.7, 62)]

# 수목수량표의 관목·초본. (이름, 지름 m, 높이비, 잎색, 꽃색, 꽃비율)
SPECIES = {
    '회양목':   (0.32, 1.90, (0.06, 0.17, 0.06), None,               0.0),
    '무궁화':   (0.42, 1.60, (0.13, 0.28, 0.10), (0.78, 0.62, 0.76), 0.35),
    '병꽃나무': (0.58, 1.10, (0.15, 0.30, 0.11), (0.74, 0.30, 0.38), 0.40),
    '개나리':   (0.50, 1.15, (0.17, 0.33, 0.11), (0.88, 0.76, 0.16), 0.45),
    '유채꽃':   (0.34, 0.85, (0.24, 0.38, 0.12), (0.90, 0.80, 0.12), 0.60),
    '민들레':   (0.26, 0.45, (0.22, 0.36, 0.11), (0.92, 0.82, 0.18), 0.35),
    '쑥부쟁이': (0.30, 0.70, (0.20, 0.34, 0.12), (0.72, 0.68, 0.85), 0.45),
    '부처꽃':   (0.30, 0.95, (0.18, 0.32, 0.11), (0.68, 0.33, 0.58), 0.50),
    '꽃창포':   (0.28, 1.15, (0.19, 0.36, 0.13), (0.52, 0.42, 0.74), 0.40),
    # ── 배식설계도 수목수량표 (401) ──────────────────────────────
    '진달래':   (0.50, 1.20, (0.16, 0.30, 0.12), (0.86, 0.55, 0.70), 0.55),   # H0.6 x W0.5
    '철쭉':     (0.60, 0.85, (0.14, 0.28, 0.11), (0.82, 0.42, 0.62), 0.60),   # H0.5 x W0.6
    '갯버들':   (0.40, 3.00, (0.30, 0.38, 0.22), None,               0.0),    # H1.2 x W0.4
    '생강나무': (0.90, 2.20, (0.20, 0.34, 0.12), (0.88, 0.80, 0.24), 0.30),   # H2.0 x R4
    '부들':     (0.30, 6.00, (0.22, 0.32, 0.12), (0.38, 0.24, 0.12), 0.70),   # 수생 4치포트
    '골풀':     (0.25, 4.00, (0.26, 0.38, 0.15), None,               0.0),    # 수생
    '갈대':     (0.30, 5.00, (0.34, 0.40, 0.18), (0.72, 0.68, 0.52), 0.35),   # 수생
}

# 교목 — 수량표 규격에서 뽑은 (꼴, 크기배율, 잎색)
TREE_SPEC = {
    '소나무':       ('ball', 1.35, (0.08, 0.20, 0.12)),   # H4.0 x W2.0 x R15 상록
    '느티나무':     ('ball', 1.55, (0.16, 0.32, 0.11)),   # H4.0 x R15
    '은행나무':     ('cone', 1.25, (0.33, 0.42, 0.11)),   # H4.0 x B10
    '갈참나무':     ('ball', 1.45, (0.14, 0.29, 0.10)),   # H3.5 x R15
    '졸참나무':     ('ball', 1.40, (0.15, 0.30, 0.10)),   # H3.5 x R15
    '상수리나무':   ('ball', 1.35, (0.13, 0.27, 0.09)),   # H3.5 x R10
    '층층나무':     ('ball', 1.15, (0.18, 0.33, 0.12)),   # H3.0 x R6
    '산벚나무':     ('ball', 1.15, (0.21, 0.34, 0.14)),   # H3.0 x B6
    '버드나무':     ('weep', 1.45, (0.22, 0.36, 0.13)),   # H4.0 x B10
    '메타세쿼이아': ('cone', 1.30, (0.16, 0.30, 0.11)),   # H4.0 x B8
    '산딸나무':     ('ball', 1.10, (0.17, 0.31, 0.12)),   # H3.0 x R8
}


def plant(x, y, name, k=1.0):
    kind, sc, rgb = TREE_SPEC[name]
    tree(x, y, kind, scale=sc * k, leaf_rgb=rgb, name=name)

random.seed(401)
TOP_VIEW = False
BIRD = False
CAM_TILT = 45.0                        # 평면을 뒤로 눕히는 각(깊이 0.71)
RES = (1920, 1280)

# ─────────────────────────────────────────────────────────────────
def bl(x, y):
    """도면 좌표(x 서→동, y 북→남) → 블렌더 좌표."""
    return x, D - y


def mat(name, rgb, rough=0.85, alpha=1.0, spread=0.0, scale=40.0, bump=0.0):
    """재질 한 장. spread 를 주면 **노이즈로 색을 흔들고 요철을 준다** —
    평면색 그대로 두면 아무리 형태가 맞아도 만화처럼 보인다."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1.0)
    b.inputs['Roughness'].default_value = rough
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    if spread > 0.0 or bump > 0.0:
        tex = nt.nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 8.0
        tex.inputs['Roughness'].default_value = 0.6
        tex.location = (-700, 0)
        if spread > 0.0:
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.location = (-480, 120)
            lo = tuple(max(0.0, c * (1.0 - spread)) for c in rgb)
            hi = tuple(min(1.0, c * (1.0 + spread)) for c in rgb)
            ramp.color_ramp.elements[0].color = (*lo, 1.0)
            ramp.color_ramp.elements[1].color = (*hi, 1.0)
            ramp.color_ramp.elements[0].position = 0.30
            ramp.color_ramp.elements[1].position = 0.70
            nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
            nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        if bump > 0.0:
            bp = nt.nodes.new('ShaderNodeBump')
            bp.inputs['Strength'].default_value = bump
            bp.location = (-480, -220)
            nt.links.new(tex.outputs['Fac'], bp.inputs['Height'])
            nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def brick_mat(name, c1, c2, mortar, scale=9.0, msize=0.028, rough=0.8):
    """소형고압블럭·블록 포장 — **줄눈이 보여야 포장으로 읽힌다.**
    단색으로 밝게만 두면 빈 흰 땅처럼 보인다(실제로 그렇게 보였다)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexBrick')
    t.location = (-600, 0)
    t.offset = 0.5
    t.squash = 1.0
    t.inputs['Color1'].default_value = (*c1, 1)
    t.inputs['Color2'].default_value = (*c2, 1)
    t.inputs['Mortar'].default_value = (*mortar, 1)
    t.inputs['Scale'].default_value = scale
    t.inputs['Mortar Size'].default_value = msize
    t.inputs['Brick Width'].default_value = 0.5
    t.inputs['Row Height'].default_value = 0.25
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.35
    nt.links.new(t.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def put(obj, m):
    obj.data.materials.append(m)
    return obj


def slab(x0, x1, y0, y1, z, m, h=0.04):
    """바닥 판 하나(포장·잔디·물)."""
    bx0, by0 = bl(x0, y1)
    bx1, by1 = bl(x1, y0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=((bx0 + bx1) / 2, (by0 + by1) / 2, z - h / 2))
    o = bpy.context.object
    o.scale = (abs(bx1 - bx0), abs(by1 - by0), h)
    return put(o, m)


def box(cx, cy, z, sx, sy, sz, m, rot=0.0):
    bx, by = bl(cx, cy)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, z + sz / 2))
    o = bpy.context.object
    o.scale = (sx, sy, sz)
    o.rotation_euler[2] = rot
    return put(o, m)


def cyl(cx, cy, z, d, h, m, verts=32):
    bx, by = bl(cx, cy)
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=d / 2, depth=h,
                                        location=(bx, by, z + h / 2))
    return put(bpy.context.object, m)


def ring(cx, cy, z, d_in, d_out, m, h=0.04):
    """원형 동선 — 고리."""
    bx, by = bl(cx, cy)
    me = bpy.data.meshes.new('ring')
    bmv = bmesh.new()
    n = 64
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p = [(math.cos(a) * r, math.sin(a) * r) for a, r in
             ((a0, d_in / 2), (a1, d_in / 2), (a1, d_out / 2), (a0, d_out / 2))]
        bmv.faces.new([bmv.verts.new((px, py, 0.0)) for px, py in p])
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('ring', me)
    bpy.context.collection.objects.link(o)
    o.location = (bx, by, z)
    return put(o, m)


def blob_band(x0, x1, y0, y1, r, gap, m, zfun=None, jitter=0.35, squash=0.65,
              avoid=()):
    """관목·초화 덩어리 — 작은 구를 한 메시로 뿌린다(수백 주는 개체로 못 만든다).

    `avoid` 에 (x0, x1, y0, y1) 를 주면 그 자리에는 심지 않는다 — **동선이 지나는
    자리에 관목이 서 있으면 길이 끊긴 것처럼 보인다**(사용자 지적)."""
    me = bpy.data.meshes.new('blob')
    bmv = bmesh.new()
    nx = max(1, int((x1 - x0) / gap))
    ny = max(1, int((y1 - y0) / gap))
    for ix in range(nx + 1):
        for iy in range(ny + 1):
            x = x0 + (x1 - x0) * ix / max(nx, 1) + random.uniform(-jitter, jitter) * gap
            y = y0 + (y1 - y0) * iy / max(ny, 1) + random.uniform(-jitter, jitter) * gap
            x = min(max(x, x0), x1)
            y = min(max(y, y0), y1)
            if any(ax0 <= x <= ax1 and ay0 <= y <= ay1 for ax0, ax1, ay0, ay1 in avoid):
                continue
            bx, by = bl(x, y)
            z = zfun(x, y) if zfun else 0.0
            rr = r * random.uniform(0.8, 1.2)
            sub = bmesh.new()
            bmesh.ops.create_icosphere(sub, subdivisions=1, radius=rr)
            bmesh.ops.scale(sub, vec=Vector((1, 1, squash)), verts=sub.verts)
            bmesh.ops.translate(sub, vec=Vector((bx, by, z + rr * squash * 0.8)), verts=sub.verts)
            tmp = bpy.data.meshes.new('t')
            sub.to_mesh(tmp)
            sub.free()
            bmv.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('blob', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def bed_kerb(x0, x1, y0, y1, m, w=0.10, h=0.06):
    """화단 경계선 — **형태만, 가는 두 줄로 경계가 보이면 된다**(사용자 지시).
    두툼하게 세우면 검은 띠가 되어 관목보다 경계석이 더 도드라진다."""
    slab(x0, x1, y0, y0 + w, Z_GROUND + h, m, h=h)
    slab(x0, x1, y1 - w, y1, Z_GROUND + h, m, h=h)
    slab(x0, x0 + w, y0, y1, Z_GROUND + h, m, h=h)
    slab(x1 - w, x1, y0, y1, Z_GROUND + h, m, h=h)


def scatter_species(points, names, z_of):
    """자리 목록에 **여러 수종을 섞어** 심는다. 한 가지로만 채우면 도면의
    '무궁화 290 · 병꽃나무 260 · 개나리 320 …' 이 한 덩어리로 뭉개진다."""
    groups = {n: [] for n in names}
    for pt in points:
        groups[random.choice(names)].append(pt)
    for name, pts_ in groups.items():
        if not pts_:
            continue
        dia, hs, leaf, flower, fr = SPECIES[name]
        m_leaf = mat('sp_' + name, leaf, spread=0.24, scale=110, bump=0.9)
        me = bpy.data.meshes.new(name)
        bmv = bmesh.new()
        fme = bmesh.new() if flower else None
        for px, py in pts_:
            bx, by = bl(px + random.uniform(-0.18, 0.18), py + random.uniform(-0.18, 0.18))
            z0 = z_of(px, py)
            rr = dia / 2 * random.uniform(0.85, 1.2)
            hh = rr * 2 * hs
            sub = bmesh.new()
            bmesh.ops.create_icosphere(sub, subdivisions=1, radius=rr)
            bmesh.ops.scale(sub, vec=Vector((1, 1, hh / (2 * rr))), verts=sub.verts)
            bmesh.ops.translate(sub, vec=Vector((bx, by, z0 + hh / 2)), verts=sub.verts)
            tmp = bpy.data.meshes.new('t'); sub.to_mesh(tmp); sub.free()
            bmv.from_mesh(tmp); bpy.data.meshes.remove(tmp)
            if flower and random.random() < fr:
                for _ in range(random.randint(2, 5)):
                    f = bmesh.new()
                    bmesh.ops.create_icosphere(f, subdivisions=1, radius=rr * 0.26)
                    bmesh.ops.translate(f, vec=Vector((
                        bx + random.uniform(-rr * 0.6, rr * 0.6),
                        by + random.uniform(-rr * 0.6, rr * 0.6),
                        z0 + hh * random.uniform(0.75, 1.0))), verts=f.verts)
                    t2 = bpy.data.meshes.new('t'); f.to_mesh(t2); f.free()
                    fme.from_mesh(t2); bpy.data.meshes.remove(t2)
        bmv.to_mesh(me); bmv.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(o); put(o, m_leaf)
        if flower and len(fme.verts):
            me2 = bpy.data.meshes.new(name + '_f')
            fme.to_mesh(me2)
            o2 = bpy.data.objects.new(name + '_f', me2)
            bpy.context.collection.objects.link(o2)
            put(o2, mat('fl_' + name, flower, rough=0.7, spread=0.18, scale=200))
        if fme:
            fme.free()


def round_poly(pts, r, seg=7):
    """꼭짓점 목록에 **둥근 모서리**를 넣어 윤곽 점열을 만든다.
    도면의 화단은 직각이 아니라 곡선으로 꺾이고, 끝이 둥글다."""
    n = len(pts)
    out = []
    for i in range(n):
        x0, y0 = pts[(i - 1) % n]
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        v1 = (x0 - x1, y0 - y1)
        v2 = (x2 - x1, y2 - y1)
        l1 = math.hypot(*v1) or 1.0
        l2 = math.hypot(*v2) or 1.0
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        rr = min(r, l1 / 2, l2 / 2)
        a1 = (x1 + u1[0] * rr, y1 + u1[1] * rr)
        a2 = (x1 + u2[0] * rr, y1 + u2[1] * rr)
        if rr < 1e-6:
            out.append((x1, y1))
            continue
        for k in range(seg + 1):                      # 두 점 사이를 꼭짓점 쪽으로 당겨 호를 만든다
            t = k / seg
            mx = (1 - t) ** 2 * a1[0] + 2 * (1 - t) * t * x1 + t ** 2 * a2[0]
            my = (1 - t) ** 2 * a1[1] + 2 * (1 - t) * t * y1 + t ** 2 * a2[1]
            out.append((mx, my))
    return out


def _inside(pt, poly):
    x, y = pt
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            c = not c
        j = i
    return c


def bed_shape(pts, r_corner, m_soil, m_kerb_, species, z=None, gap=0.62,
              kerb_r=0.07, shrub_inset=0.30):
    """도면 윤곽 그대로의 화단 — 둥근 모서리 + **끊김 없는 경계선** + 안쪽 관목.

    사각형 넷을 따로 그리면 모서리에서 선이 겹치고 끊긴다(사용자 지적). 윤곽을
    한 줄의 닫힌 곡선으로 두르면 그런 일이 없다."""
    z = Z_GROUND + 0.012 if z is None else z
    poly = round_poly(pts, r_corner)
    # 바닥
    me = bpy.data.meshes.new('bed')
    bmv = bmesh.new()
    vs = [bmv.verts.new((*bl(x, y), z)) for x, y in poly]
    bmv.faces.new(vs)
    bmv.to_mesh(me); bmv.free()
    o = bpy.data.objects.new('bed', me)
    bpy.context.collection.objects.link(o)
    put(o, m_soil)
    # 경계선 — 닫힌 커브에 굵기를 줘 한 줄로 두른다
    cu = bpy.data.curves.new('kerb', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = kerb_r
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(poly) - 1)
    for i, (x, y) in enumerate(poly):
        bx, by = bl(x, y)
        sp.points[i].co = (bx, by, z + kerb_r * 0.4, 1.0)
    sp.use_cyclic_u = True
    ko = bpy.data.objects.new('kerb', cu)
    bpy.context.collection.objects.link(ko)
    put(ko, m_kerb_)
    # 관목 — 윤곽 안쪽에만
    xs = [x for x, _ in poly]; ys = [y for _, y in poly]
    inner = [((x - sum(xs) / len(xs)) * 0.0 + x, y) for x, y in poly]   # 판정용
    keep = []
    wx, wy = max(xs) - min(xs), max(ys) - min(ys)
    # **좁은 띠에서는 칸을 잘게 쪼갠다.** 격자를 폭보다 성기게 잡으면 양 가장자리만
    # 찍히고 안쪽 판정에서 전부 걸러져 화단이 텅 빈다(실제로 공원 둘레가 그랬다)
    nx = max(2, int(wx / min(gap, max(wx / 3.0, 0.2))))
    ny = max(2, int(wy / min(gap, max(wy / 3.0, 0.2))))
    for ix in range(nx):
        for iy in range(ny):
            px = min(xs) + wx * (ix + 0.5) / nx      # 칸 가운데에 심는다
            py = min(ys) + wy * (iy + 0.5) / ny
            if _inside((px, py), inner) and all(
                    _inside((px + dx, py + dy), inner)
                    for dx, dy in ((shrub_inset, 0), (-shrub_inset, 0),
                                   (0, shrub_inset), (0, -shrub_inset))):
                keep.append((px, py))
    if keep:
        scatter_species(keep, species, lambda _x, _y=None: z)


def planting_bed(x0, x1, y0, y1, m_soil, m_kerb_, m_shrub_, r=0.30, gap=0.55,
                 avoid=(), inset=0.14):
    """화단 한 벌 — 바닥 + **경계석** + 안쪽에 앉힌 관목.

    관목만 뿌려 놓으면 땅에 흘러내린 것처럼 보이고, 도면의 화단 윤곽선이 사라진다.
    경계석을 두르고 관목은 그 **안쪽으로 들여** 심는다."""
    slab(x0, x1, y0, y1, Z_GROUND + 0.012, m_soil)
    bed_kerb(x0, x1, y0, y1, m_kerb_)
    blob_band(x0 + inset, x1 - inset, y0 + inset, y1 - inset, r, gap, m_shrub_,
              squash=0.5, avoid=avoid)


def stalk_band(x0, x1, y0, y1, m, zfun, gap=0.5, per=7, h=(1.3, 1.9),
               rad=0.035, splay=0.22, tip=0.0):
    """갈대·갯버들처럼 **줄기로 선 식생**. 둥근 덩이로 그리면 관목처럼 보인다 —
    갈대는 가늘고 높게 선 줄기 다발, 갯버들은 낮고 굵은 가지 다발이다."""
    me = bpy.data.meshes.new('stalks')
    bmv = bmesh.new()
    nx = max(1, int((x1 - x0) / gap))
    ny = max(1, int((y1 - y0) / gap))
    for ix in range(nx + 1):
        for iy in range(ny + 1):
            cx = x0 + (x1 - x0) * ix / max(nx, 1)
            cy = y0 + (y1 - y0) * iy / max(ny, 1)
            z0 = zfun(cx, cy)
            for _ in range(per):
                hh = random.uniform(*h)
                ox = random.uniform(-gap / 2, gap / 2)
                oy = random.uniform(-gap / 2, gap / 2)
                bx, by = bl(cx + ox, cy + oy)
                sub = bmesh.new()
                bmesh.ops.create_cone(sub, cap_ends=True, cap_tris=False, segments=5,
                                      radius1=rad, radius2=rad * 0.25, depth=hh)
                bmesh.ops.rotate(sub, verts=sub.verts,
                                 matrix=__import__('mathutils').Matrix.Rotation(
                                     random.uniform(-splay, splay), 3, 'X'))
                bmesh.ops.translate(sub, vec=Vector((bx, by, z0 + hh / 2)), verts=sub.verts)
                if tip > 0.0:
                    t2 = bmesh.new()
                    bmesh.ops.create_icosphere(t2, subdivisions=1, radius=tip)
                    bmesh.ops.scale(t2, vec=Vector((1, 1, 0.6)), verts=t2.verts)
                    bmesh.ops.translate(t2, vec=Vector((bx, by, z0 + hh)), verts=t2.verts)
                    tm = bpy.data.meshes.new('t'); t2.to_mesh(tm); t2.free()
                    bmv.from_mesh(tm); bpy.data.meshes.remove(tm)
                tmp = bpy.data.meshes.new('t'); sub.to_mesh(tmp); sub.free()
                bmv.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    bmv.to_mesh(me); bmv.free()
    o = bpy.data.objects.new('stalks', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)



# ─────────────────────────────────────────────────────────────────
# 지형 — 등고선에서 높이면을 만든다
# ─────────────────────────────────────────────────────────────────
import numpy as np

GRID = 1.0                              # 높이면 격자 (m)
PAD = 8.0                               # 부지 밖으로 조금 더 만든다 — 실개천이 공중에 뜨지 않게


def _resample(pts, step=1.5):
    """폴리라인을 일정 간격으로 다시 나눈다."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(round(L / step)))
        out += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(1, k + 1)]
    return out


def _seg_dist(px, py, poly):
    """격자점들에서 닫힌 다각형 변까지의 최단거리 (numpy)."""
    d = np.full(px.shape, 1e9)
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0.0, 1.0)
        d = np.minimum(d, np.hypot(px - (ax + t * vx), py - (ay + t * vy)))
    return d


def _inside_np(px, py, poly):
    """짝수-홀수 규칙 (numpy)."""
    inside = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > py) != (yj > py))
        with np.errstate(divide='ignore', invalid='ignore'):
            xint = (xj - xi) * (py - yi) / np.where(yj - yi == 0, 1e-9, yj - yi) + xi
        inside ^= cond & (px < xint)
        j = i
    return inside


_HF = {}                                # 높이면 캐시 (격자, x0, y0)


def _heightfield():
    """등고선 + 계획고 점을 역거리가중(IDW)으로 펴고, 못·개천을 판다."""
    if _HF:
        return _HF['z'], _HF['x0'], _HF['y0']
    cx, cy, cz = [], [], []
    for z, pts in CONTOURS:                         # 등고선을 점으로 흩는다
        for x, y in _resample(pts, 1.5):
            cx.append(x); cy.append(y); cz.append(z)
    for x, y, z in SPOTS:
        for _ in range(6):                          # 계획고 점은 무겁게 — 여섯 번 넣는다
            cx.append(x); cy.append(y); cz.append(z)
    cx, cy, cz = np.array(cx), np.array(cy), np.array(cz)

    xs = np.arange(-PAD, W + PAD + GRID, GRID)
    ys = np.arange(-PAD, D + PAD + GRID, GRID)
    PX, PY = np.meshgrid(xs, ys, indexing='ij')
    d2 = (PX[..., None] - cx) ** 2 + (PY[..., None] - cy) ** 2 + 0.25
    wgt = 1.0 / d2 ** 1.6
    Z = (wgt * cz).sum(axis=-1) / wgt.sum(axis=-1)

    # 못·습지를 판다 — 가장자리에서 2m 안쪽까지 완만하게 내려간다
    for poly, zw in ((POND, Z_POND), (MARSH, Z_MARSH)):
        ins = _inside_np(PX, PY, poly)
        dist = _seg_dist(PX, PY, poly)
        t = np.clip(dist / 2.0, 0.0, 1.0)
        Z = np.where(ins, Z * (1 - t) + Z_BASIN * t, Z)
    # 실개천 — 폴리라인 양쪽 폭만큼 판다
    ds = np.full(PX.shape, 1e9)
    for a, b in zip(STREAM, STREAM[1:]):
        vx, vy = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vy * vy
        t = np.clip(((PX - a[0]) * vx + (PY - a[1]) * vy) / max(L2, 1e-9), 0.0, 1.0)
        ds = np.minimum(ds, np.hypot(PX - (a[0] + t * vx), PY - (a[1] + t * vy)))
    t = np.clip(ds / (STREAM_W / 2 + 1.2), 0.0, 1.0)
    Z = np.minimum(Z, Z * t + (Z_STREAM - 0.35) * (1 - t))

    # 포장 자리는 평탄하게 깎는다 — 가장자리 1.5m 는 주변 지반과 이어 준다
    for (x0, x1, y0, y1), zf in FLATS:
        dx = np.maximum(np.maximum(x0 - PX, PX - x1), 0.0)
        dy = np.maximum(np.maximum(y0 - PY, PY - y1), 0.0)
        t = np.clip(np.hypot(dx, dy) / 1.5, 0.0, 1.0)
        Z = Z * t + zf * (1 - t)

    _HF.update(z=Z, x0=-PAD, y0=-PAD)
    return Z, -PAD, -PAD


def height(x, y):
    """도면 좌표에서의 지반 표고 (겹선형 보간)."""
    Z, x0, y0 = _heightfield()
    fx = (x - x0) / GRID
    fy = (y - y0) / GRID
    i = min(max(int(fx), 0), Z.shape[0] - 2)
    j = min(max(int(fy), 0), Z.shape[1] - 2)
    tx, ty = fx - i, fy - j
    return ((Z[i, j] * (1 - tx) + Z[i + 1, j] * tx) * (1 - ty)
            + (Z[i, j + 1] * (1 - tx) + Z[i + 1, j + 1] * tx) * ty)


def terrain():
    """지형면 — 격자 메시."""
    Z, x0, y0 = _heightfield()
    nx, ny = Z.shape
    me = bpy.data.meshes.new('terrain')
    bmv = bmesh.new()
    vs = [[None] * ny for _ in range(nx)]
    for i in range(nx):
        for j in range(ny):
            x, y = x0 + i * GRID, y0 + j * GRID
            bx, by = bl(x, y)
            # **지형을 포장 판보다 6cm 내린다** — 같은 높이면 Cycles 에서 겹쳐 새까맣다
            vs[i][j] = bmv.verts.new((bx, by, Z[i, j] - 0.06))
    for i in range(nx - 1):
        for j in range(ny - 1):
            bmv.faces.new([vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]])
    bmv.normal_update()
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('terrain', me)
    bpy.context.collection.objects.link(o)
    o.modifiers.new('smooth', 'SMOOTH').iterations = 2
    return put(o, mat('ground', (0.24, 0.40, 0.13), spread=0.30, scale=420, bump=1.1))


def _face_up(bmv):
    """수평 판의 면이 아래를 보면 뒤집는다 — 뒤집힌 면은 빛을 못 받아 새까맣다."""
    bmv.normal_update()
    bad = [f for f in bmv.faces if f.normal.z < 0]
    if bad:
        bmesh.ops.reverse_faces(bmv, faces=bad)


def water_plane(poly, z, m, inset=0.0):
    """닫힌 물가를 수면 판으로.

    **부채꼴(중심에서 삼각형)로 만들면 안 된다** — 습지처럼 오목한 도형에서는
    삼각형이 도형 밖으로 튀어나가 잔디 위에 검은 쐐기가 생긴다. 평면이므로
    ngon 하나로 두고 ear-clipping 에 맡긴다.
    """
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    me = bpy.data.meshes.new('water')
    bmv = bmesh.new()
    vs = []
    for x, y in poly:
        if inset:
            L = math.hypot(x - cx, y - cy) or 1.0
            x, y = x + (cx - x) / L * inset, y + (cy - y) / L * inset
        vs.append(bmv.verts.new((*bl(x, y), z)))
    bmv.faces.new(vs)
    bmesh.ops.triangulate(bmv, faces=bmv.faces[:])
    _face_up(bmv)
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('water', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def strip(pts, width, z_off, m, zfun=None):
    """폴리라인을 따라 띠(관찰로·실개천 등)를 깐다."""
    me = bpy.data.meshes.new('strip')
    bmv = bmesh.new()
    rows = []
    for k, (x, y) in enumerate(pts):
        if k == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif k == len(pts) - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[k + 1][0] - pts[k - 1][0], pts[k + 1][1] - pts[k - 1][1]
        L = math.hypot(dx, dy) or 1.0
        nx_, ny_ = -dy / L * width / 2, dx / L * width / 2
        z = (zfun(x, y) if zfun else height(x, y)) + z_off
        rows.append((bmv.verts.new((*bl(x + nx_, y + ny_), z)),
                     bmv.verts.new((*bl(x - nx_, y - ny_), z))))
    for a, b in zip(rows, rows[1:]):
        bmv.faces.new([a[0], a[1], b[1], b[0]])
    _face_up(bmv)                       # 서→동이냐 동→서냐에 따라 뒤집힌다
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('strip', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def poly_pad(pts, z, m):
    """다각형 포장 판 — 윗면이 z. 지형을 그 높이로 평탄하게 깎아 두었으므로 판만 얹으면 된다."""
    return water_plane(pts, z, m)


def ramp(pts_z, m):
    """높이가 다른 두 변을 잇는 비탈 판 — [(x, y, z), ...] 네 점."""
    me = bpy.data.meshes.new('ramp')
    bmv = bmesh.new()
    vs = [bmv.verts.new((*bl(x, y), z)) for x, y, z in pts_z]
    bmv.faces.new(vs)
    _face_up(bmv)
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('ramp', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def pad(x0, x1, y0, y1, z, m, h=0.12):
    """평평한 포장 판 — **윗면이 계획고에 오게** 한다.

    slab() 은 z 를 윗면으로 쓴다. 여기서 z-h 를 넘기면 포장이 12cm 잠겨
    지형(계획고-6cm)에 덮여 통째로 사라진다 — 처음에 그렇게 당했다.
    """
    return slab(x0, x1, y0, y1, z, m, h=h)

def tree(x, y, kind, scale=1.0, leaf_rgb=None, name=''):
    """교목 한 주. **수관은 공 하나가 아니라 작은 덩이 여럿**을 겹쳐 만든다 —
    매끈한 공은 사탕처럼 보이고, 그것이 '만화 같다'의 가장 큰 원인이다."""
    z = height(x, y)
    bx, by = bl(x, y)
    bark = mat('bark', (0.19, 0.14, 0.10), rough=0.9, spread=0.25, scale=200, bump=0.9)
    leaf = mat('canopy' + (name or ''), leaf_rgb or (0.09, 0.20, 0.07),
               rough=0.95, spread=0.30, scale=90, bump=1.0)
    ht = {'cone': 3.0, 'weep': 2.7, 'ball': 2.7}[kind] * scale
    cyl(x, y, z, 0.30 * scale, ht, bark, verts=12)
    me = bpy.data.meshes.new('crown')
    bmv = bmesh.new()
    if kind == 'cone':                      # 침엽·원추형 (메타세쿼이아 · 은행)
        lobes, rad, top, spread_r = 10, 0.74, 3.4, 0.68
    elif kind == 'weep':                    # 처지는 덩이 (버드나무)
        lobes, rad, top, spread_r = 12, 0.80, 1.7, 0.72
    else:                                   # 둥근 (참나무류 · 느티 · 산벚)
        lobes, rad, top, spread_r = 11, 0.78, 1.8, 0.70
    rad, top, spread_r = rad * scale, top * scale, spread_r * scale
    for i in range(lobes):
        t = i / max(lobes - 1, 1)
        if kind == 'cone':
            rr = rad * (1.0 - 0.75 * t)
            off = spread_r * (1.0 - t)
        else:
            rr = rad * (0.75 + 0.35 * math.sin(math.pi * t))
            off = spread_r
        ang = 2.399 * i
        px = bx + math.cos(ang) * off * random.uniform(0.3, 1.0)
        py = by + math.sin(ang) * off * random.uniform(0.3, 1.0)
        pz = z + ht + top * t * (1.0 if kind == 'cone' else 0.55) + rr * 0.4
        sub = bmesh.new()
        bmesh.ops.create_icosphere(sub, subdivisions=2, radius=rr * random.uniform(0.85, 1.15))
        bmesh.ops.scale(sub, vec=Vector((1.0, 1.0, 0.8 if kind != 'cone' else 0.9)),
                        verts=sub.verts)
        bmesh.ops.translate(sub, vec=Vector((px, py, pz)), verts=sub.verts)
        tmp = bpy.data.meshes.new('t'); sub.to_mesh(tmp); sub.free()
        bmv.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    bmv.to_mesh(me); bmv.free()
    o = bpy.data.objects.new('crown', me)
    bpy.context.collection.objects.link(o)
    return put(o, leaf)


def shelter(cx, cy, z):
    """이동식 쉘터 4x4 — 기둥 넷 + 낮은 모임지붕."""
    wood = mat('wood', (0.36, 0.23, 0.13), rough=0.8, spread=0.20, scale=120, bump=0.5)
    roof = mat('roof', (0.34, 0.20, 0.14), rough=0.75, spread=0.16, scale=60, bump=0.7)
    for dx in (-1.8, 1.8):
        for dy in (-1.8, 1.8):
            cyl(cx + dx, cy + dy, z, 0.16, 2.3, wood, verts=10)
    bx, by = bl(cx, cy)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.05, radius2=0.0, depth=0.85,
                                    location=(bx, by, z + 2.3 + 0.42),
                                    rotation=(0, 0, math.radians(45)))
    put(bpy.context.object, roof)
    box(cx, cy, z + 2.22, 4.3, 4.3, 0.10, roof)       # 처마 판


def pergola(cx, cy, z):
    """원형퍼걸러 지름 3 — 기둥 여섯 + **방사형 살대 지붕**(통판이면 탁자로 보인다)."""
    wood = mat('wood', (0.46, 0.31, 0.18), rough=0.75, spread=0.18, scale=90, bump=0.25)
    for i in range(6):
        a = 2 * math.pi * i / 6
        cyl(cx + math.cos(a) * 1.35, cy + math.sin(a) * 1.35, z, 0.14, 2.3, wood)
    bx, by = bl(cx, cy)
    for i in range(6):                                    # 살대 6개
        a = math.pi * i / 6
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, z + 2.38))
        o = bpy.context.object
        o.scale = (PERG_D * 0.94, 0.10, 0.09)
        o.rotation_euler[2] = a
        put(o, wood)
    cyl(cx, cy, z + 2.46, PERG_D, 0.05, wood, verts=28)          # 지붕판(살대를 덮는다)
    bx2, by2 = bl(cx, cy)
    bpy.ops.mesh.primitive_torus_add(location=(bx2, by2, z + 2.40),
                                     major_radius=PERG_D / 2, minor_radius=0.06,
                                     major_segments=28, minor_segments=6)
    put(bpy.context.object, wood)                                 # 테두리



# ─────────────────────────────────────────────────────────────────
# 401 전용 부품
# ─────────────────────────────────────────────────────────────────
def _walk(pts, n):
    """폴리라인을 길이 비례로 n+1 점으로 다시 나눈다."""
    seg = [math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(pts, pts[1:])]
    tot = sum(seg)
    out, k, run = [pts[0]], 0, 0.0
    for i in range(1, n + 1):
        want = tot * i / n
        while k < len(seg) - 1 and run + seg[k] < want:
            run += seg[k]; k += 1
        t = 0.0 if seg[k] == 0 else (want - run) / seg[k]
        a, b = pts[k], pts[k + 1]
        out.append((a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t))
    return out


def deck_poly(outer, inner, z, m, n=160):
    """관찰로 — 바깥선과 안선 사이의 띠.

    **한 ngon 으로 묶으면 안 된다** — 삼각분할이 even-odd 규칙을 안 써서 가운데
    (산림지구)까지 메워지고 법선이 뒤집혀 새까맣다.
    **길이 비례로만 짝지어도 안 된다** — 한쪽에 꺾임이 많으면 짝이 어긋나 띠가 접히고,
    접힌 자리가 검은 쐐기로 남는다. 바깥선의 각 점에서 **가장 가까운 안선 점**을 쓰되
    **차례가 뒤로 가지 않게**(단조) 막는다.
    """
    A = _walk(list(outer), n)
    B = _walk(list(reversed(inner)), n * 4)
    # **창을 좁게 두면 급한 꺾임에서 짝을 놓쳐 면이 접힌다**(검은 쐐기).
    # 전역 최근접으로 고른 뒤 차례만 단조로 보정한다.
    idx = []
    for ax, ay in A:
        bj = min(range(len(B)), key=lambda j2: (B[j2][0] - ax) ** 2 + (B[j2][1] - ay) ** 2)
        idx.append(bj)
    for k in range(1, len(idx)):
        idx[k] = max(idx[k], idx[k - 1])
    idx[0], idx[-1] = 0, len(B) - 1
    me = bpy.data.meshes.new('boardwalk')
    bmv = bmesh.new()
    va = [bmv.verts.new((*bl(x, y), z)) for x, y in A]
    vb = [bmv.verts.new((*bl(*B[k]), z)) for k in idx]
    for k in range(n):
        if idx[k] == idx[k + 1]:                     # 안선이 제자리면 삼각형으로
            bmv.faces.new([va[k], vb[k], va[k + 1]])
        else:
            bmv.faces.new([va[k], vb[k], vb[k + 1], va[k + 1]])
    _face_up(bmv)
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('boardwalk', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def deck_posts(pts, z, m, step=4.0, w=0.16):
    """데크 밑 기둥 — 지반까지 내린다."""
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for i in range(max(1, int(L / step))):
            t = (i + 0.5) / max(1, int(L / step))
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            g = height(x, y)
            if z - g > 0.25:
                box(x, y, g - 0.2, w, w, z - g + 0.2, m)


def obs_deck(cx, cy, w, h, deg, z, wood, rail):
    """관찰데크 — 상판 + 난간 + 기둥."""
    a = math.radians(deg)
    box(cx, cy, z - 0.14, w, h, 0.14, wood, rot=-a)
    for dx, dy in ((-w / 2 + 0.1, -h / 2 + 0.1), (w / 2 - 0.1, -h / 2 + 0.1),
                   (-w / 2 + 0.1, h / 2 - 0.1), (w / 2 - 0.1, h / 2 - 0.1)):
        px = cx + dx * math.cos(a) - dy * math.sin(a)
        py = cy + dx * math.sin(a) + dy * math.cos(a)
        g = height(px, py)
        box(px, py, g - 0.2, 0.14, 0.14, z - g + 0.2, wood)          # 기둥
        box(px, py, z - 0.14, 0.09, 0.09, 0.85, rail)                # 난간 기둥
    for s in (-1, 1):                                                 # 난간 가로대 두 줄
        for hh in (0.45, 0.78):
            ox, oy = -s * h / 2 * math.sin(a), s * h / 2 * math.cos(a)
            box(cx + ox, cy - oy, z + hh, w, 0.06, 0.06, rail, rot=-a)


def bird_hide(x0, x1, y0, y1, z, wood, roof, glass):
    """조류관찰소 — 낮은 목조 오두막, 관찰창이 뚫려 있다."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = x1 - x0, y1 - y0
    box(cx, cy, z - 0.15, sx, sy, 0.15, wood)                         # 바닥판
    for (bx, by, bw, bh) in ((cx, y0 + 0.1, sx, 0.2), (cx, y1 - 0.1, sx, 0.2),
                             (x0 + 0.1, cy, 0.2, sy), (x1 - 0.1, cy, 0.2, sy)):
        box(bx, by, z, bw, bh, 1.05, wood)                            # 아래 벽
        box(bx, by, z + 1.45, bw, bh, 0.75, wood)                     # 관찰창 위 벽
        box(bx, by, z + 1.05, bw, bh, 0.40, glass)                    # 관찰창
    box(cx, cy, z + 2.2, sx + 0.7, sy + 0.7, 0.16, roof)              # 지붕


def pergola4(cx, cy, z, wood):
    """파고라 4 x 4 — 기둥 넷 + **두 켜 격자 지붕**.

    살대를 0.45m 간격에 7cm 폭으로 두었더니 그늘이 거의 없었다(햇빛이 다 샌다).
    큰 보 넷 위에 살대를 0.17m 간격으로 촘촘히 깔고, 그 위에 가로 살대를 한 켜 더
    올려 **두 켜가 엇갈리게** 한다 — 실제 파고라의 짙은 줄그림자가 이렇게 난다.
    """
    for dx in (-1.8, 1.8):
        for dy in (-1.8, 1.8):
            box(cx + dx, cy + dy, z, 0.18, 0.18, 2.4, wood)
    for d in (-1.9, 1.9):                                 # 테두리 보
        box(cx + d, cy, z + 2.40, 0.16, 4.0, 0.18, wood)
        box(cx, cy + d, z + 2.40, 4.0, 0.16, 0.18, wood)
    for d in (-0.62, 0.62):                               # 가운데 보 둘
        box(cx + d, cy, z + 2.40, 0.14, 4.0, 0.18, wood)
    n = 18                                                # 아래 켜 — 서까래
    for i in range(n):
        box(cx - 1.85 + i * (3.7 / (n - 1)), cy, z + 2.58, 0.10, 3.9, 0.10, wood)
    m = 12                                                # 위 켜 — **판재**(틈 5cm)
    for i in range(m):                                    # 살대만으로는 빛이 24% 샌다
        box(cx, cy - 1.80 + i * (3.6 / (m - 1)), z + 2.68, 3.9, 0.29, 0.06, wood)


def bench(cx, cy, deg, z, wood, leg):
    """평의자 1.8 x 0.4."""
    a = -math.radians(deg)
    box(cx, cy, z + 0.40, 1.8, 0.42, 0.08, wood, rot=a)
    for d in (-0.7, 0.7):
        px = cx + d * math.cos(-a)
        py = cy + d * math.sin(-a)
        box(px, py, z, 0.09, 0.36, 0.40, leg, rot=a)


def tree_grate(cx, cy, z, m_grate, m_soil):
    """수목보호대 2 x 2 — **사각 틀이 보여야 한다.**

    위에서 내려다보면 수관이 틀을 덮는다. 틀 모서리는 중심에서 1.41m 이므로
    여기에 심는 느티나무는 수관 반지름을 그보다 작게 준다(build 의 k 값).
    """
    for (bx, by, bw, bh) in ((cx, cy - 0.88, 2.0, 0.24), (cx, cy + 0.88, 2.0, 0.24),
                             (cx - 0.88, cy, 0.24, 2.0), (cx + 0.88, cy, 0.24, 2.0)):
        box(bx, by, z - 0.05, bw, bh, 0.14, m_grate)
    slab(cx - 0.76, cx + 0.76, cy - 0.76, cy + 0.76, z - 0.01, m_soil, h=0.06)


def sign(cx, cy, z, post, panel, w=0.6, h=1.9):
    box(cx, cy, z, 0.09, 0.09, h * 0.55, post)
    box(cx, cy, z + h * 0.5, w, 0.08, h * 0.5, panel)


# ─────────────────────────────────────────────────────────────────
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    m_water = mat('water', (0.05, 0.17, 0.22), rough=0.04, spread=0.06, scale=3, bump=0.06)
    m_marsh = mat('marsh', (0.09, 0.19, 0.17), rough=0.10, spread=0.10, scale=6, bump=0.10)
    m_lawn  = mat('lawn',  (0.28, 0.47, 0.14), spread=0.26, scale=520, bump=1.4)
    m_block = brick_mat('block', (0.78, 0.75, 0.68), (0.72, 0.69, 0.62), (0.58, 0.56, 0.52), scale=7.0)
    m_plaza = brick_mat('plaza', (0.80, 0.77, 0.70), (0.74, 0.71, 0.64), (0.60, 0.58, 0.54), scale=6.0)
    m_wooddk = mat('wooddeck', (0.46, 0.32, 0.19), rough=0.78, spread=0.20, scale=140, bump=0.55)
    m_wood  = mat('wood',  (0.40, 0.27, 0.16), rough=0.80, spread=0.18, scale=110, bump=0.45)
    m_roof  = mat('roof',  (0.33, 0.20, 0.14), rough=0.75, spread=0.16, scale=60, bump=0.7)
    m_glass = mat('glass', (0.10, 0.14, 0.16), rough=0.12, spread=0.04, scale=8, bump=0.05)
    m_rail  = mat('rail',  (0.30, 0.22, 0.15), rough=0.80, spread=0.14, scale=100, bump=0.30)
    m_steel = mat('steel', (0.26, 0.26, 0.27), rough=0.45, spread=0.06, scale=40, bump=0.15)
    m_soil  = mat('soil',  (0.24, 0.18, 0.12), spread=0.28, scale=120, bump=0.8)
    m_kerb  = mat('kerb',  (0.62, 0.60, 0.56), rough=0.85, spread=0.10, scale=60, bump=0.25)
    m_panel = mat('panel', (0.84, 0.83, 0.79), rough=0.55, spread=0.05, scale=30, bump=0.10)

    terrain()

    # ── 물 ──────────────────────────────────────────────────────
    water_plane(POND, Z_POND, m_water)
    water_plane(MARSH, Z_MARSH, m_marsh)
    strip(STREAM, STREAM_W, 0.0, m_water, zfun=lambda x, y: Z_STREAM)

    # ── 포장 ────────────────────────────────────────────────────
    pad(*NE_PLAZA, Z_NE_PLAZA, m_plaza)
    pad(*EAST_WALK, Z_NE_PLAZA, m_plaza)
    pad(*MEET, 72.00, m_plaza)
    pad(*SPINE, 71.80, m_block)
    pad(*SE_PLAZA, Z_SE_PLAZA, m_plaza)
    poly_pad(REST_POLY, 71.65, m_block)
    # 관찰로(72.0) ↔ 휴게공간(71.65) 을 잇는 사선 진입로. 이게 없으면 데크에서
    # 휴게공간으로 들어갈 길이 없다
    ramp([(LINK[0][0], LINK[0][1], Z_DECK), (LINK[1][0], LINK[1][1], Z_DECK),
          (LINK[2][0], LINK[2][1], 71.66), (LINK[3][0], LINK[3][1], 71.66)], m_wooddk)

    # ── 관찰로 (목재데크) ───────────────────────────────────────
    deck_poly(RO_OUT, RO_IN, Z_DECK, m_wooddk)
    deck_posts(RO_OUT, Z_DECK, m_wood)
    deck_posts(RO_IN, Z_DECK, m_wood)
    # **관찰로와 같은 72.0 에 두면 겹친 자리가 z-파이팅으로 새까맣다.** 1.2cm 올린다
    strip(SPUR, 2.0, 0.012, m_wooddk, zfun=lambda x, y: Z_DECK)

    # ── 관찰데크 5 · 조류관찰소 ─────────────────────────────────
    for cx, cy, w, h, deg in DECKS:
        obs_deck(cx, cy, w, h, deg, Z_DECK, m_wooddk, m_rail)
    bird_hide(*BIRD_HIDE, Z_DECK, m_wood, m_roof, m_glass)

    # ── 휴게공간 안 시설 ────────────────────────────────────────
    pergola4((PERGOLA[0] + PERGOLA[1]) / 2, (PERGOLA[2] + PERGOLA[3]) / 2, 71.65, m_wood)

    # ── 시설물 ──────────────────────────────────────────────────
    for cx, cy in GRATES:
        tree_grate(cx, cy, height(cx, cy) + 0.12, m_steel, m_soil)
    for cx, cy, deg in BENCHES:
        bench(cx, cy, deg, height(cx, cy) + 0.05, m_wood, m_steel)
    for cx, cy in BINS:
        cyl(cx, cy, height(cx, cy), 0.6, 0.85, m_steel)
    for cx, cy in SIGNS:
        sign(cx, cy, height(cx, cy), m_steel, m_panel)
    sign(*BIG_SIGN, height(*BIG_SIGN), m_steel, m_panel, w=1.8, h=2.2)

    # ── 식재 — 성운 배식설계도(답안지 III) ─────────────────────
    #
    # **구역을 도면 라벨로 잡는다.** 처음에 거꾸로 심었다 —
    #   기존수림 (9.5, 46.8) · 저수지구 (29, 7.2) · 습지지구 (31.5, 31.8) · 산림지구 (38.5, 47.2)
    # 즉 **습지지구가 관찰로 루프 안**이고 **산림지구는 루프 바깥 남쪽**이다.
    # 습지지구에는 교목을 심지 않는다 — 수생·수변 초본류다.
    def wood_x(y):
        """기존수림 경계선(WOOD_EDGE)의 그 y 에서의 x."""
        for a, b in zip(WOOD_EDGE, WOOD_EDGE[1:]):
            if a[1] <= y <= b[1]:
                t = (y - a[1]) / max(b[1] - a[1], 1e-6)
                return a[0] + (b[0] - a[0]) * t
        return WOOD_EDGE[0][0] if y < WOOD_EDGE[0][1] else WOOD_EDGE[-1][0]

    PAVED = [NE_PLAZA, EAST_WALK, MEET, SPINE, SE_PLAZA, REST]

    def free(x, y, m=1.2):
        """포장·물을 피한다."""
        if not (0.6 < x < W - 0.6 and 0.6 < y < D - 0.6):
            return False
        for (x0, x1, y0, y1) in PAVED:
            if x0 - m < x < x1 + m and y0 - m < y < y1 + m:
                return False
        return not (_inside((x, y), POND) or _inside((x, y), MARSH))

    def on_deck(x, y, m=1.0):
        """관찰로 띠 위(바깥선 안 · 안선 밖)."""
        return _inside((x, y), RO_OUT) and not _inside((x, y), RO_IN)

    def d_loop(x, y):
        """관찰로 바깥선까지의 거리."""
        best = 1e9
        for a, b in zip(RO_OUT, RO_OUT[1:] + RO_OUT[:1]):
            vx, vy = b[0] - a[0], b[1] - a[1]
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - a[0]) * vx + (y - a[1]) * vy) / L2))
            best = min(best, math.hypot(x - (a[0] + t * vx), y - (a[1] + t * vy)))
        return best

    def d_built(x, y):
        """조류관찰소·관찰데크까지의 거리."""
        bx, by = (BIRD_HIDE[0] + BIRD_HIDE[1]) / 2, (BIRD_HIDE[2] + BIRD_HIDE[3]) / 2
        best = math.hypot(x - bx, y - by) - 3.2
        for cx, cy, *_ in DECKS:
            best = min(best, math.hypot(x - cx, y - cy) - 2.0)
        return best

    # **교목은 관찰로에서 3.5m, 시설에서 3.5m 를 띄운다.** 안 띄우면 축측도에서
    # 수관이 관찰로와 조류관찰소를 덮어 버린다(위에서 보면 멀쩡한데 비스듬히 보면 가린다)
    CLEAR_PATH, CLEAR_BUILT = 3.5, 3.5

    def in_forest(x, y, clear=True):
        """산림지구 — 관찰로 루프 **바깥**, 기존수림 **동쪽**, 공원 보행로 서쪽."""
        if not (free(x, y) and not _inside((x, y), RO_OUT)
                and x > wood_x(y) + 0.5 and x < 63.0):
            return False
        if clear and (d_loop(x, y) < CLEAR_PATH or d_built(x, y) < CLEAR_BUILT):
            return False
        return True

    def spots(n, box, test, gap=2.6, tries=6000):
        x0, x1, y0, y1 = box
        out = []
        for _ in range(tries):
            if len(out) >= n:
                break
            x, y = random.uniform(x0, x1), random.uniform(y0, y1)
            if not test(x, y):
                continue
            if any(math.hypot(x - px, y - py) < gap for px, py in out):
                continue
            out.append((x, y))
        return out

    # 1) 수목보호대 5 — **느티나무를 심되 사각 틀이 보이게** 수관을 줄인다.
    #    기본 크기(수관 반지름 2.3m)면 2x2 틀(모서리 1.41m)을 통째로 덮는다
    for cx, cy in GRATES:
        plant(cx, cy, '느티나무', k=0.58)

    # 2) 동측 완충식재 — 은행나무 18 (주택가와의 기능 분리)
    ge = 0
    for i in range(30):
        y = 1.5 + i * 2.0
        if ge >= 18 or y > D - 1.0:
            break
        if free(88.6, y, m=0.4):
            plant(88.6, y, '은행나무')
            ge += 1

    # 3) 유도식재 — 느티나무 (주동선을 따라)
    for x, y in ((65.6, 28.0), (65.6, 34.0), (65.6, 40.0), (65.6, 46.0), (62.4, 16.0)):
        if free(x, y, m=0.5):
            plant(x, y, '느티나무')

    # 4) 기존수림 — 서측. 경계선 서쪽을 빽빽하게
    for _ in range(420):
        y = random.uniform(0.8, 59.2)
        x = random.uniform(0.8, max(1.0, wood_x(y) - 0.8))
        if free(x, y) and d_loop(x, y) > CLEAR_PATH and d_built(x, y) > CLEAR_BUILT:
            tree(x, y, random.choice(['ball', 'ball', 'cone', 'weep']))

    # 5) **산림지구 — 교목 + 관목.** 루프 바깥, 기존수림 동쪽
    FZ = (13.0, 62.0, 2.0, 59.0)
    # 소나무 7 과 산벚나무 6 은 **동측 진입광장 일대**로 간다(아래 11 참조)
    plan = [('갈참나무', 5), ('졸참나무', 9), ('상수리나무', 4),
            ('층층나무', 7), ('산벚나무', 14), ('느티나무', 2)]
    need = sum(c for _, c in plan)
    pts = spots(need + 40, FZ, in_forest, gap=3.0)
    random.shuffle(pts)
    k = 0
    for name, cnt in plan:
        for _ in range(cnt):
            if k >= len(pts):
                break
            plant(*pts[k], name); k += 1
    # 산림지구를 메우는 배경목
    for x, y in spots(120, FZ, in_forest, gap=2.8):
        tree(x, y, random.choice(['ball', 'ball', 'weep', 'cone']))
    # 산림지구 관목 — 병꽃나무 300 · 진달래 · 철쭉
    sh = [(random.uniform(*FZ[:2]), random.uniform(*FZ[2:])) for _ in range(2200)]
    scatter_species([q for q in sh if in_forest(*q, clear=False) and d_loop(*q) > 1.2],
                    ['병꽃나무', '진달래', '철쭉'], height)   # 관목은 1.2m 만 띄운다

    # 6) 저수지구 둘레 — 버드나무 · 메타세쿼이아 · 산딸나무 (물가 바깥)
    near_pond = lambda x, y: (free(x, y) and d_loop(x, y) > CLEAR_PATH
                              and d_built(x, y) > CLEAR_BUILT
                              and 1.0 < min(math.hypot(x - px, y - py) for px, py in POND) < 6.0)
    wp = spots(5, (12.0, 42.0, 0.5, 22.0), near_pond, gap=4.0)
    for q in wp:
        plant(*q, '버드나무')
    for q in spots(7, (12.0, 44.0, 0.5, 22.0), near_pond, gap=4.0):
        plant(*q, '메타세쿼이아')
    for q in spots(5, (30.0, 60.0, 12.0, 24.0), lambda x, y: in_forest(x, y), gap=4.0):
        plant(*q, '산딸나무')

    # 7) **습지지구(루프 안) — 초본류만.** 교목·배경목을 두지 않는다
    def in_marshzone(x, y):
        return (_inside((x, y), RO_IN) and free(x, y, m=0.4)
                and min(math.hypot(x - mx, y - my) for mx, my in MARSH) > 0.8)

    hb = [(random.uniform(20.0, 58.0), random.uniform(8.0, 41.0)) for _ in range(2600)]
    hb = [q for q in hb if in_marshzone(*q)]
    scatter_species(hb, ['갈대', '부들', '골풀', '꽃창포', '부처꽃', '쑥부쟁이'], height)

    # 8) 수생·수변 — 저수지·습지 물가
    def rim(poly, step, off):
        cx = sum(q[0] for q in poly) / len(poly)
        cy = sum(q[1] for q in poly) / len(poly)
        out = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            for t in range(max(1, int(L / step))):
                u = (t + 0.5) / max(1, int(L / step))
                x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                d = math.hypot(x - cx, y - cy) or 1.0
                out.append((x + (x - cx) / d * off, y + (y - cy) / d * off))
        return [q for q in out if 0.4 < q[0] < W - 0.4 and 0.4 < q[1] < D - 0.4
                and not on_deck(*q)]

    scatter_species(rim(POND, 1.0, -0.6), ['부들', '갈대'], lambda x, y: Z_POND)
    scatter_species(rim(POND, 1.2, 0.9), ['골풀', '꽃창포'], height)
    scatter_species(rim(MARSH, 0.9, -0.5), ['갈대', '부들', '골풀'], lambda x, y: Z_MARSH)
    scatter_species(rim(MARSH, 1.0, 1.0), ['갯버들', '꽃창포', '부처꽃'], height)
    scatter_species(rim(POND, 1.4, 2.2), ['갯버들'], height)

    # 9) **동측 진입광장 일대 — 도면대로.**
    #    진입로(보행로) 쪽에 철쭉 띠 → 안쪽은 잔디 → 소나무 7 → 그 위(북쪽) 산벚나무 6
    #    → 오른쪽 도로변에 은행나무 열식.
    #    마운딩 전체에 진달래·철쭉을 흩어 놓았던 것을 걷어낸다 — 도면은 띠다
    band = []
    for _ in range(1400):                       # 철쭉 띠 — 보행로 동쪽 2.5m
        x, y = random.uniform(72.3, 74.8), random.uniform(18.0, 52.0)
        if free(x, y, m=0.3):
            band.append((x, y))
    scatter_species(band, ['철쭉', '철쭉', '진달래'], height)
    for _ in range(500):                        # 남동 진입광장 둘레에도 조금
        x, y = random.uniform(66.5, 80.0), random.uniform(50.0, 52.0)
        if free(x, y, m=0.3):
            band.append((x, y))
    scatter_species(band[-400:], ['철쭉', '진달래'], height)

    for q in spots(7, (76.0, 86.0, 32.0, 50.0),                     # 소나무 7 (지표식재)
                   lambda x, y: free(x, y, m=1.5), gap=3.4):
        plant(*q, '소나무')
    for q in spots(6, (76.0, 86.0, 19.0, 31.0),                     # 산벚나무 6 — 소나무 위쪽
                   lambda x, y: free(x, y, m=1.5), gap=3.4):
        plant(*q, '산벚나무')

    # 10) 광장 주변 관목 — 무궁화 · 회양목
    for (x0, x1, y0, y1) in ((64.0, 66.8, 25.0, 31.0), (64.0, 66.8, 45.0, 52.0),
                             (79.5, 82.0, 6.0, 13.0), (79.5, 83.0, 53.0, 59.5)):
        pts2 = [(random.uniform(x0, x1), random.uniform(y0, y1)) for _ in range(30)]
        scatter_species([q for q in pts2 if free(*q, m=0.3)], ['회양목', '무궁화', '병꽃나무'], height)

    # ── 카메라 · 빛
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = 102.0
    cam_d.clip_end = 400
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.collection.objects.link(cam)
    # 45° 로 눕힌 직교 카메라는 **cam_y + cam_z 자리를 겨냥한다**(시선이 (0, .707, -.707)).
    # 부지 한가운데(블렌더 Y = D/2)를 보게 맞춘다 — 안 맞추면 부지가 화면 위로 쏠린다
    cam_z = 100.0
    if BIRD:                                       # 조감도 — 원근, 남동 상공에서 북서를 본다
        cam_d.type = 'PERSP'
        cam_d.lens = 45.0
        cam.location = (W / 2 + 88.0, D / 2 - 94.0, 160.0)
        tgt = bpy.data.objects.new('aim', None)
        tgt.location = (W / 2, D / 2, 71.5)
        bpy.context.collection.objects.link(tgt)
        c = cam.constraints.new('TRACK_TO')
        c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    elif TOP_VIEW:                                 # 도면과 1:1 로 견주는 평면 렌더
        cam_d.ortho_scale = 94.0
        cam.location = (W / 2, D / 2, 260.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
    else:
        cam.location = (W / 2, D / 2 - cam_z, cam_z + 72.0)
        cam.rotation_euler = (math.radians(CAM_TILT), 0.0, 0.0)
    bpy.context.scene.camera = cam

    sun_d = bpy.data.lights.new('sun', 'SUN')
    sun_d.energy = 3.0
    sun_d.angle = math.radians(3.0)          # 그림자 가장자리를 조금 부드럽게
    sun = bpy.data.objects.new('sun', sun_d)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(46), math.radians(4), math.radians(212))

    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    bgn = world.node_tree.nodes['Background']
    bgn.inputs[0].default_value = (0.58, 0.66, 0.78, 1)   # 하늘빛
    bgn.inputs[1].default_value = 1.15                    # **그늘을 열어 준다** — 낮으면 그림자가 새까맣다
    if globals().get('SKY'):
        # 내장 절차적 하늘(Nishita). HDRI 사진과 달리 메모리를 쓰지 않는다.
        # 해는 램프가 이미 있으므로 **원반은 끈다** — 켜면 빛이 두 벌이 된다.
        tex = world.node_tree.nodes.new('ShaderNodeTexSky')
        tex.sky_type = 'MULTIPLE_SCATTERING'   # 5.2 에서 NISHITA 가 이 이름으로 갈렸다
        tex.sun_disc = False
        tex.sun_elevation = math.radians(43.9)   # 램프 방향에서 계산한 값
        tex.sun_rotation = math.radians(125.8)
        tex.altitude = 30.0
        world.node_tree.links.new(tex.outputs[0], bgn.inputs[0])
        bgn.inputs[1].default_value = 1.0
    bpy.context.scene.world = world



def render(path):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = globals().get('SAMPLES', 512 if globals().get('HQ') else 200)
    # **스레드를 다 쓰지 않는다** — 다른 일(워드 등)을 하는 중에 돌리므로 여유를 남긴다
    if globals().get('THREADS'):
        sc.render.threads_mode = 'FIXED'
        sc.render.threads = THREADS
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.filepath = path
    # **AgX 는 채도·대비를 눌러 그림이 흐려 보인다.** 도면용 그림에는 Standard 가 맞다
    try:
        sc.view_settings.view_transform = 'Standard'
    except TypeError:
        sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    for attr, val in (('taa_render_samples', 128), ('use_gtao', True),
                      ('gtao_distance', 1.2), ('use_raytracing', True),
                      ('use_shadows', True), ('shadow_ray_count', 3)):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, val)
    bpy.ops.render.render(write_still=True)
    print('RENDER ->', path)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = argv[argv.index('--out') + 1] if '--out' in argv else 'r01.png'
    if '--max' in argv:                    # 최고 품질 — 크게 뽑아 줄여 쓴다(수퍼샘플링)
        globals()['RES'] = (5120, 3413)
        globals()['SAMPLES'] = 1024
    if '--threads' in argv:
        globals()['THREADS'] = int(argv[argv.index('--threads') + 1])
    if '--bird' in argv:                   # 조감도(원근). 기본은 축측도(평행투영)
        globals()['BIRD'] = True
        globals()['RES'] = (1920, 1280)
    if '--sky' in argv:                    # 내장 절차적 하늘로 비춘다
        globals()['SKY'] = True
    if '--hq' in argv:                     # 마무리용 고품질 — 4K · 512 샘플
        globals()['RES'] = (3840, 2560)
        globals()['HQ'] = True
    if '--top' in argv:
        globals()['TOP_VIEW'] = True
        globals()['RES'] = (3300, 2200) if globals().get('SAMPLES') else (1650, 1100)
    here = os.path.dirname(os.path.abspath(__file__))
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, 'axo401.blend'))
    render(os.path.join(here, out))

