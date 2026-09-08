"""잡초 카드 손그림(k###.jpg)을 WeedCard.sketch_image 에 연결한다.

파일은 이미 media/weeds/s51/ 에 있어야 한다(scratchpad/weedcard/cut_sketch.py 로 추출).
손그림이 없는 카드는 건너뛴다.

  python load_weed_sketches.py            # 확인만
  python load_weed_sketches.py --apply    # DB 반영
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.conf import settings  # noqa: E402

from exam.models import WeedCard  # noqa: E402

SUBJECT_PK = 51


def main():
    apply = '--apply' in sys.argv
    cards = WeedCard.objects.filter(subject_id=SUBJECT_PK).order_by('order')
    hit, miss = [], []
    for c in cards:
        rel = 'weeds/s%d/k%03d.jpg' % (SUBJECT_PK, c.card_no)
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, rel)):
            hit.append((c, rel))
        else:
            miss.append(c.name)

    print('손그림 있음 %d장 / 없음 %d장' % (len(hit), len(miss)))
    if miss:
        print('  없는 카드:', ', '.join(miss))
    if not apply:
        print('\n--apply 를 붙이면 DB 에 반영합니다.')
        return

    n = 0
    for c, rel in hit:
        if c.sketch_image.name != rel:
            c.sketch_image.name = rel
            c.save(update_fields=['sketch_image'])
            n += 1
    print('반영', n, '건')


main()
