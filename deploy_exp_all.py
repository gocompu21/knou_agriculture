# -*- coding: utf-8 -*-
"""재작성한 필답 해설을 서버로 옮긴다.

726문항 전체를 다시 쓰는 작업이 배치 단위로 진행되므로, **로컬에 반영된
것만** 골라 내보낸다 — 아직 안 쓴 문항의 옛 해설을 건드리면 안 된다.
로컬 pk=6 / 서버 pk=3 이라 (year, round, number)로 찾는다.

  python deploy_exp_all.py export   # b*_done.json 에 있는 문항의 현재 해설 추출
  python deploy_exp_all.py load     # 서버에서
"""
import argparse
import glob
import json
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

OUT = '_deploy_exp_all.json'


def export():
    pks = set()
    for p in glob.glob('_exp_all/b*_done.json'):
        pks |= {r['pk'] for r in json.load(open(p, encoding='utf-8'))}
    rows = [{'year': q.year, 'round': q.round, 'number': q.number,
             'reference': q.reference}
            for q in Q.objects.filter(pk__in=pks).exclude(reference='')
                              .order_by('year', 'round', 'number')]
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건  {os.path.getsize(OUT)/1024:.0f}KB')


def load():
    rows = json.load(open(OUT, encoding='utf-8'))
    n = miss = 0
    for r in rows:
        q = Q.objects.filter(source='기출', year=r['year'], round=r['round'],
                             number=r['number']).first()
        if not q:
            miss += 1
            continue
        q.reference = r['reference']
        q.save(update_fields=['reference'])
        n += 1
    print(f'반영 {n} / 못 찾음 {miss}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    a = ap.parse_args()
    (export if a.cmd == 'export' else load)()
