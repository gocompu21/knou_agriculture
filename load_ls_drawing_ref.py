# -*- coding: utf-8 -*-
"""조경기사 작업형 — 기출 도면별 자료(작도 팁·수량표·완성 도면 사진)를 넣는다.

자료는 `_ls_drawing_refs/<도면 번호>/` 에 둔다.
  content.md   작도 팁(마크다운)
  *.jpg        완성 도면 사진 — 파일 이름 차례대로, 설명은 CAPTIONS

- 287 아파트단지 입구 : 「1-1. 팁 (아파트단지입구 287).hwp」에서 뽑았다. 원문은 문제 2 → 3 → 1
  차례였는데 1 → 2 → 3 으로 옮겼고, 번호가 두 번 나온 ⑦ 을 ⑧~⑪ 로 고쳤다.
  식재 수량표의 수량 칸은 원문이 비어 있어 완성 도면 사진에서 읽었다

  python load_ls_drawing_ref.py            # 검사만
  python load_ls_drawing_ref.py --apply    # 넣기(그림은 지우고 다시 넣는다)
"""
import io
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
REFS = {
    '287': {'title': '아파트단지 입구', 'captions': {
        '1_concept.jpg': '답안지 I · 설계 구상개념도 (1/300)',
        '2_plan.jpg': '답안지 II · 기본설계도',
        '3_section.jpg': '답안지 III · A-A′ 단면도 (1/200)',
    }},
}


def main():
    apply_ = '--apply' in sys.argv
    cert = Certification.objects.get(name='조경기사')
    for code, spec in REFS.items():
        folder = os.path.join(SRC, code)
        content = io.open(os.path.join(folder, 'content.md'), encoding='utf-8').read()
        images = sorted(f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png')))
        print(f"{spec['title']} {code}: 자료 {len(content):,}자 · 그림 {len(images)}장")
        if not apply_:
            continue
        ref, _ = GisaDrawingRef.objects.update_or_create(
            certification=cert, code=code, title=spec['title'], defaults={'content': content})
        for im in ref.images.all():
            im.image.delete(save=False)
            im.delete()
        for i, fn in enumerate(images):
            with open(os.path.join(folder, fn), 'rb') as fh:
                obj = ref.images.create(caption=spec['captions'].get(fn, ''), order=i,
                                        image=File(fh, name=fn))
            print('  ', obj.image.name)
    print('반영 완료' if apply_ else '검사만 했습니다 (--apply 로 반영)')


if __name__ == '__main__':
    main()
