# -*- coding: utf-8 -*-
"""444 주차공원 — 입체 모형(축측도 · 평면 · 조감도).

좌표는 **사용자가 CAD 탭에 그린 '주차공원 444' 시설배치도(서버 CadDrawing pk=3)에서 그대로
가져온다.** 도면을 눈으로 다시 읽지 않는다 — 점 좌표가 m 단위로 이미 있다.
x 는 서(-5)에서 동(145), y 는 북(0)에서 남(107) 으로 잰 m (부지 150 × 107, 남동 모서리 45° 모따기).
블렌더 좌표는 X=x, Y=107-y (북쪽이 +Y), Z=높이(평탄한 부지라 0).
식재는 성운 배식평면도(답안지 III) 수목수량표의 수종·수량을 자리별로 나눠 넣었다.
주변은 문제지 현황도 — 북측 주거지, 서측 상업지, 동측 6m 보도 + 35m 광로, 남측 6m 보도 + 차도,
남동 모서리 보도의 지하철 출입구.

    blender -b -P make444.py -- --out r01.png [--top|--bird] [--max] [--samples N] [--threads N]
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

# ─────────────────────────────────────────────────────────────────
# 치수 (m) — CAD 도면(주차공원 444)의 점 좌표. 고칠 것은 여기만
# ─────────────────────────────────────────────────────────────────
D = 107.0
Z_GROUND = 0.0
Z_ASPH = 0.02                           # 주차장 · 통로 아스팔트 윗면
Z_PAVE = 0.14                           # 보도 · 광장 윗면(연석 높이만큼)

# 주변 — 현황도: 동측 보도 6m + 광로, 남측 보도 6m + 차도, 남동 모서리 보도가 넓어 지하철 출입구가 놓인다
SIDEWALK = [(-60, 107), (110, 107), (145, 72), (145, -45), (151, -45), (151, 89), (127, 113), (-60, 113)]
ROAD = [(151, -45), (200, -45), (200, 150), (-60, 150), (-60, 113), (127, 113), (151, 89)]

# 부지 안 포장
ASPHALT = [(15, 17), (145, 17), (145, 27), (139, 27), (139, 68.5), (107, 68.5), (107, 101), (25, 101),
           (25, 107), (15, 107), (15, 101), (10, 101), (10, 31), (15, 31)]
REST_NW = [(-5, 3), (29, 3), (29, 12), (15, 12), (15, 27), (-5, 27)]      # 북서 휴게공간(화강석판석)
TOILET_PAD = [(34, 6), (46, 6), (46, 12), (34, 12)]
N_WALK = [(15, 12), (145, 12), (145, 17), (15, 17)]                        # 북측 보행로(소형고압블럭)
W_WALK = [(7, 27), (10, 27), (10, 107), (7, 107)]                          # 서측 보행로(투수콘)
SE_PLAZA = [(107, 72), (145, 72), (110, 107), (107, 107)]                  # 남동 휴게공간(화강석판석)
KERBS = [
    [(15, 17), (145, 17)], [(29, 12), (34, 12)], [(46, 12), (145, 12)],
    [(-5, 3), (29, 3), (29, 12)], [(34, 12), (34, 6), (46, 6), (46, 12)], [(-5, 27), (7, 27)],
    [(7, 27), (7, 107)], [(10, 31), (10, 101)], [(10, 27), (15, 27), (15, 31), (10, 31)],
    [(10, 101), (15, 101), (15, 107)], [(25, 107), (25, 101), (107, 101), (107, 72), (145, 72)],
    [(139, 27), (139, 68.5), (111, 68.5)], [(145, 27), (139, 27)],
]

# 주차 칸 — (x0, x1, 통로쪽 y, 안쪽 y). 한 칸 2.5 × 5
STALL_ROWS = [(29, 129, 27, 32), (29, 129, 39, 34), (29, 129, 45, 50), (29, 129, 57, 52),
              (29, 94, 63, 68), (29, 94, 75, 70), (29, 94, 82, 87), (29, 94, 94, 89)]
MEDIANS = [(29, 129, 32, 34), (29, 129, 50, 52), (29, 94, 68, 70), (29, 94, 87, 89)]   # 가운데 녹지 2m
ISLANDS = [(25, 29, 27, 39), (129, 133, 27, 39), (25, 29, 45, 57), (129, 133, 45, 57),
           (25, 29, 63, 75), (94, 98, 63, 75), (25, 29, 82, 94), (94, 98, 82, 94)]     # 양 끝 둥근 화단(R0.8)
TRIANGLE = [(114, 79), (127.5, 79), (114, 92.5)]                         # 남동 삼각 화단

# 건물 · 시설물 — CAD 기호 자리 그대로
TOILET = (35, 45, 7, 12)
KIOSKS = [(139.1, 143.1, 27.1, 31.1), (25, 29, 103, 107)]                # 주차관리소 4 × 4
PERGOLA = (20, 28, 4, 8)
GRATES = [(0, 10), (5, 10), (10, 10), (15, 10), (0, 15), (5, 15), (10, 15), (0, 20), (5, 20), (10, 20)]
BENCHES = [(111, 73, 0), (114.5, 73, 0), (118, 73, 0), (127, 73, 0), (130.5, 73, 0), (135.2, 72.7, 0),
           (115, 78.2, 0), (120, 78.2, 0), (125, 78.2, 0),
           (113.25, 81.9, 90), (113.25, 86.1, 90), (113.25, 90.5, 90)]
BINS = [(122, 73), (13, 4)]
FOUNTAINS = [(124.5, 73), (16, 4)]
LAMPS = [(31.5, 10), (60, 10), (75, 10), (90, 10), (105, 10), (120, 10), (135, 10),
         (5, 35), (5, 50), (5, 65), (5, 80), (5, 95), (110, 70), (125, 70), (139, 70)]
BOLLARDS = [(13.5, 20), (13.5, 24), (17.5, 15.5), (22.5, 15.5),
            (108.5, 77.5), (108.5, 82.5), (108.5, 87.5), (108.5, 92.5), (108.5, 98)]

# 관목 — (지름, 높이/지름, 잎색, 꽃색, 꽃 비율)
SPECIES = {
    '회양목':   (0.50, 1.00, (0.06, 0.18, 0.06), None,               0.0),    # H0.5 × W0.5
    '사철나무': (0.55, 2.60, (0.07, 0.21, 0.08), None,               0.0),    # H1.5 × W0.5
    '수수꽃다리': (1.40, 1.60, (0.15, 0.30, 0.11), (0.70, 0.58, 0.82), 0.35),  # H2.5 × W1.5
    '진달래':   (0.50, 1.20, (0.16, 0.30, 0.12), (0.86, 0.55, 0.70), 0.50),   # H0.6 × W0.5
    '산철쭉':   (0.60, 0.85, (0.14, 0.28, 0.11), (0.82, 0.36, 0.58), 0.55),   # H0.5 × W0.6
}
# 교목 — (꼴, 크기배율, 잎색). 성운 수목수량표 15종
TREE_SPEC = {
    '스트로브잣나무': ('cone', 1.25, (0.09, 0.21, 0.15)),   # H3.5 × W1.8 상록
    '향나무':        ('cone', 0.90, (0.10, 0.23, 0.12)),   # H3.5 × W1.2 상록
    '편백':          ('cone', 1.15, (0.08, 0.22, 0.10)),   # H3.5 × W1.2 상록
    '측백':          ('cone', 1.00, (0.13, 0.25, 0.10)),   # H3.0 × W1.2 상록
    '느티나무':      ('ball', 1.55, (0.16, 0.32, 0.11)),   # H4.0 × R15
    '은행나무':      ('cone', 1.20, (0.33, 0.42, 0.11)),   # H4.0 × B6
    '왕벚나무':      ('ball', 1.35, (0.20, 0.34, 0.13)),   # H3.5 × B8
    '이팝나무':      ('ball', 1.30, (0.19, 0.35, 0.12)),   # H3.5 × R12
    '회화나무':      ('ball', 1.25, (0.20, 0.36, 0.12)),   # H3.5 × R8
    '칠엽수':        ('ball', 1.35, (0.12, 0.28, 0.09)),   # H3.5 × R12
    '중국단풍':      ('ball', 1.20, (0.22, 0.36, 0.12)),   # H3.5 × R12
    '산딸나무':      ('ball', 1.10, (0.17, 0.31, 0.12)),   # H3.0 × R8
    '산사나무':      ('ball', 1.00, (0.18, 0.32, 0.12)),   # H3.0 × R6
    '꽃사과나무':    ('ball', 1.05, (0.20, 0.33, 0.13)),   # H3.0 × R8
    '팥배나무':      ('ball', 1.05, (0.19, 0.33, 0.12)),   # H3.0 × R6
    '수수꽃다리_교': ('ball', 0.62, (0.15, 0.30, 0.11)),   # 큰 관목 H2.5 — 덩이 하나로
}


def plant(x, y, name, k=1.0):
    kind, sc, rgb = TREE_SPEC[name]
    tree(x, y, kind, scale=sc * k, leaf_rgb=rgb, name=name)


random.seed(444)
TOP_VIEW = False
BIRD = False
CAM_TILT = 45.0
RES = (1920, 1280)


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


def brick_mat(name, c1, c2, mortar, scale=9.0, msize=0.028, rough=0.8, bw=0.5, rh=0.25):
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
    t.inputs['Brick Width'].default_value = bw
    t.inputs['Row Height'].default_value = rh
    # **물체 좌표(m)로 깐다** — 기본(생성 좌표)은 판 크기에 비례해 늘어나 큰 보도의 벽돌이 몇 m 가 됐다
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], t.inputs['Vector'])
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


def bench(cx, cy, deg, z, wood, leg):
    """평의자 1.8 x 0.4."""
    a = -math.radians(deg)
    box(cx, cy, z + 0.40, 1.8, 0.42, 0.08, wood, rot=a)
    for d in (-0.7, 0.7):
        px = cx + d * math.cos(-a)
        py = cy + d * math.sin(-a)
        box(px, py, z, 0.09, 0.36, 0.40, leg, rot=a)


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


# ─────────────────────────────────────────────────────────────────
# 444 전용
# ─────────────────────────────────────────────────────────────────
def height(x, y):
    return 0.0                                   # 평탄한 부지


def poly_slab(pts, z, m, h=0.04, name='poly'):
    """다각형 판 — 윗면이 z. ngon 하나로 두고 삼각분할에 맡긴다."""
    me = bpy.data.meshes.new(name)
    bmv = bmesh.new()
    top = [bmv.verts.new((*bl(x, y), z)) for x, y in pts]
    bot = [bmv.verts.new((*bl(x, y), z - h)) for x, y in pts]
    bmv.faces.new(top)
    bmesh.ops.triangulate(bmv, faces=bmv.faces[:])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        try:
            bmv.faces.new([top[i], top[j], bot[j], bot[i]])
        except ValueError:
            pass
    _face_up(bmv)
    bmv.to_mesh(me)
    bmv.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def rrect(x0, x1, y0, y1, r):
    """둥근 모서리 사각형 윤곽 — 주차열 끝 화단(반지름 0.8m)."""
    return round_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], r, seg=6)


def kerb_line(pts, m, w=0.18, h=0.14, closed=False):
    """경계석 — 폴리라인을 따라 도톰한 띠(단면 w × h)."""
    cu = bpy.data.curves.new('kerbl', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = w / 2
    cu.bevel_resolution = 1
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        bx, by = bl(x, y)
        sp.points[i].co = (bx, by, h * 0.45, 1.0)
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new('kerbl', cu)
    o.scale = (1, 1, 1)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def paint_line(x0, y0, x1, y1, m, w=0.12, z=Z_ASPH + 0.004):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    a = math.atan2(-(y1 - y0), x1 - x0)          # 블렌더 좌표는 y 가 뒤집힌다
    box(cx, cy, z - 0.002, L, w, 0.004, m, rot=a)


def car(cx, cy, along_y, m_body, m_glass, m_tire):
    """승용차 — 차체 + 유리 캐빈 + 바퀴. 길이 4.6 · 폭 1.8."""
    rot = math.pi / 2 if along_y else 0.0
    box(cx, cy, 0.30, 4.5, 1.78, 0.62, m_body, rot=rot)
    ox, oy = (0.0, 0.25) if along_y else (-0.25, 0.0)
    box(cx + ox, cy + oy, 0.90, 2.5, 1.60, 0.52, m_glass, rot=rot)
    box(cx + ox, cy + oy, 1.40, 2.3, 1.52, 0.06, m_body, rot=rot)
    for sx in (-1.45, 1.45):
        for sy in (-0.82, 0.82):
            dx, dy = (sy, sx) if along_y else (sx, sy)
            bx, by = bl(cx + dx, cy + dy)
            bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.33, depth=0.24,
                                                location=(bx, by, 0.33),
                                                rotation=(0, math.pi / 2, 0) if along_y else (math.pi / 2, 0, 0))
            put(bpy.context.object, m_tire)


def small_house(cx, cy, sx, sy, h, m_wall, m_roof, pitch=True):
    box(cx, cy, 0.0, sx, sy, h, m_wall)
    if pitch:
        bx, by = bl(cx, cy)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(sx, sy) * 0.74, radius2=0.0,
                                        depth=min(sx, sy) * 0.45, location=(bx, by, h + min(sx, sy) * 0.22),
                                        rotation=(0, 0, math.radians(45)))
        o = bpy.context.object
        o.scale = (sx / max(sx, sy), sy / max(sx, sy), 1.0)
        put(o, m_roof)
    else:
        box(cx, cy, h, sx + 0.3, sy + 0.3, 0.25, m_roof)


def hip_roof(x0, x1, y0, y1, z, rise, m, over=0.4):
    """모임지붕 — 처마 네 모서리 + 긴 변을 따라 가는 용마루(도면의 X 자 지붕선 그대로)."""
    x0, x1, y0, y1 = x0 - over, x1 + over, y0 - over, y1 + over
    sx, sy = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if sx >= sy:
        h = (sx - sy) / 2
        r0, r1 = (cx - h, cy), (cx + h, cy)
    else:
        h = (sy - sx) / 2
        r0, r1 = (cx, cy - h), (cx, cy + h)
    me = bpy.data.meshes.new('roof')
    bmv = bmesh.new()
    c0 = bmv.verts.new((*bl(x0, y0), z)); c1 = bmv.verts.new((*bl(x1, y0), z))
    c2 = bmv.verts.new((*bl(x1, y1), z)); c3 = bmv.verts.new((*bl(x0, y1), z))
    ra = bmv.verts.new((*bl(*r0), z + rise)); rb = bmv.verts.new((*bl(*r1), z + rise))
    if sx >= sy:
        faces = [(c0, c1, rb, ra), (c1, c2, rb), (c2, c3, ra, rb), (c3, c0, ra)]
    else:
        faces = [(c0, c1, ra), (c1, c2, rb, ra), (c2, c3, rb), (c3, c0, ra, rb)]
    for f in faces:
        bmv.faces.new(f)
    bmv.faces.new((c3, c2, c1, c0))
    bmv.normal_update()
    bmv.to_mesh(me); bmv.free()
    o = bpy.data.objects.new('roof', me)
    bpy.context.collection.objects.link(o)
    return put(o, m)


def small_house(cx, cy, sx, sy, h, m_wall, m_roof, pitch=True):
    box(cx, cy, 0.0, sx, sy, h, m_wall)
    hip_roof(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, h, min(sx, sy) * 0.32, m_roof, over=0.5)


def hip_building(x0, x1, y0, y1, h, m_wall, m_roof, m_door=None):
    """화장실 · 주차관리소 — 벽 + 모임지붕."""
    cx, cy, sx, sy = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    box(cx, cy, 0.03, sx, sy, h, m_wall)
    hip_roof(x0, x1, y0, y1, 0.03 + h, 0.6 + min(sx, sy) * 0.18, m_roof)
    if m_door:
        box(cx, y1 + 0.02, 0.03, min(1.2, sx * 0.3), 0.06, 2.1, m_door)


def pergola_rect(x0, x1, y0, y1, z, wood):
    """퍼걸러 8 × 4 — 기둥 + 테두리 보 + 촘촘한 판재(그늘이 져야 퍼걸러로 읽힌다)."""
    cx, cy, sx, sy = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    for px in (x0 + 0.3, cx, x1 - 0.3):
        for py in (y0 + 0.3, y1 - 0.3):
            box(px, py, z, 0.2, 0.2, 2.5, wood)
    for py in (y0 + 0.3, y1 - 0.3):
        box(cx, py, z + 2.5, sx + 0.4, 0.18, 0.22, wood)
    n = int(sx / 0.32)
    for i in range(n + 1):
        box(x0 + i * sx / n, cy, z + 2.72, 0.09, sy + 0.5, 0.12, wood)


def grate(cx, cy, z, s, m_grate, m_soil):
    """수목보호대 s × s (도면 1.6m 사각)."""
    t = 0.18
    for (bx, by, bw, bh) in ((cx, cy - s / 2 + t / 2, s, t), (cx, cy + s / 2 - t / 2, s, t),
                             (cx - s / 2 + t / 2, cy, t, s), (cx + s / 2 - t / 2, cy, t, s)):
        box(bx, by, z - 0.02, bw, bh, 0.06, m_grate)
    slab(cx - s / 2 + t, cx + s / 2 - t, cy - s / 2 + t, cy + s / 2 - t, z + 0.005, m_soil, h=0.03)


def lamp(cx, cy, pole, head):
    """정원등 H4.5 — 가는 기둥 + 둥근 갓."""
    cyl(cx, cy, 0.0, 0.14, 4.3, pole, verts=10)
    cyl(cx, cy, 4.3, 0.55, 0.22, head, verts=16)


def bollard(cx, cy, m):
    cyl(cx, cy, 0.03, 0.30, 0.85, m, verts=14)


def spots_line(x0, y0, x1, y1, n):
    return [(x0 + (x1 - x0) * i / max(n - 1, 1), y0 + (y1 - y0) * i / max(n - 1, 1)) for i in range(n)]


def shrub_area(x0, x1, y0, y1, names, gap=0.62, z=0.0, avoid=()):
    pts = []
    for _ in range(int((x1 - x0) * (y1 - y0) / (gap * gap))):
        x, y = random.uniform(x0, x1), random.uniform(y0, y1)
        if any(a0 <= x <= a1 and b0 <= y <= b1 for a0, a1, b0, b1 in avoid):
            continue
        pts.append((x, y))
    scatter_species(pts, names, lambda _x, _y=None: z)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    m_lawn  = mat('lawn',  (0.27, 0.46, 0.13), spread=0.26, scale=520, bump=1.4)
    m_asph  = mat('asph',  (0.12, 0.12, 0.13), rough=0.9, spread=0.22, scale=260, bump=0.6)
    m_road  = mat('road',  (0.10, 0.10, 0.11), rough=0.9, spread=0.18, scale=240, bump=0.5)
    m_paint = mat('paint', (0.92, 0.92, 0.88), rough=0.6)
    m_yellow = mat('yellow', (0.90, 0.72, 0.12), rough=0.6)
    m_blue  = mat('hcblue', (0.13, 0.33, 0.66), rough=0.6, spread=0.06, scale=40)
    m_block = brick_mat('block', (0.62, 0.58, 0.52), (0.55, 0.51, 0.46), (0.40, 0.38, 0.35), scale=2.5, msize=0.01)
    m_gran  = brick_mat('granite', (0.70, 0.68, 0.64), (0.62, 0.60, 0.56), (0.50, 0.49, 0.46), scale=0.8, msize=0.006, bw=0.5, rh=0.5)
    m_perm  = mat('permcon', (0.55, 0.33, 0.27), rough=0.95, spread=0.12, scale=300, bump=0.5)   # 투수콘(적색)
    m_walk  = brick_mat('sidewalk', (0.58, 0.57, 0.54), (0.51, 0.50, 0.47), (0.42, 0.41, 0.39), scale=1.6, msize=0.008, bw=0.5, rh=0.5)
    m_kerb  = mat('kerb',  (0.70, 0.69, 0.66), rough=0.85, spread=0.10, scale=60, bump=0.25)
    m_soil  = mat('soil',  (0.24, 0.18, 0.12), spread=0.28, scale=120, bump=0.8)
    m_wood  = mat('wood',  (0.42, 0.28, 0.17), rough=0.80, spread=0.18, scale=110, bump=0.45)
    m_steel = mat('steel', (0.24, 0.24, 0.25), rough=0.45, spread=0.06, scale=40, bump=0.15)
    m_wall  = mat('wall',  (0.86, 0.84, 0.79), rough=0.8, spread=0.05, scale=40, bump=0.1)
    m_roof  = mat('roof',  (0.30, 0.22, 0.18), rough=0.75, spread=0.16, scale=60, bump=0.7)
    m_glass = mat('glass', (0.16, 0.22, 0.26), rough=0.08, spread=0.04, scale=8, bump=0.05)
    m_head  = mat('lamphead', (0.93, 0.92, 0.86), rough=0.4)
    m_tire  = mat('tire', (0.04, 0.04, 0.04), rough=0.8)
    m_hwall = [mat('hw%d' % i, c, rough=0.85, spread=0.05, scale=30) for i, c in
               enumerate([(0.86, 0.83, 0.76), (0.80, 0.78, 0.74), (0.74, 0.66, 0.56), (0.88, 0.86, 0.82)])]
    m_hroof = [mat('hr%d' % i, c, rough=0.7, spread=0.1, scale=40) for i, c in
               enumerate([(0.36, 0.20, 0.16), (0.24, 0.26, 0.30), (0.40, 0.30, 0.22)])]
    m_bldg  = [mat('bd%d' % i, c, rough=0.6, spread=0.06, scale=12) for i, c in
               enumerate([(0.72, 0.74, 0.76), (0.64, 0.62, 0.58), (0.80, 0.78, 0.72), (0.52, 0.56, 0.60)])]
    m_cars  = [mat('car%d' % i, c, rough=0.25, spread=0.03, scale=5) for i, c in
               enumerate([(0.85, 0.86, 0.87), (0.62, 0.63, 0.65), (0.08, 0.08, 0.09), (0.28, 0.29, 0.31),
                          (0.12, 0.20, 0.42), (0.55, 0.08, 0.07), (0.90, 0.90, 0.88)])]

    # ── 바탕: 부지 밖까지 잔디(주변 필지) ─────────────────────────
    slab(-60, 200, -45, 150, -0.01, m_lawn, h=0.2)

    # ── 주변: 도로 · 보도 · 지하철 출입구 ─────────────────────────
    poly_slab(ROAD, 0.0, m_road, name='road')
    poly_slab(SIDEWALK, 0.12, m_walk, name='sidewalk')
    kerb_line([(151, -45), (151, 89), (127, 113), (-60, 113)], m_kerb)
    for y in range(-40, 150, 9):                          # 동측 광로 차선
        paint_line(168.5, y, 168.5, y + 4.5, m_paint, w=0.15, z=0.004)
    paint_line(185.5, -45, 185.5, 150, m_yellow, w=0.3, z=0.004)
    for x in range(-55, 120, 9):                          # 남측 도로 차선
        paint_line(x, 124.5, x + 4.5, 124.5, m_paint, w=0.15, z=0.004)
    # 지하철 출입구 — 보도 위 18.4 × 9.2, 45° (현황도)
    sx, sy, sc = 18.4, 9.2, (131.75, 97.75)
    box(sc[0], sc[1], 0.12, sx, sy, 1.1, m_wall, rot=math.radians(45))
    box(sc[0], sc[1], 1.22, sx - 0.4, sy - 0.4, 0.08, m_steel, rot=math.radians(45))
    box(sc[0], sc[1], 2.9, sx + 0.4, sy + 0.4, 0.12, m_glass, rot=math.radians(45))
    for dx, dy in ((-7.5, -3.5), (7.5, -3.5), (-7.5, 3.5), (7.5, 3.5)):
        a = math.radians(-45)
        px = sc[0] + dx * math.cos(a) - dy * math.sin(a)
        py = sc[1] + dx * math.sin(a) + dy * math.cos(a)
        box(px, py, 0.12, 0.2, 0.2, 2.8, m_steel)

    # ── 북측 주거지 · 서측 상업지 ────────────────────────────────
    random.seed(4441)
    for i, x in enumerate(range(-2, 146, 15)):
        small_house(x + 5.5, -14.0 + random.uniform(-1.5, 1.5), 10.0, 8.5, random.choice((5.8, 6.4, 7.0)),
                    m_hwall[i % 4], m_hroof[i % 3])
        slab(x - 1.5, x + 12.5, -4.5, -3.5, 0.9, m_kerb, h=0.9)          # 담장
    slab(-60, 200, -30, -24, 0.004, m_road, h=0.05)                        # 주거지 안길
    for j, (y0, y1) in enumerate(((-30, 8), (19, 52), (56, 86), (90, 113))):
        box(-27.0, (y0 + y1) / 2, 0.0, 26.0, y1 - y0 - 2.0, 11.0 + 5.0 * (j % 2), m_bldg[j % 4])
        box(-27.0, (y0 + y1) / 2, 11.0 + 5.0 * (j % 2), 24.0, y1 - y0 - 4.0, 0.6, m_bldg[(j + 1) % 4])
    poly_slab([(-14, -45), (-5, -45), (-5, 107), (-14, 107)], 0.12, m_walk, name='w_sidewalk')
    # 차량 진출입구 — 보도를 끊고 차도까지 아스팔트(현황도 · 도면)
    poly_slab([(145, 17), (151, 17), (151, 27), (145, 27)], 0.125, m_asph, name='e_drive')
    poly_slab([(15, 107), (25, 107), (25, 113), (15, 113)], 0.125, m_asph, name='s_drive')
    poly_slab([(-14, 12), (-5, 12), (-5, 17), (-14, 17)], 0.13, m_block, name='w_path')   # 서측 보행로(5m)

    # ── 부지 안 포장 ─────────────────────────────────────────────
    poly_slab(ASPHALT, Z_ASPH, m_asph, name='asphalt')
    poly_slab(REST_NW, Z_PAVE, m_gran, name='rest_nw')
    poly_slab(TOILET_PAD, Z_PAVE, m_gran, name='toilet_pad')
    poly_slab(N_WALK, Z_PAVE, m_block, name='n_walk')
    poly_slab(W_WALK, Z_PAVE, m_perm, name='w_walk')
    poly_slab(SE_PLAZA, Z_PAVE, m_gran, name='se_plaza')
    # 경계석 — 포장 · 녹지 경계
    for ln in KERBS:
        kerb_line(ln, m_kerb)

    # ── 주차 구획선 ─────────────────────────────────────────────
    for (x0, x1, ya, yb) in STALL_ROWS:                  # 가로로 늘어선 칸(세로선)
        n = int(round((x1 - x0) / 2.5))
        for k in range(n + 1):
            paint_line(x0 + 2.5 * k, ya, x0 + 2.5 * k, yb, m_paint)
    for k in range(29):                                   # 서측 1열 — 세로로 늘어선 칸
        paint_line(10.0, 31.0 + 2.5 * k, 15.0, 31.0 + 2.5 * k, m_paint)
    for k in range(9):                                    # 장애인 주차 3.5m
        paint_line(111.0 + 3.5 * k, 63.0, 111.0 + 3.5 * k, 68.5, m_paint)
    for k in range(8):
        slab(111.4 + 3.5 * k, 114.1 + 3.5 * k, 63.4, 68.1, Z_ASPH + 0.003, m_blue, h=0.004)
        box(112.75 + 3.5 * k, 66.2, Z_ASPH + 0.004, 1.2, 1.2, 0.003, m_paint)   # 휠체어 표시 자리
    # 순환 방향 화살표 — 주차 통로 가운데
    for (x, y, rot) in ((70, 42, 0.0), (70, 60, math.pi), (60, 78.5, 0.0), (60, 97.5, math.pi),
                        (20, 60, math.pi / 2), (136, 45, -math.pi / 2), (102, 80, -math.pi / 2)):
        box(x, y, Z_ASPH, 2.6, 0.35, 0.004, m_paint, rot=rot)

    # ── 주차열 화단(가운데 녹지 + 양 끝 둥근 화단) ──────────────────
    for (x0, x1, y0, y1) in MEDIANS:
        bed_shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.2, m_soil, m_kerb,
                  ['회양목', '회양목', '산철쭉'], z=Z_ASPH + 0.05, gap=0.7)
    for (x0, x1, y0, y1) in ISLANDS:
        bed_shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.8, m_soil, m_kerb,
                  ['산철쭉', '회양목', '진달래'], z=Z_ASPH + 0.05, gap=0.55)
    # 남동 삼각 화단 (둥근 모서리)
    bed_shape(TRIANGLE, 0.6, m_soil, m_kerb, ['산철쭉', '산철쭉', '진달래'], z=Z_PAVE + 0.05, gap=0.55)

    # ── 건물 ────────────────────────────────────────────────────
    hip_building(*TOILET, 3.3, m_wall, m_roof, m_door=m_wood)
    for b in KIOSKS:
        hip_building(*b, 2.7, m_wall, m_roof)

    # ── 시설물 ──────────────────────────────────────────────────
    pergola_rect(*PERGOLA, Z_PAVE, m_wood)
    for cx, cy in GRATES:
        grate(cx, cy, Z_PAVE, 1.6, m_steel, m_soil)
    for cx, cy, deg in BENCHES:
        bench(cx, cy, deg, Z_PAVE, m_wood, m_steel)
    for cx, cy in BINS:
        cyl(cx, cy, Z_PAVE, 0.7, 0.85, m_steel)
    for cx, cy in FOUNTAINS:
        cyl(cx, cy, Z_PAVE, 0.9, 0.85, m_gran, verts=20)
        cyl(cx, cy, Z_PAVE + 0.85, 0.5, 0.08, m_steel, verts=16)
    for cx, cy in LAMPS:
        lamp(cx, cy, m_steel, m_head)
    for cx, cy in BOLLARDS:
        bollard(cx, cy, m_steel)

    # ── 주차된 차 — 칸의 절반쯤 ──────────────────────────────────
    random.seed(4442)
    for (x0, x1, ya, yb) in STALL_ROWS:
        n = int(round((x1 - x0) / 2.5))
        for k in range(n):
            if random.random() < 0.46:
                car(x0 + 2.5 * k + 1.25, (ya + yb) / 2, True, random.choice(m_cars), m_glass, m_tire)
    for k in range(28):
        if random.random() < 0.4:
            car(12.5, 31.0 + 2.5 * k + 1.25, False, random.choice(m_cars), m_glass, m_tire)
    for k in (1, 4, 6):
        car(111.0 + 3.5 * k + 1.75, 65.8, True, random.choice(m_cars), m_glass, m_tire)
    for (x, y, ay) in ((172, 10, True), (179, 60, True), (164, 95, True), (40, 120, False), (90, 128, False), (5, 128, False)):
        car(x, y, ay, random.choice(m_cars), m_glass, m_tire)

    # ── 식재 — 성운 배식평면도(답안지 III) 수량표 ───────────────────
    random.seed(444)
    P = plant
    # 북측 완충녹지(12m) — 바깥 줄 스트로브잣나무 20, 안쪽 줄 꽃나무, 관목 띠, 보도변 회양목
    for x, y in spots_line(48.5, 2.0, 143.0, 2.0, 20):
        P(x, y + random.uniform(-0.4, 0.4), '스트로브잣나무')
    inner = ['산딸나무', '꽃사과나무', '중국단풍', '산딸나무', '꽃사과나무', '중국단풍', '산딸나무', '꽃사과나무',
             '중국단풍', '산딸나무', '꽃사과나무', '중국단풍', '산딸나무']
    for (x, y), nm in zip(spots_line(52.0, 7.0, 140.0, 7.0, 13), inner):
        P(x, y, nm)
    for x in (70.0, 100.0, 128.0):
        P(x + 3.5, 7.8, '수수꽃다리_교')
    shrub_area(47.0, 144.0, 4.0, 10.2, ['사철나무', '진달래', '산철쭉', '진달래'], gap=0.9,
               avoid=[(lx - 0.8, lx + 0.8, 9.2, 10.8) for lx, _ in LAMPS])
    shrub_area(47.0, 144.0, 10.8, 11.8, ['회양목'], gap=0.45)
    shrub_area(-5.0, 29.0, 0.4, 2.7, ['회양목', '사철나무'], gap=0.55)
    for x, y in spots_line(-3.0, 1.5, 27.0, 1.5, 6):
        P(x, y, '향나무' if x > 20 else '측백')
    shrub_area(29.4, 33.8, 0.5, 11.5, ['사철나무', '회양목'], gap=0.55)
    # 서측 완충녹지(12m) — 바깥 줄 편백 14, 안쪽 줄 느티 · 산사 · 중국단풍 · 팥배, 진달래 띠
    for x, y in spots_line(-3.3, 30.0, -3.3, 104.5, 14):
        P(x, y, '편백')
    west_in = ['느티나무', '산사나무', '팥배나무', '중국단풍', '산사나무', '팥배나무', '느티나무', '산사나무',
               '팥배나무', '중국단풍', '산사나무', '팥배나무', '느티나무', '산사나무', '팥배나무', '중국단풍']
    for (x, y), nm in zip(spots_line(2.2, 29.5, 2.2, 104.0, 16), west_in):
        P(x, y + random.uniform(-0.6, 0.6), nm)
    shrub_area(-1.5, 6.2, 28.0, 106.5, ['진달래', '진달래', '사철나무', '산철쭉'], gap=0.95,
               avoid=[(3.8, 6.2, ly - 0.8, ly + 0.8) for lx, ly in LAMPS if lx < 10])
    shrub_area(6.2, 6.9, 27.5, 106.8, ['회양목'], gap=0.4)
    # 남측 완충녹지(6m) — 은행나무 13 열식, 측백 7 · 산딸 · 꽃사과, 진달래 · 회양목
    for x, y in spots_line(33.0, 105.3, 104.0, 105.3, 13):
        P(x, y, '은행나무')
    south_in = ['측백', '산딸나무', '측백', '꽃사과나무', '측백', '산딸나무', '측백', '꽃사과나무', '측백', '측백']
    for (x, y), nm in zip(spots_line(36.0, 102.8, 101.0, 102.8, 10), south_in):
        P(x, y, nm)
    shrub_area(29.8, 106.5, 101.6, 106.7, ['진달래', '회양목', '산철쭉'], gap=0.75)
    shrub_area(10.3, 14.7, 101.8, 106.7, ['회양목', '산철쭉'], gap=0.5)
    # 동측 완충녹지(6m) — 칠엽수 · 수수꽃다리, 회양목
    for x, y in spots_line(142.0, 34.5, 142.0, 69.5, 9):
        P(x, y, '칠엽수')
    shrub_area(139.4, 144.6, 32.0, 71.6, ['회양목', '사철나무', '진달래'], gap=0.7)
    # 주차열 녹지 — 녹음수 열식(1·2열 이팝나무, 3열 칠엽수, 4열 이팝나무 · 느티)
    for (x0, x1, y0, y1), nm, n in ((MEDIANS[0], '이팝나무', 17), (MEDIANS[1], '이팝나무', 17),
                                     (MEDIANS[2], '칠엽수', 11), (MEDIANS[3], '이팝나무', 11)):
        for x, y in spots_line(x0 + 2.0, (y0 + y1) / 2, x1 - 2.0, (y0 + y1) / 2, n):
            P(x, y, nm, 0.85)
    # 서측 주차열 머리 · 끝 화단, 장애인주차 앞 녹지(회화나무 5 · 수수꽃다리), 남동 섬 화단
    shrub_area(10.3, 14.6, 27.4, 30.6, ['회양목', '산철쭉'], gap=0.5)
    for x, y in spots_line(114.0, 70.2, 136.5, 70.2, 5):
        P(x, y, '회화나무')
    shrub_area(111.3, 138.7, 68.9, 71.6, ['회양목', '회양목', '진달래'], gap=0.55,
               avoid=[(lx - 0.7, lx + 0.7, 69.3, 70.7) for lx, ly in LAMPS if ly == 70])
    bed_shape([(107.2, 63.2), (110.8, 63.2), (110.8, 71.8), (107.2, 71.8)], 0.6, m_soil, m_kerb,
              ['회양목', '산철쭉'], z=Z_ASPH + 0.05, gap=0.5)
    P(109.0, 66.0, '수수꽃다리_교', 0.8)
    # 북서 휴게공간 — 수목보호대에 느티나무, 모서리에 왕벚나무 · 산딸나무
    for cx, cy in GRATES:
        P(cx, cy, '느티나무', 0.62)
    # 남동 휴게공간 — 삼각 화단에 향나무 3, 모서리에 왕벚나무 1
    for x, y in ((117.0, 82.5), (116.5, 87.5), (120.5, 83.0)):
        P(x, y, '향나무', 0.8)
    P(140.5, 75.0, '왕벚나무')

    # ── 카메라 · 빛 ─────────────────────────────────────────────
    cam_d = bpy.data.cameras.new('cam')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = 176.0
    cam_d.clip_end = 900
    cam = bpy.data.objects.new('cam', cam_d)
    bpy.context.collection.objects.link(cam)
    CX, CY = 70.0, D - 53.5
    cam_z = 160.0
    if BIRD:                                       # 조감도 — 원근, 남동 상공에서 북서를 본다
        cam_d.type = 'PERSP'
        cam_d.lens = 40.0
        cam.location = (CX + 120.0, CY - 150.0, 150.0)
        tgt = bpy.data.objects.new('aim', None)
        tgt.location = (CX - 4.0, CY + 4.0, 0.0)
        bpy.context.collection.objects.link(tgt)
        c = cam.constraints.new('TRACK_TO')
        c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    elif TOP_VIEW:
        cam_d.ortho_scale = 190.0
        cam.location = (CX + 3.0, CY + 1.0, 400.0)
        cam.rotation_euler = (0.0, 0.0, 0.0)
    else:
        cam.location = (CX, CY - cam_z, cam_z)
        cam.rotation_euler = (math.radians(CAM_TILT), 0.0, 0.0)
    bpy.context.scene.camera = cam

    sun_d = bpy.data.lights.new('sun', 'SUN')
    sun_d.energy = 3.2
    sun_d.angle = math.radians(3.0)
    sun = bpy.data.objects.new('sun', sun_d)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(44), math.radians(4), math.radians(212))

    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    bgn = world.node_tree.nodes['Background']
    bgn.inputs[0].default_value = (0.60, 0.68, 0.80, 1)
    bgn.inputs[1].default_value = 1.15
    bpy.context.scene.world = world


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = argv[argv.index('--out') + 1] if '--out' in argv else 'r01.png'
    if '--bird' in argv:
        globals()['BIRD'] = True
    if '--top' in argv:
        globals()['TOP_VIEW'] = True
        globals()['RES'] = (1650, 1100)
    if '--max' in argv:                    # 최고 품질 — 크게 뽑아 줄여 쓴다(수퍼샘플링). --bird·--top 뒤에 두어 해상도를 되돌리지 않게
        globals()['RES'] = (5120, 3413)
        globals()['SAMPLES'] = 1024
    if '--hq' in argv:
        globals()['RES'] = (3840, 2560)
        globals()['HQ'] = True
    if '--samples' in argv:
        globals()['SAMPLES'] = int(argv[argv.index('--samples') + 1])
    if '--threads' in argv:
        globals()['THREADS'] = int(argv[argv.index('--threads') + 1])
    build()
    render(os.path.abspath(out))
