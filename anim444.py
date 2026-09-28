# -*- coding: utf-8 -*-
"""444 주차공원 — 모형이 도면 위로 솟아오르는 애니메이션(소개 영상용).

make444.py 의 build() 를 그대로 불러 모형을 세운 뒤,
  ① 카메라: 평면(도면과 같은 구도) → 45° 축측도(make444 기본 구도)로 기울인다
  ② 물체: 바닥(포장·도로)은 처음부터 있고, 나머지는 땅속에서 솟아오른다
     화단·시설 → 건물 → 나무·가로등 → 자동차 차례
프레임을 PNG 로 뽑는다.

    blender -b -P anim444.py -- --out frames/ [--frames 0-191] [--samples 24] [--res 1500x1000] [--threads 18]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
G = {'__name__': 'make444', '__file__': os.path.join(HERE, 'make444.py')}
exec(open(os.path.join(HERE, 'make444.py'), encoding='utf-8').read(), G)

FPS = 24
N_FRAMES = 192                      # 8초
TILT_START, TILT_END = 24, 120      # 카메라가 기우는 구간
STAGES = [                          # (이름, 솟기 시작, 끝) — 각 물체는 이 구간 안에서 차례로 솟는다
    ('low', 30, 80),                # 화단 흙·관목·벤치·볼라드
    ('bldg', 55, 105),              # 건물·지붕·퍼걸러·출입구
    ('tall', 80, 140),              # 나무·가로등
    ('car', 110, 160),              # 자동차
]
RISE = 14                           # 한 물체가 솟는 데 걸리는 프레임


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def world_box(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(c.x for c in cs), max(c.x for c in cs), min(c.y for c in cs), max(c.y for c in cs),
            min(c.z for c in cs), max(c.z for c in cs))


def classify(o):
    mats = [s.material.name for s in o.material_slots if s.material]
    x0, x1, y0, y1, z0, z1 = world_box(o)
    if z1 <= 0.3:
        return None                                     # 바닥 — 처음부터 있다
    if any(m.startswith(('car', 'tire')) for m in mats):
        return 'car'
    if any(m == 'glass' for m in mats) and z1 < 2.2 and (x1 - x0) < 6 and (y1 - y0) < 6:
        return 'car'                                    # 차 유리
    if any(m.startswith(('wall', 'roof', 'hw', 'hr', 'bd', 'steel', 'glass', 'wood')) for m in mats) and z1 > 1.8:
        return 'bldg'
    if z1 > 1.8:
        return 'tall'
    return 'low'


def animate_objects():
    rnd = random.Random(7)
    groups = {k: [] for k, _, _ in STAGES}
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        k = classify(o)
        if k:
            groups[k].append(o)
    for k, f0, f1 in STAGES:
        objs = groups[k]
        # 서→동으로 훑듯 솟게: x 좌표 순으로 시작 프레임을 나눠 준다(조금 흔든다)
        objs.sort(key=lambda o: world_box(o)[0] + rnd.uniform(-8, 8))
        n = max(1, len(objs))
        for i, o in enumerate(objs):
            x0, x1, y0, y1, z0, z1 = world_box(o)
            drop = (z1 - z0) + 0.6
            z = o.location.z
            start = f0 + (f1 - RISE - f0) * i / n
            o.location.z = z - drop
            o.keyframe_insert('location', index=2, frame=0)
            o.keyframe_insert('location', index=2, frame=int(start))
            o.location.z = z
            o.keyframe_insert('location', index=2, frame=int(start + RISE))
        print('stage', k, len(objs))
    # 보간은 기본(베지어, 앞뒤 완만)으로 둔다 — 블렌더 5 는 Action 이 층 구조라 fcurves 를 바로 못 만진다


def animate_camera():
    cam = bpy.context.scene.camera
    CX, CY = 70.0, G['D'] - 53.5
    top_t, axo_t = Vector((CX + 3.0, CY + 1.0, 0.0)), Vector((CX, CY, 0.0))
    R = 226.0
    for f in range(N_FRAMES):
        p = ease((f - TILT_START) / (TILT_END - TILT_START))
        th = math.radians(G['CAM_TILT']) * p
        tgt = top_t.lerp(axo_t, p)
        cam.location = tgt + Vector((0.0, -R * math.sin(th), R * math.cos(th)))
        cam.rotation_euler = (th, 0.0, 0.0)
        cam.data.ortho_scale = 190.0 + (176.0 - 190.0) * p
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.keyframe_insert('ortho_scale', frame=f)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    arg = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    out = os.path.abspath(arg('--out', 'frames')) + os.sep
    f0, f1 = (int(v) for v in arg('--frames', '0-%d' % (N_FRAMES - 1)).split('-'))
    rw, rh = (int(v) for v in arg('--res', '1500x1000').split('x'))
    G['build']()
    sc = bpy.context.scene
    sc.camera.data.type = 'ORTHO'
    animate_camera()
    animate_objects()
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = int(arg('--samples', '24'))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.device = 'CPU'
    sc.render.threads_mode = 'FIXED'
    sc.render.threads = int(arg('--threads', '18'))
    sc.render.resolution_x, sc.render.resolution_y = rw, rh
    sc.render.fps = FPS
    try:
        sc.view_settings.view_transform = 'Standard'
    except TypeError:
        pass
    sc.render.image_settings.file_format = 'PNG'
    if '--only' in argv:                                  # 시험용 — 몇 장만
        for f in (int(v) for v in arg('--only', '0').split(',')):
            sc.frame_set(f)
            sc.render.filepath = out + 'f_%04d.png' % f
            bpy.ops.render.render(write_still=True)
    else:
        sc.frame_start, sc.frame_end = f0, f1
        sc.render.filepath = out + 'f_'
        bpy.ops.render.render(animation=True)
    print('DONE', out)


main()
