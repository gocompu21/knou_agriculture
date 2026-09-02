"""직접 묶은 주제 그룹을 서버에 반영한다.

자격증 pk가 로컬 6 / 서버 3으로 다르므로 (year, round, number)로 찾는다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

OUT = '_deploy_essay_group.json'


def export():
    rows = [{'year': q.year, 'round': q.round, 'number': q.number,
             'topic_key': q.topic_key, 'freq_rounds': q.freq_rounds,
             'freq_note': q.freq_note}
            for q in Q.objects.filter(source='기출').order_by('year', 'round', 'number')]
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건')


def load():
    rows = json.load(open(OUT, encoding='utf-8'))
    n = miss = 0
    for r in rows:
        q = Q.objects.filter(source='기출', year=r['year'], round=r['round'],
                             number=r['number']).first()
        if not q:
            miss += 1; continue
        q.topic_key = r['topic_key']
        q.freq_rounds = r['freq_rounds']
        q.freq_note = r['freq_note']
        q.save(update_fields=['topic_key', 'freq_rounds', 'freq_note'])
        n += 1
    print(f'반영 {n} / 못 찾음 {miss}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    a = ap.parse_args()
    (export if a.cmd == 'export' else load)()
