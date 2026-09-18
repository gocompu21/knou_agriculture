# -*- coding: utf-8 -*-
"""기출 도면 자료 한 벌을 지운다(사진 파일까지) — 탭 이름(source)을 바꿨을 때 옛 것을 치운다.

  python drop_drawing_ref.py 444 작업          # 확인만
  python drop_drawing_ref.py 444 작업 --apply  # 지우기

`load_ls_drawing_ref.py` 는 (도면 번호, 이름, 탭 이름)으로 자료를 찾아 넣으므로,
폴더의 탭 이름을 바꾸면 새 자료가 따로 생기고 옛 것은 그대로 남는다.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaDrawingRef  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        print(__doc__)
        return
    code, source = args
    apply = '--apply' in sys.argv
    refs = GisaDrawingRef.objects.filter(code=code, source=source)
    if not refs:
        print(f'{code} · {source}: 없음')
    for r in refs:
        n = r.images.count()
        print(f'{r.title} {r.code} · {r.source}: 자료 {len(r.content):,}자 · 그림 {n}장', '→ 삭제' if apply else '')
        if apply:
            for im in r.images.all():
                im.image.delete(save=False)
                im.delete()
            r.delete()
    if not apply and refs:
        print('확인만 했습니다. 지우려면 --apply')


if __name__ == '__main__':
    main()
