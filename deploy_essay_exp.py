"""작성한 필답 해설을 서버로 옮긴다.

로컬 pk=6 / 서버 pk=3 으로 자격증 pk가 달라 (year, round, number)로 찾는다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

OUT = '_deploy_essay_exp.json'


def export(year, round_):
    qs = Q.objects.filter(source='기출', year=year, round=round_).exclude(reference='')
    rows = [{'year': q.year, 'round': q.round, 'number': q.number,
             'reference': q.reference} for q in qs.order_by('number')]
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건  {os.path.getsize(OUT)/1024:.0f}KB')


def load():
    rows = json.load(open(OUT, encoding='utf-8'))
    n = miss = 0
    for r in rows:
        q = Q.objects.filter(source='기출', year=r['year'], round=r['round'],
                             number=r['number']).first()
        if not q:
            miss += 1; continue
        q.reference = r['reference']
        q.save(update_fields=['reference'])
        n += 1
    print(f'해설 반영 {n}건 / 못 찾음 {miss}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    ap.add_argument('--year', type=int, default=2022)
    ap.add_argument('--round', type=int, default=1)
    a = ap.parse_args()
    export(a.year, a.round) if a.cmd == 'export' else load()
