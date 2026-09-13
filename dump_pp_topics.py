# -*- coding: utf-8 -*-
"""식물보호 실기 주제(topic_key)를 분류용 목록으로 뽑는다.

`topic_group`(주제 분류)은 규칙으로 못 맞힌다 — 자연생태복원에서 키워드 가중치로
해 보다 58%가 한 항목에 몰려 실패한 적이 있다(`classify_essay_std.py` 머리말).
그래서 **문항을 읽고 사람이 배정한다.** 다만 358문항을 하나씩 보지 않고,
이미 묶인 주제(topic_key) 단위로 배정한다 — 176번만 판단하면 되고, 같은 주제가
다른 분류로 흩어지는 일도 없다.

  python dump_pp_topics.py              # _pp_topics.md 로 목록을 뽑는다
  python dump_pp_topics.py --check      # 배정 결과(_pp_topics.json)를 검사만
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from gisa.essay_topics import siblings, topic_groups  # noqa: E402
from gisa.models import Certification, GisaEssayQuestion  # noqa: E402

CERT = '식물보호기사'
OUT_MD = '_pp_topics.md'
OUT_JSON = '_pp_topics.json'


def rows():
    certs = list(Certification.objects.filter(name__in=siblings(CERT)))
    short = {c.pk: ('산기' if '산업' in c.name else '기사') for c in certs}
    qs = (GisaEssayQuestion.objects
          .filter(certification__in=certs, source='기출')
          .exclude(topic_key='')
          .order_by('-freq_rounds', 'topic_key', '-year', '-round', 'number'))
    topics = {}
    for q in qs:
        t = topics.setdefault(q.topic_key, {'key': q.topic_key, 'freq': q.freq_rounds,
                                            'qs': [], 'sheets': []})
        t['qs'].append(q)
        lab = '%s%d-%d-%d' % (short.get(q.certification_id, ''), q.year, q.round, q.number)
        t['sheets'].append(lab)
    return sorted(topics.values(), key=lambda t: (-t['freq'], -len(t['qs'])))


def head(q, n=88):
    """발문 + 상자 + 답 첫머리.

    식물보호 발문은 "다음 용어의 뜻을 각각 쓰시오"처럼 상투적인 것이 많아
    그것만 보면 무엇을 묻는지 알 수 없다. 묻는 알맹이는 상자(`[box]`) 안이나
    답에 있으므로 함께 보여 준다 — 안 그러면 분류를 할 수가 없다.
    """
    def flat(x):
        x = re.sub(r'\[/?(box|eq)\]', ' ', x or '')
        return re.sub(r'\s+', ' ', x).strip()

    s = flat(q.text)[:n]
    ans = flat(' / '.join((q.answer_items or [])[:2]))
    return '%s  →  %s' % (s, ans[:60]) if ans else s


def main():
    ts = rows()
    if '--check' in sys.argv:
        got = json.load(io.open(OUT_JSON, encoding='utf-8'))
        got = {k: v for k, v in got.items() if not k.startswith('_')}
        valid = {gid for gid, _ in topic_groups(CERT)}
        miss = [t['key'] for t in ts if t['key'] not in got]
        bad = {k: v for k, v in got.items() if v not in valid}
        extra = [k for k in got if k not in {t['key'] for t in ts}]
        print('주제 %d개 · 배정 %d개' % (len(ts), len(got)))
        if miss:
            print('  배정 안 된 주제 %d개: %s' % (len(miss), miss[:6]))
        if bad:
            print('  분류 번호가 범위 밖: %s' % bad)
        if extra:
            print('  없는 주제 키: %s' % extra[:6])
        if not (miss or bad or extra):
            cnt = {}
            for v in got.values():
                cnt[v] = cnt.get(v, 0) + 1
            names = dict(topic_groups(CERT))
            print('  이상 없음. 분류별 주제 수:')
            for gid, nm in topic_groups(CERT):
                print('    %2d %-12s %3d개' % (gid, nm, cnt.get(gid, 0)))
        return 0

    with io.open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('# 식물보호 실기 주제 분류\n\n')
        f.write('분류: ' + ' / '.join('%d %s' % g for g in topic_groups(CERT)) + '\n\n')
        f.write('주제 %d개. 각 줄의 키를 `_pp_topics.json` 에 "키": 분류번호 로 적는다.\n\n')
        for i, t in enumerate(ts, 1):
            f.write('%3d. `%s` [%d장·%d문항] %s\n' % (
                i, t['key'], t['freq'], len(t['qs']), ' '.join(t['sheets'][:6])))
            for q in t['qs'][:1]:
                f.write('     - %s\n' % head(q))
            f.write('\n')
    print('%s 에 주제 %d개를 적었다' % (OUT_MD, len(ts)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
