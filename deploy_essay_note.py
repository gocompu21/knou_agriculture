"""실기 학습자료를 서버로 옮긴다.

자격증 pk 가 로컬 6 / 서버 3 으로 다르므로 이름으로 찾는다.
"""
import argparse, json, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import Certification, GisaEssayNote

OUT = '_deploy_essay_note.json'
CERT = '자연생태복원기사'


def export():
    cert = Certification.objects.get(name=CERT)
    rows = [{'slug': n.slug, 'title': n.title, 'summary': n.summary,
             'order': n.order, 'content': n.content}
            for n in GisaEssayNote.objects.filter(certification=cert)]
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{OUT}  {len(rows)}건  {os.path.getsize(OUT)/1024:.0f}KB')


def load():
    cert = Certification.objects.get(name=CERT)
    rows = json.load(open(OUT, encoding='utf-8'))
    for r in rows:
        n, created = GisaEssayNote.objects.update_or_create(
            certification=cert, slug=r['slug'],
            defaults={k: r[k] for k in ('title', 'summary', 'order', 'content')})
        print(f'  {"생성" if created else "갱신"}  {n.title}  {len(r["content"]):,}자')
    print(f'반영 {len(rows)}건')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['export', 'load'])
    a = ap.parse_args()
    (export if a.cmd == 'export' else load)()
