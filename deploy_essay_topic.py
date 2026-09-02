"""주제 분류와 재부여한 번호를 서버로 옮긴다.

번호가 바뀌므로 (year, round, orig_number)로 문항을 찾는다. 서버는 아직
orig_number 가 비어 있으므로 첫 배포에서는 현재 number 로 대조한다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction
from gisa.models import GisaEssayQuestion as Q

OUT = '_deploy_essay_topic.json'


def export():
    rows = [{'year': q.year, 'round': q.round,
             'orig': q.orig_number, 'new': q.number, 'topic': q.topic_group}
            for q in Q.objects.filter(source='기출').order_by('year', 'round', 'number')]
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건')


def load():
    rows = json.load(open(OUT, encoding='utf-8'))
    with transaction.atomic():
        found = []
        for r in rows:
            # 이미 재부여된 서버라면 orig_number 로, 처음이라면 number 로 찾는다
            q = (Q.objects.filter(source='기출', year=r['year'], round=r['round'],
                                  orig_number=r['orig']).first()
                 or Q.objects.filter(source='기출', year=r['year'], round=r['round'],
                                     number=r['orig'], orig_number__isnull=True).first())
            if not q:
                print(f"  못 찾음: {r['year']}-{r['round']}-{r['orig']}"); continue
            found.append((q, r))
        # unique_together 충돌을 피해 음수로 비켰다가 되돌린다
        for q, r in found:
            if q.orig_number is None:
                q.orig_number = r['orig']
            q.topic_group = r['topic']
            q.number = -r['new']
            q.save(update_fields=['orig_number', 'topic_group', 'number'])
        for q, r in found:
            q.number = r['new']
            q.save(update_fields=['number'])
    print(f'반영 {len(found)} / 전체 {len(rows)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    a = ap.parse_args()
    (export if a.cmd == 'export' else load)()
