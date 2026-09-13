# -*- coding: utf-8 -*-
"""`_pesticide_cards.json` 을 농약 암기카드로 적재한다.

  python load_pesticide_cards.py            # 검증만
  python load_pesticide_cards.py --apply    # DB 반영

원본은 한울회 배포 `농약_DVD_기출.pptx`(2018~2023 기출 빈도, 92종).
슬라이드에서 농약명·분류 단서·출제수를 뽑고, 구분(충·균·초)은 앞머리의
정답표 이미지를 읽어 옮겼다. 만드는 절차는 docs/농약암기카드.md 참조.
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

from django.db import transaction  # noqa: E402

from gisa.models import PesticideCard  # noqa: E402

SRC = '_pesticide_cards.json'
FIELDS = ('name', 'category', 'hint', 'whole', 'exam_count',
          'family', 'action', 'target', 'note')


def main():
    apply_ = '--apply' in sys.argv
    rows = json.load(io.open(SRC, encoding='utf-8'))

    # 같은 이름이 두 번 들어오면 unique 제약에 걸려 적재가 중간에 멎는다
    dup = [n for n, c in Counter(r['name'] for r in rows).items() if c > 1]
    if dup:
        print('농약명이 겹친다: %s' % dup)
        return 1
    bad = [r['no'] for r in rows
           if r['category'] not in ('살충제', '살균제', '제초제')]
    if bad:
        print('구분이 잘못된 번호: %s' % bad)
        return 1

    cnt = Counter(r['category'] for r in rows)
    print('%d종 · %s' % (len(rows), ' · '.join('%s %d' % kv for kv in cnt.items())))
    print('통암기(단서 없음) %d종 · 최다 출제 %s'
          % (sum(1 for r in rows if r['whole']),
             ', '.join('%s %d회' % (r['name'], r['exam_count'])
                       for r in sorted(rows, key=lambda x: -x['exam_count'])[:3])))

    have = {c.no: c for c in PesticideCard.objects.all()}
    add = sum(1 for r in rows if r['no'] not in have)
    chg = sum(1 for r in rows if r['no'] in have
              and any(getattr(have[r['no']], f) != r[f] for f in FIELDS))
    print('새로 넣을 것 %d종 · 고칠 것 %d종 · 이미 있는 것 %d종'
          % (add, chg, len(have)))

    if not apply_:
        print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
        return 0
    with transaction.atomic():
        for r in rows:
            PesticideCard.objects.update_or_create(
                no=r['no'], defaults={f: r[f] for f in FIELDS})
    print('반영했다 — 모두 %d종' % PesticideCard.objects.count())
    return 0


if __name__ == '__main__':
    sys.exit(main())
