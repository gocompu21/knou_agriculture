"""실기 학습자료 마크다운을 GisaEssayNote 에 넣는다.

사용:
  python load_essay_note.py freq58 _freq58/빈출58주제_정리.md "빈출 58주제"
"""
import argparse, io, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import Certification, GisaEssayNote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('path')
    ap.add_argument('title')
    ap.add_argument('--summary', default='')
    ap.add_argument('--order', type=int, default=0)
    ap.add_argument('--cert', default='자연생태복원기사')
    args = ap.parse_args()

    cert = Certification.objects.filter(name=args.cert).first()
    if not cert:
        print(f'자격증 없음: {args.cert}'); return

    content = io.open(args.path, encoding='utf-8').read()
    note, created = GisaEssayNote.objects.update_or_create(
        certification=cert, slug=args.slug,
        defaults={'title': args.title, 'summary': args.summary,
                  'content': content, 'order': args.order})
    print(f'{"생성" if created else "갱신"}  {note}  {len(content):,}자')


if __name__ == '__main__':
    main()
