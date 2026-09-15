# -*- coding: utf-8 -*-
"""조경기사 작업형 — 기출 도면별 자료(작도 팁·수량표·완성 도면 사진)를 넣는다.

자료는 `_ls_drawing_refs/<도면 번호>/` 에 도면마다 한 폴더씩 둔다.
  meta.json    {"title": 도면명(출제 목록과 같은 이름), "captions": {파일: 설명}}
  content.md   작도 팁(마크다운). 큰 단계는 (1)(2)…, 그 아래 단계는 ①②… 로 적는다
  *.jpg        완성 도면 사진 — 파일 이름 차례대로. 집게·배경을 잘라 도면지만 남긴다

원본은 수험 자료의 「N-1. 팁 (도면명 번호).hwp」다. 원문은 문제 2 → 3 → 1 차례라 1 → 2 → 3 으로
옮기고, 식재 수량표의 비어 있는 수량 칸은 완성 도면 사진의 수량표에서 읽는다(다르면 그 사실을 적는다).

  python load_ls_drawing_ref.py              # 검사만
  python load_ls_drawing_ref.py --apply      # 모든 도면 넣기(그림은 지우고 다시 넣는다)
  python load_ls_drawing_ref.py --apply 412  # 한 도면만
"""
import io
import json
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files import File  # noqa: E402

from gisa.models import Certification, GisaDrawingRef  # noqa: E402

SRC = os.path.join(HERE, '_ls_drawing_refs')


def main():
    apply_ = '--apply' in sys.argv
    only = [a for a in sys.argv[1:] if a.isdigit()]
    cert = Certification.objects.get(name='조경기사')
    for code in sorted(os.listdir(SRC)):
        folder = os.path.join(SRC, code)
        if not os.path.isdir(folder) or (only and code not in only):
            continue
        meta = json.load(io.open(os.path.join(folder, 'meta.json'), encoding='utf-8'))
        content = io.open(os.path.join(folder, 'content.md'), encoding='utf-8').read()
        images = sorted(f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png')))
        missing = [f for f in images if f not in meta.get('captions', {})]
        print(f"{meta['title']} {code}: 자료 {len(content):,}자 · 그림 {len(images)}장"
              + (f" · 설명 없음 {missing}" if missing else ''))
        if not apply_:
            continue
        ref, _ = GisaDrawingRef.objects.update_or_create(
            certification=cert, code=code, title=meta['title'], defaults={'content': content})
        for im in ref.images.all():
            im.image.delete(save=False)
            im.delete()
        for i, fn in enumerate(images):
            with open(os.path.join(folder, fn), 'rb') as fh:
                ref.images.create(caption=meta['captions'].get(fn, ''), order=i, image=File(fh, name=fn))
    print('반영 완료' if apply_ else '검사만 했습니다 (--apply 로 반영)')


if __name__ == '__main__':
    main()
