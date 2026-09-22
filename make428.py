# -*- coding: utf-8 -*-
"""428 호안생태공원(생태하천변설계) — 입체평면도 모델.

성운 종합계획도의 치수를 그대로 옮긴다. **고칠 것은 아래 DIMS 한 곳만 만진다.**
좌표는 도면과 같다 — x 는 서(0)에서 동(55), y 는 북(0)에서 남(40) 으로 잰 m.
블렌더 좌표는 X=x, Y=40-y (북쪽이 +Y), Z=높이.

    blender -b -P make428.py -- --out r01.png
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
W, D = 55.0, 40.0                      # 부지 가로(동서) · 세로(남북)

RIVER   = (0.0, 8.0)                   # 하천
BANK    = (8.0, 12.72)                 # 호안 Unit1 (1:2 경사)
LEVEE   = (12.72, 18.0)                # 제방 Unit2 (+1.0 성토)
BIKE    = (18.0, 20.0)                 # 자전거도로 (투수콘)
WALK    = (20.0, 22.5)                 # 보행로 (투수콘)
PARK    = (22.5, 35.8)                 # 공원 Unit3
BUFFER  = (35.8, 38.5)                 # 보행자 완충공간 (소형고압블럭)
LOT     = (38.5, 53.3)                 # 주차장 Unit4 (아스콘)
EASTGRN = (53.3, 55.0)                 # 동측 완충녹지

Z_WATER, Z_CREST, Z_GROUND = -1.0, 1.0, 0.0
LEVEE_FLAT = (13.5, 16.0)              # 제방 마루(이 사이가 +1.0, 양옆은 경사)

# 호안 다섯 켜 (물쪽부터)
REVET_BLOCK = (8.0, 10.0)              # 호안블록 30x30, 폭 2m
REVET_PILE  = 10.3                     # 나무말뚝 1열 (1m 간격)
REVET_COIR  = (10.5, 11.1)             # 야자섬유두루마리 2열
REVET_REED  = (11.1, 12.1)             # 갈대 1m
REVET_WILL  = (12.1, 12.72)            # 갯버들

# 공원 세 공간 (y)
REST  = (0.0, 13.0)                    # 휴식공간
SCULP = (13.0, 27.0)                   # 조각공간
LAWN  = (27.0, 40.0)                   # 잔디공간

SHELTER = 4.0                          # 이동식 쉘터 4x4  (2개)
SHELTER_POS = [(25.7, 3.1), (32.6, 3.1)]      # 도면 눈금으로 다시 잼
BENCH = (1.8, 0.4)                     # 평의자 1.8 x 0.4, 6개
# **도면대로 — 한 줄이 아니다.** 좌·우 경계 안쪽에 세로로 둘씩, 가운데 아래 가로로 둘.
# (x, y, 각도) — 각도 90° 면 남북 방향
BENCH_POS = [(23.75, 8.90, 90), (23.75, 11.05, 90),   # 좌측 세로 2
             (34.85, 8.90, 90), (34.85, 11.05, 90),   # 우측 세로 2
             (26.10, 11.80, 0), (32.50, 11.80, 0)]    # 가운데 아래 가로 2
BIN_D, BIN_POS = 0.7, [(28.2, 11.7), (30.4, 11.7)]    # 휴지통 2 — 가운데에 나란히

POND_D    = 4.0                        # 원형연못 지름
RING_W    = 2.0                        # 원형동선 폭  → 바깥 지름 8.0
POND_C    = (29.15, 20.0)              # 연못 중심
CROSS_W   = 1.8                        # 십자 동선 폭 (도면 실측)
# 조각 8 — **사분면 잔디 위**. 앞서 넷이 원형동선(반지름 4m) 안에 들어가 길을 밟고 있었다.
# 아래 CHECK 가 원형동선·십자동선을 밟는 것이 있으면 렌더를 멈춘다
# 사분면마다 둘씩, **대각으로** 놓인다(도면). 나란히 둘이 아니다
SCULP_POS = [(25.7, 14.7), (24.6, 16.5), (32.5, 14.6), (33.4, 16.6),
             (24.6, 22.3), (25.7, 24.2), (33.3, 22.3), (32.4, 24.2)]

PERG_D   = 3.0                         # 원형퍼걸러 지름 (4개)
PERG_POS = [(25.9, 29.7), (33.1, 29.7), (25.9, 36.4), (33.1, 36.4)]

# 주차장
LOT_BED_W  = 1.5                       # 서쪽 화단 폭
BAY_W, BAY_L = 2.5, 5.0                # 주차 1대 (폭 x 길이)
BAY_N_Y, BAY_S_Y = 5.5, 22.5           # 북·남 주차군 시작 y (각 5대 → 12.5m)
GULLY = [(45.6, 6.5), (45.6, 34.0)]    # 빗물받이 2
CROSS_LOT = (19.0, 21.0)               # 주차장을 가로지르는 동서 통로 y
GATE_IN, GATE_OUT = (5.0, 9.0), (28.0, 33.0)   # 동쪽 경계 틈(입구·출구) y
EAST_BED = (12.0, 28.0)                # 동측 회양목 화단 y
NORTH_BED, SOUTH_BED = (0.0, 5.0), (35.0, 40.0)  # 주차장 북·남 가장자리 식재 y

# 제방 교목 15주 (한 줄)
TREE_X, TREE_N = 14.9, 15
TREE_Y0, TREE_Y1 = 1.6, 38.4
TREE_KIND = ['cone'] * 5 + ['weep'] * 5 + ['ball'] * 5   # 낙우송·왕버들·물푸레

HQ = False
TOP_VIEW = False                       # --top 이면 바로 위에서 본다
BIRD = False
CAM_TILT = 45.0                        # 평면을 뒤로 눕히는 각(깊이 0.71)
RES = (1920, 1280)

# 수목수량표의 관목·초본. (이름, 지름 m, 높이비, 잎색, 꽃색, 꽃비율)
# H·W 는 도면 규격 그대로 — 회양목 H0.6xW0.3 · 무궁화 H1.5xW0.4 · 병꽃나무 H1.2xW0.6 ·
# 개나리 H1.2x5가지 · 초본은 4치 포트
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
}

random.seed(428)

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
            z = zfun(x) if zfun else 0.0
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
            z0 = z_of(px)
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
        scatter_species(keep, species, lambda _x: z)


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
            z0 = zfun(cx)
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


def height(x):
    """서→동 지형 높이."""
    if x <= RIVER[1]:
        return Z_WATER
    if x <= LEVEE_FLAT[0]:
        t = (x - RIVER[1]) / (LEVEE_FLAT[0] - RIVER[1])
        return Z_WATER + (Z_CREST - Z_WATER) * t
    if x <= LEVEE_FLAT[1]:
        return Z_CREST
    if x <= LEVEE[1]:
        t = (x - LEVEE_FLAT[1]) / (LEVEE[1] - LEVEE_FLAT[1])
        return Z_CREST + (Z_GROUND - Z_CREST) * t
    return Z_GROUND


def terrain():
    """지형 — 높이는 x 에만 달렸다."""
    xs = sorted({0.0, RIVER[1], BANK[1], LEVEE_FLAT[0], LEVEE_FLAT[1], LEVEE[1], W})
    xs = sorted(set(xs + [RIVER[1] + i * 0.4 for i in range(1, 12)]))
    me = bpy.data.meshes.new('terrain')
    bmv = bmesh.new()
    rows = []
    for x in xs:
        # **지형을 포장 판보다 6cm 내린다.** 같은 높이에 두면 Cycles 에서 두 면이
        # 겹쳐 새까맣게 나온다(EEVEE 는 그냥 덮어 가려 못 알아챘다)
        z = height(x) - 0.06
        bx0, by0 = bl(x, 0.0)
        bx1, by1 = bl(x, D)
        rows.append((bmv.verts.new((bx0, by0, z)), bmv.verts.new((bx1, by1, z))))
    for a, b in zip(rows, rows[1:]):
        bmv.faces.new([a[0], a[1], b[1], b[0]])
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new('terrain', me)
    bpy.context.collection.objects.link(o)
    return put(o, mat('soil', (0.26, 0.21, 0.14), spread=0.30, scale=90, bump=0.6))


def tree(x, y, kind):
    """교목 한 주. **수관은 공 하나가 아니라 작은 덩이 여럿**을 겹쳐 만든다 —
    매끈한 공은 사탕처럼 보이고, 그것이 '만화 같다'의 가장 큰 원인이다."""
    z = height(x)
    bx, by = bl(x, y)
    bark = mat('bark', (0.19, 0.14, 0.10), rough=0.9, spread=0.25, scale=200, bump=0.9)
    leaf = mat('canopy', (0.09, 0.20, 0.07), rough=0.95, spread=0.30, scale=90, bump=1.0)
    ht = {'cone': 3.0, 'weep': 2.7, 'ball': 2.7}[kind]
    cyl(x, y, z, 0.30, ht, bark, verts=12)
    me = bpy.data.meshes.new('crown')
    bmv = bmesh.new()
    if kind == 'cone':                      # 낙우송 — 좁고 높은 원추
        lobes, rad, top, spread_r = 10, 0.74, 3.4, 0.68
    elif kind == 'weep':                    # 왕버들 — 넓고 처지는 덩이
        lobes, rad, top, spread_r = 12, 0.80, 1.7, 0.72
    else:                                   # 물푸레나무 — 둥근
        lobes, rad, top, spread_r = 11, 0.78, 1.8, 0.70
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


def shelter(cx, cy):
    """이동식 쉘터 4x4 — 기둥 넷 + 낮은 모임지붕."""
    z = Z_GROUND
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


def pergola(cx, cy):
    """원형퍼걸러 지름 3 — 기둥 여섯 + **방사형 살대 지붕**(통판이면 탁자로 보인다)."""
    z = Z_GROUND
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


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    m_water = mat('water', (0.05, 0.16, 0.24), rough=0.04, spread=0.06, scale=3, bump=0.06)
    m_grass = mat('grass', (0.20, 0.38, 0.11), spread=0.28, scale=480, bump=1.3)
    m_lawn  = mat('lawn',  (0.26, 0.46, 0.13), spread=0.26, scale=520, bump=1.4)
    m_bike  = mat('bike',  (0.48, 0.22, 0.16), spread=0.20, scale=200, bump=0.35)
    m_walk  = mat('walk',  (0.72, 0.68, 0.58), spread=0.16, scale=220, bump=0.40)
    m_pave  = brick_mat('pave',  (0.76, 0.73, 0.64), (0.72, 0.69, 0.60), (0.58, 0.55, 0.48), scale=7.0)
    m_block = brick_mat('block', (0.60, 0.59, 0.56), (0.55, 0.54, 0.51), (0.40, 0.39, 0.37), scale=11.0)
    m_asph  = mat('asph',  (0.10, 0.10, 0.11), spread=0.35, scale=260, bump=0.45)
    m_kerb  = mat('kerb',  (0.60, 0.59, 0.56), spread=0.06, scale=220, bump=0.12)
    m_shrub = mat('shrub', (0.10, 0.22, 0.08), spread=0.22, scale=110, bump=0.9)
    m_flower= mat('flower',(0.35, 0.44, 0.17), spread=0.45, scale=70, bump=0.6)
    m_reed  = mat('reed',  (0.52, 0.55, 0.24), spread=0.30, scale=140, bump=0.5)
    m_will  = mat('will',  (0.24, 0.36, 0.14), spread=0.28, scale=140, bump=0.6)
    m_line  = mat('line',  (0.86, 0.86, 0.84), spread=0.05, scale=300, bump=0.10)
    m_stone = mat('stone', (0.58, 0.57, 0.54), spread=0.07, scale=400, bump=0.20)

    terrain()

    # ── 하천
    slab(*RIVER, 0.0, D, Z_WATER, m_water, h=0.25)

    # ── 호안 다섯 켜 (경사면 위)
    for i in range(int((REVET_BLOCK[1] - REVET_BLOCK[0]) / 0.6) + 1):      # 호안블록
        x = REVET_BLOCK[0] + i * 0.6
        for j in range(int(D / 0.6)):
            box(x, j * 0.6 + 0.3, height(x), 0.52, 0.52, 0.12, m_stone)
    for j in range(int(D)):                                                # 나무말뚝 1열
        cyl(REVET_PILE, j + 0.5, height(REVET_PILE) - 0.1, 0.12, 0.7,
            mat('pile', (0.42, 0.30, 0.18)), verts=10)
    for x in (REVET_COIR[0] + 0.15, REVET_COIR[1] - 0.15):                 # 야자섬유 2열
        bx, by = bl(x, D / 2)
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.17, depth=D,
                                            location=(bx, by, height(x) + 0.15),
                                            rotation=(math.radians(90), 0, 0))
        # **눕혀야 한다.** 블렌더 원통은 Z 축이 기본이라 회전을 빼면 40m 짜리 기둥이
        # 강 위로 솟는다. 위에서 내려다보는 평면·축측도에서는 점으로만 보여 못 보다가
        # 원근 조감도에서 드러났다
        put(bpy.context.object, mat('coir', (0.52, 0.40, 0.22)))
    stalk_band(*REVET_REED, 0.0, D, m_reed, height, gap=0.50, per=6,
               h=(0.9, 1.4), rad=0.026, splay=0.16)          # 갈대 — 가늘고 높게
    stalk_band(*REVET_WILL, 0.0, D, m_will, height, gap=0.46, per=5,
               h=(0.5, 0.8), rad=0.042, splay=0.40, tip=0.10)  # 갯버들 — 낮고 퍼진 가지

    # ── 제방 — 잔디 + 교목 15주 한 줄 + 초화 띠
    for i in range(TREE_N):
        y = TREE_Y0 + (TREE_Y1 - TREE_Y0) * i / (TREE_N - 1)
        tree(TREE_X, y, TREE_KIND[i])
    blob_band(12.95, 14.0, 0.0, D, 0.30, 0.42, m_flower, zfun=height)
    blob_band(16.0, 17.8, 0.0, D, 0.30, 0.42, m_flower, zfun=height)

    # ── 자전거도로 · 연석 · 보행로
    slab(*BIKE, 0.0, D, Z_GROUND, m_bike)
    slab(BIKE[1] - 0.12, BIKE[1] + 0.12, 0.0, D, Z_GROUND + 0.12, m_kerb, h=0.24)
    slab(*WALK, 0.0, D, Z_GROUND, m_walk)

    # ── 공원 Unit 3
    slab(*PARK, *REST, Z_GROUND, m_pave)                     # 휴식공간 투수콘
    slab(*PARK, *SCULP, Z_GROUND, m_lawn)                    # 조각공간 잔디
    slab(*PARK, *LAWN, Z_GROUND, m_lawn)                     # 잔디공간
    for cx, cy in SHELTER_POS:
        shelter(cx, cy)
    m_bwood = mat('bwood', (0.34, 0.21, 0.12), rough=0.8, spread=0.20, scale=150, bump=0.5)
    for bx_, by_, rot_ in BENCH_POS:
        rr = math.radians(rot_)
        box(bx_, by_, Z_GROUND + 0.36, BENCH[0], BENCH[1], 0.07, m_bwood, rot=rr)  # 좌판
        for dd in (-BENCH[0] / 2 + 0.2, BENCH[0] / 2 - 0.2):
            ddx = dd * math.cos(rr)
            ddy = -dd * math.sin(rr)
            box(bx_ + ddx, by_ + ddy, Z_GROUND, 0.10, 0.10, 0.36, m_bwood)
    for cx, cy in BIN_POS:
        cyl(cx, cy, Z_GROUND, BIN_D, 0.8, mat('bin', (0.35, 0.33, 0.30)))
    # 조각공간 — 십자 동선 + 원형동선 + 연못
    ring(*POND_C, Z_GROUND + 0.04, POND_D, POND_D + 2 * RING_W, m_pave)
    cx_, cy_ = POND_C
    ZP = Z_GROUND + 0.035                     # 잔디·화단 위에 얹는 포장 — 같은 높이면 검게 나온다
    slab(cx_ - CROSS_W / 2, cx_ + CROSS_W / 2, SCULP[0], cy_ - POND_D / 2 - RING_W, ZP, m_pave)
    slab(cx_ - CROSS_W / 2, cx_ + CROSS_W / 2, cy_ + POND_D / 2 + RING_W, SCULP[1], ZP, m_pave)
    slab(PARK[0], cx_ - POND_D / 2 - RING_W, cy_ - CROSS_W / 2, cy_ + CROSS_W / 2, ZP, m_pave)
    slab(cx_ + POND_D / 2 + RING_W, PARK[1], cy_ - CROSS_W / 2, cy_ + CROSS_W / 2, ZP, m_pave)
    cyl(cx_, cy_, Z_GROUND - 0.35, POND_D, 0.36, m_water)    # 연못 — 물만
    r_ring = POND_D / 2 + RING_W + 0.25                 # 원형동선 바깥 + 여유
    for sx, sy in SCULP_POS:                            # 길을 밟으면 멈춘다
        d_ = math.hypot(sx - POND_C[0], sy - POND_C[1])
        on_cross = (abs(sx - POND_C[0]) < CROSS_W / 2 + 0.25) or                    (abs(sy - POND_C[1]) < CROSS_W / 2 + 0.25)
        assert d_ > r_ring and not on_cross,             '조각 (%.1f, %.1f) 이 길 위에 있다 — 잔디로 옮겨라 (중심거리 %.2f)' % (sx, sy, d_)
    for i, (sx, sy) in enumerate(SCULP_POS):
        h_ = random.uniform(0.9, 1.5)
        if i % 3 == 0:
            box(sx, sy, Z_GROUND, 0.30, 0.30, 0.18, m_stone)          # 좌대
            box(sx, sy, Z_GROUND + 0.18, 0.55, 0.55, h_, m_stone,
                rot=math.radians(random.uniform(0, 60)))
        elif i % 3 == 1:
            box(sx, sy, Z_GROUND, 0.30, 0.30, 0.18, m_stone)
            cyl(sx, sy, Z_GROUND + 0.18, 0.62, h_, m_stone, verts=20)
        else:
            box(sx, sy, Z_GROUND, 0.30, 0.30, 0.18, m_stone)
            bx_, by_ = bl(sx, sy)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=h_ * 0.34,
                                                  location=(bx_, by_, Z_GROUND + 0.18 + h_ * 0.34))
            put(bpy.context.object, m_stone)
    for cx, cy in PERG_POS:
        pergola(cx, cy)
    # 공간 경계식재 — **십자 동선이 지나는 자리는 비운다**
    mg = 0.5
    r_in = POND_D / 2 + RING_W
    paths = [
        (cx_ - CROSS_W / 2 - mg, cx_ + CROSS_W / 2 + mg, SCULP[0] - mg, cy_ - r_in + mg),
        (cx_ - CROSS_W / 2 - mg, cx_ + CROSS_W / 2 + mg, cy_ + r_in - mg, SCULP[1] + mg),
        (PARK[0] - mg, cx_ - r_in + mg, cy_ - CROSS_W / 2 - mg, cy_ + CROSS_W / 2 + mg),
        (cx_ + r_in - mg, PARK[1] + mg, cy_ - CROSS_W / 2 - mg, cy_ + CROSS_W / 2 + mg),
    ]
    # 공간 경계식재 + **공원 네 변을 두르는 완충식재**(도면 — 위아래 띠를 빠뜨렸었다)
    for y in (REST[1], SCULP[1]):              # 남북 동선이 지나는 자리에서 끊는다
        for a, b in ((PARK[0] + 0.2, cx_ - CROSS_W / 2 - 0.45),
                     (cx_ + CROSS_W / 2 + 0.45, PARK[1] - 0.2)):
            bed_shape([(a, y - 0.55), (b, y - 0.55), (b, y + 0.55), (a, y + 0.55)],
                      0.0, m_grass, m_kerb, ['회양목'], gap=0.40, shrub_inset=0.14)
    EW, NS = 1.0, 1.0                          # 좌·우 / 위·아래 경계식재 띠 폭(도면 실측)
    gx0, gx1 = cx_ - CROSS_W / 2 - 0.45, cx_ + CROSS_W / 2 + 0.45   # 남북 동선이 지나는 자리
    gy0, gy1 = cy_ - CROSS_W / 2 - 0.45, cy_ + CROSS_W / 2 + 0.45   # 동서 동선이 지나는 자리
    SPP = ['회양목']                           # 도면의 사선 해치 = 경계식재 = 회양목
    # **좌·우 경계식재는 한 줄이 아니라 토막이다**(도면 — 토막 사이로 잔디가 경계선까지 나온다).
    # 토막 2.0m · 사이 1.4m 로 되풀이하고, 동서 동선이 지나는 자리는 건너뛴다
    SEG, GAPY = 2.0, 1.4
    yy = 0.0
    while yy < D - 0.4:
        y2 = min(yy + SEG, D)
        if not (y2 > gy0 and yy < gy1):        # 동선 자리는 비운다
            for x_a, x_b in ((PARK[0], PARK[0] + EW), (PARK[1] - EW, PARK[1])):
                bed_shape([(x_a, yy), (x_b, yy), (x_b, y2), (x_a, y2)],
                          0.25, m_grass, m_kerb, SPP, gap=0.40, shrub_inset=0.14)
        yy = y2 + GAPY
    for a, b in ((PARK[0] + EW, PARK[1] - EW),):   # 위·아래 띠
        bed_shape([(a, 0.0), (b, 0.0), (b, NS), (a, NS)],
                  0.0, m_grass, m_kerb, SPP, gap=0.40, shrub_inset=0.14)
        bed_shape([(a, D - NS), (b, D - NS), (b, D), (a, D)],
                  0.0, m_grass, m_kerb, SPP, gap=0.40, shrub_inset=0.14)

    # ── 보행자 완충공간
    slab(*BUFFER, 0.0, D, Z_GROUND, m_block)

    # ── 주차장
    slab(*LOT, 0.0, D, Z_GROUND, m_asph)
    slab(LOT[1], W, 0.0, D, Z_GROUND, m_asph)         # 동측 띠 — 맨흙이 드러나지 않게 먼저 깐다
    # 서쪽 화단 두 도막 — 도면에서는 북·남 가장자리 식재와 **ㄱ자로 이어지고 모서리가 둥글다**
    bed_shape([(39.5, 0.0), (46.5, 0.0), (46.5, 4.4), (40.9, 4.4), (40.9, 17.6), (39.5, 17.6)],
              1.0, m_grass, m_kerb, ['민들레', '병꽃나무', '무궁화'], gap=0.62)   # 북서 ㄱ자
    bed_shape([(39.5, 40.0), (46.5, 40.0), (46.5, 35.6), (40.9, 35.6), (40.9, 22.4), (39.5, 22.4)],
              1.0, m_grass, m_kerb, ['민들레', '병꽃나무', '유채꽃'], gap=0.62)   # 남서 ㄱ자
    bx0 = LOT[0] + LOT_BED_W                                   # 주차면 서쪽 끝
    for grp in (BAY_N_Y, BAY_S_Y):
        for i in range(6):                                     # 구획선 6줄 = 5대
            slab(bx0, bx0 + BAY_L, grp + i * BAY_W - 0.06, grp + i * BAY_W + 0.06,
                 Z_GROUND + 0.01, m_line, h=0.02)
        slab(bx0 + BAY_L - 0.06, bx0 + BAY_L + 0.06, grp, grp + 5 * BAY_W,
             Z_GROUND + 0.01, m_line, h=0.02)
    slab(*LOT, *CROSS_LOT, Z_GROUND + 0.005, m_block)          # 동서 통로
    for gx, gy in GULLY:
        box(gx, gy, Z_GROUND, 0.6, 0.6, 0.06, mat('gully', (0.25, 0.25, 0.26)))
    # 동측 식재 세 덩이 — 북 · 가운데 회양목 · 남 (틈 둘이 입구·출구)
    # **회양목 띠는 동측 경계(x=55)에 붙어야 한다.** 안쪽에 띄워 놓으면 경계 쪽에
    # 아무것도 없는 아스팔트 띠가 남아 어색하다. 도면을 재면 52.9~55.0 · y 12.7~28.1
    # 이고, 그 위(y 2.8~12.7)가 차량입구, 아래(y 28.1~37.2)가 차량출구로 도로에 붙는다
    # 끝이 둥근 타원 화단 셋 — 북동 초화 · 남동 초화 · 동측 회양목
    for pts_ in (
            [(46.2, 0.0), (55.0, 0.0), (55.0, 2.8), (46.2, 2.8)],       # 북동
            [(46.2, 37.2), (55.0, 37.2), (55.0, 40.0), (46.2, 40.0)],   # 남동
            [(53.0, 12.7), (55.0, 12.7), (55.0, 28.1), (53.0, 28.1)]):  # 동측 회양목 — **경계에 붙인다**
        bed_shape(pts_, 0.95, m_grass, m_kerb,
                  ['회양목'] if pts_[0][0] > 50 and pts_[0][1] > 5 else ['유채꽃', '민들레', '쑥부쟁이'],
                  gap=0.55, shrub_inset=0.24)

    # ── 카메라 · 빛
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = 62.0
    cam_d.clip_end = 400
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.collection.objects.link(cam)
    # 45° 로 눕힌 직교 카메라는 **cam_y + cam_z 자리를 겨냥한다**(시선이 (0, .707, -.707)).
    # 부지 한가운데(블렌더 Y = D/2)를 보게 맞춘다 — 안 맞추면 부지가 화면 위로 쏠린다
    cam_z = 60.0
    if BIRD:                                       # 조감도 — 원근, 남동 상공에서 북서를 본다
        cam_d.type = 'PERSP'
        cam_d.lens = 45.0
        cam.location = (W / 2 + 54.0, D / 2 - 58.0, 54.0)
        tgt = bpy.data.objects.new('aim', None)
        tgt.location = (W / 2 + 1.0, D / 2, 0.0)
        bpy.context.collection.objects.link(tgt)
        c = cam.constraints.new('TRACK_TO')
        c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    elif TOP_VIEW:                                 # 도면과 1:1 로 견주는 평면 렌더
        cam_d.ortho_scale = 56.0
        cam.location = (W / 2, D / 2, 90.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
    else:
        cam.location = (W / 2, D / 2 - cam_z, cam_z)
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
        globals()['RES'] = (3200, 2328) if globals().get('SAMPLES') else (1600, 1164)
    here = os.path.dirname(os.path.abspath(__file__))
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, 'axo428.blend'))
    render(os.path.join(here, out))
