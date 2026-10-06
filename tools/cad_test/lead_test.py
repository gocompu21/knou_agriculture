# -*- coding: utf-8 -*-
"""식재지시선 시험 — 긋기 → 수정 칸에서 글 고치기 → 형 바꾸기. CAD 의 시험을 새로 짤 때 본보기로 쓴다.

    ../../../venv/Scripts/python.exe tools/cad_test/lead_test.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadkit import Cad

doc = {'v': 1, 'sheet': 'a2-400', 'seq': 10, 'syms': {},
       'pts': [{'n': 1, 'x': 40, 'y': 60}, {'n': 2, 'x': 60, 'y': 60}],
       'ops': [{'id': 1, 't': 'line', 'a': 1, 'b': 2, 'ls': 'solid', 'w': 'p5', 'grp': 1, 'gname': '다각선', 'poly': True, 'tl': 0}]}
ok = True
with Cad(doc, ls={'cadLeadKind': 'plant', 'cadLeadType': 'ur', 'cadLeadArea': ''}) as c:
    c.zoom(45, 55, 6)
    c.key('l')
    c.click(40, 60)                                    # 다각선 끝점
    c.pg.fill('#fdCnt', '9'); c.pg.fill('#fdName', '스트로브잣나무'); c.pg.keyboard.press('Tab'); c.pg.fill('#fdSpec', 'H3.5 x W1.8')
    c.click(40, 50)                                    # 꺾는 자리
    t = c.texts(); print('그린 뒤', t)
    ok &= [s for s, *_ in t] == ['9 - 스트로브잣나무', 'H3.5 x W1.8']
    ok &= t[1][1] > t[0][1]                            # 규격은 수종 시작 자리에서(갯수 폭만큼 들어감)
    c.key('v'); c.click(40, 55)                        # 지시선 고르기 → 수정 칸
    ok &= c.pg.locator('#fsLead').is_visible()
    c.pg.fill('#fleCnt', '12'); c.pg.fill('#fleName', '산철쭉'); c.pg.fill('#fleSpec', 'H0.4 x W0.6'); c.pg.click('#fleGo'); c.pg.wait_for_timeout(300)
    t = c.texts(); print('수정 뒤', t); ok &= t[0][0] == '12 - 산철쭉'
    c.pg.click('#fleTypes [data-lt=dl]'); c.pg.wait_for_timeout(300)
    t = c.texts(); print('형 바꾼 뒤', t); ok &= t[0][2] > 60    # 아래로 꺾여 글이 시작점보다 아래
    print('페이지 오류', c.errors or '없음'); ok &= not c.errors
print('통과' if ok else '실패'); sys.exit(0 if ok else 1)
