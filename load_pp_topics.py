# -*- coding: utf-8 -*-
"""`_pp_topics.json` 의 주제 분류를 식물보호 문항에 기록한다.

배정은 **주제(topic_key) 단위**라, 같은 주제로 묶인 문항은 급수가 달라도
같은 분류를 받는다. 기사와 산업기사가 한 주제를 공유하므로 이렇게 해야
쪽집게 노트에서 한 덩어리로 보인다.

  python load_pp_topics.py            # 검증만
  python load_pp_topics.py --apply    # DB 반영
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

from gisa.essay_topics import siblings, topic_groups  # noqa: E402
from gisa.models import Certification, GisaEssayQuestion  # noqa: E402

CERT = '식물보호기사'
SRC = '_pp_topics.json'


def main():
    apply_ = '--apply' in sys.argv
    table = {k: v for k, v in json.load(io.open(SRC, encoding='utf-8')).items()
             if not k.startswith('_')}
    names = dict(topic_groups(CERT))
    certs = list(Certification.objects.filter(name__in=siblings(CERT)))
    qs = list(GisaEssayQuestion.objects
              .filter(certification__in=certs, source='기출')
              .exclude(topic_key=''))

    bad = sorted({q.topic_key for q in qs} - set(table))
    if bad:
        print('분류가 없는 주제 %d개 — 넣지 않는다: %s' % (len(bad), bad[:5]))
        print('  dump_pp_topics.py 를 다시 돌려 목록을 갱신했는지 보라.')
        return 1
    off = {v for v in table.values()} - set(names)
    if off:
        print('분류표에 없는 번호: %s' % sorted(off))
        return 1

    cnt, changed = Counter(), 0
    for q in qs:
        g = table[q.topic_key]
        cnt[g] += 1
        if q.topic_group != g:
            changed += 1
            q.topic_group = g

    print('%s  문항 %d건 · 주제 %d개' % (' + '.join(c.name for c in certs),
                                    len(qs), len(table)))
    for gid, nm in topic_groups(CERT):
        print('  %2d %-12s 문항 %3d건' % (gid, nm, cnt.get(gid, 0)))
    print('바뀌는 문항 %d건' % changed)

    if not apply_:
        print('(검증만 했다. --apply 를 붙여야 DB 에 들어간다)')
        return 0
    with transaction.atomic():
        for q in qs:
            q.save(update_fields=['topic_group'])
    print('반영했다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
