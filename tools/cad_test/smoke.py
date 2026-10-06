# -*- coding: utf-8 -*-
"""운영 서버 도면 하나를 그대로 열어 본다 — 페이지 오류가 없는지, 화면이 어떻게 보이는지.

    ../../../venv/Scripts/python.exe tools/cad_test/smoke.py 10          # 서버 도면 pk 10
    ../../../venv/Scripts/python.exe tools/cad_test/smoke.py 10 --port 8097

서버는 읽기만 한다. 결과 그림은 tools/cad_test/out/ (git 밖).
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad, server_drawing

ap = argparse.ArgumentParser(); ap.add_argument('pk', type=int); ap.add_argument('--port', type=int, default=8099)
a = ap.parse_args()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'); os.makedirs(OUT, exist_ok=True)
j = server_drawing(a.pk, cache_dir=OUT)
d = dict(j['data']); d['sheet'] = j['sheet'] or d.get('sheet')
print(f"서버 도면 {a.pk} '{j['title']}' — 작도 {len(d['ops'])}줄 · 점 {len(d['pts'])}개")
with Cad(d, port=a.port, size=(1600, 1000), wait=4000) as c:
    f = os.path.join(OUT, f'smoke{a.pk}.png'); c.shot(f)
    print('그림', f)
    print('페이지 오류', c.errors or '없음')
