"""재서술한 필답 문제문을 서버로 옮긴다.

문항 본문만 바꾸는 작업이라 pk 대신 (source, section, year, round, number)로
찾는다. 로컬 pk=6, 서버 pk=3으로 자격증 pk가 달라 pk 매칭이 불가능하다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

OUT = '_deploy_essay_text.json'


def key(q):
    return [q.source, q.section or '', q.year, q.round, q.number]


def export():
    rows = [{'key': key(q), 'text': q.text, 'notes': q.notes or ''}
            for q in Q.objects.order_by('source', 'section', 'year', 'round', 'number')]
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건  {os.path.getsize(OUT)/1024:.0f}KB')


def load():
    with open(OUT, encoding='utf-8') as f:
        rows = json.load(f)
    n, miss, same = 0, 0, 0
    for r in rows:
        src, sec, yr, rd, num = r['key']
        q = Q.objects.filter(source=src, section=sec or '', year=yr,
                             round=rd, number=num).first()
        if not q:
            miss += 1; continue
        if q.text == r['text'] and (q.notes or '') == r['notes']:
            same += 1; continue
        q.text = r['text']
        q.notes = r['notes']
        q.save(update_fields=['text', 'notes'])
        n += 1
    print(f'갱신 {n} / 동일 {same} / 못 찾음 {miss}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    a = ap.parse_args()
    (export if a.cmd == 'export' else load)()
