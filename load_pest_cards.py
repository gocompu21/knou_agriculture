# -*- coding: utf-8 -*-
"""`_pest_cards.json` 을 해충 암기카드로 적재한다.

  python load_pest_cards.py            # 검증만
  python load_pest_cards.py --apply    # DB 반영

사진은 이미 `media/pests/` 에 있으므로 파일을 옮기지 않고 경로만 적는다
(ImageField 에 상대 경로를 넣으면 그대로 가리킨다). 원본과 자르는 절차는
docs/해충암기카드.md 참조.
"""
import io
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402

from gisa.models import PestCard  # noqa: E402

SRC = '_pest_cards.json'
FIELDS = ('slide', 'name', 'group', 'image', 'desc')


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open(SRC, encoding='utf-8'))

    dup = [n for n, c in Counter(r['name'] for r in rows).items() if c > 1]
    if dup:
        print('해충명이 겹친다: %s' % dup)
        return 1

    # 사진이 실제로 있는지 본다 — 없으면 화면에 깨진 그림이 뜬다
    miss = [r['name'] for r in rows
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, r['image']))]
    if miss:
        print('사진이 없는 카드 %d종: %s' % (len(miss), miss[:6]))
        return 1

    cnt = Counter(r['group'] for r in rows)
    print('%d종 · %s' % (len(rows), ' · '.join('%s %d' % kv for kv in cnt.items())))
    print('설명 평균 %d자 · 가장 짧은 것 %d자'
          % (sum(len(r['desc']) for r in rows) // len(rows),
             min(len(r['desc']) for r in rows)))

    have = {c.no: c for c in PestCard.objects.all()}
    add = sum(1 for r in rows if r['no'] not in have)
    chg = sum(1 for r in rows if r['no'] in have
              and any(str(getattr(have[r['no']], f)) != str(r[f]) for f in FIELDS))
    print('새로 넣을 것 %d종 · 고칠 것 %d종 · 이미 있는 것 %d종'
          % (add, chg, len(have)))

    if not apply_:
        print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
        return 0
    with transaction.atomic():
        for r in rows:
            PestCard.objects.update_or_create(
                no=r['no'], defaults={f: r[f] for f in FIELDS})
    print('반영했다 — 모두 %d종' % PestCard.objects.count())
    return 0


if __name__ == '__main__':
    sys.exit(main())
