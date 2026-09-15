# -*- coding: utf-8 -*-
"""`_ls_topics.json` 의 주제표를 조경기사·조경산업기사 실기 문항에 기록한다.

식물보호는 발문 유사도로 군집을 만들고 사람이 분류만 붙였지만, 조경은 **문항을
읽고 주제까지 손으로 배정**한다. 조경 실기는 한 문항에 사실 하나를 묻는 꼴이 많아
글자 유사도로는 같은 기준표(도시공원 규모·식재 토심·원가 요율)의 다른 칸이 한
주제로 묶이지 않기 때문이다.

- **주제키는 id 에서 만든다**(md5 앞 16자). 제목·배정을 고쳐 다시 넣어도 키가 그대로라
  정리 자료(`**주제키**`)와의 연결이 끊기지 않는다. `tag_essay_frequency` 는 조경을
  잠가 두었다 — 돌리면 해시 키로 덮어쓴다
- `freq_rounds` = 그 주제가 나온 **기출 시험지 수**(기사·산업기사 합산, 학원 제외)
- `written_freq` = kw 가운데 조경기사 필기 문항(본문+선지)에 가장 많이 나온 횟수.
  150건을 넘는 일반어는 세지 않는다
- 학원 문항도 같은 주제키를 받아 쪽집게 노트에서 함께 펼쳐지지만 빈도에는 넣지 않는다
- 주제 제목은 `gisa/essay_topic_titles.json` 에 `key:<주제키>` 로 적는다

  python load_ls_topics.py            # 검사만
  python load_ls_topics.py --apply    # DB 반영 + 제목 파일 갱신
새 문항을 넣은 뒤 이것을 돌리면 **배정되지 않은 문항 목록**이 나온다.
"""
import hashlib
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

from gisa.models import Certification, GisaEssayQuestion, GisaQuestion  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '_ls_topics.json')
TITLES = os.path.join(HERE, 'gisa', 'essay_topic_titles.json')
CERTS = {'기': '조경기사', '산': '조경산업기사'}
DF_CAP = 150


def topic_key(tid):
    return hashlib.md5(tid.encode('utf-8')).hexdigest()[:16]


def main():
    apply_ = '--apply' in sys.argv
    data = json.load(io.open(SRC, encoding='utf-8'))
    groups = dict(data['groups'])
    topics = data['topics']

    certs = {c.name: c for c in Certification.objects.filter(name__in=CERTS.values())}
    qs = list(GisaEssayQuestion.objects
              .filter(certification__in=certs.values(), source__in=('기출', '학원'))
              .select_related('certification'))
    index = {}
    for q in qs:
        tag = '학' if q.source == '학원' else ('기' if q.certification.name == '조경기사' else '산')
        index[f'{tag} {q.year}-{q.round}-{q.number}'] = q

    errors, seen = [], Counter()
    ids = Counter(t['id'] for t in topics)
    errors += [f'id 중복: {i}' for i, n in ids.items() if n > 1]
    for t in topics:
        if t['g'] not in groups:
            errors.append(f"{t['id']}: 없는 분류 {t['g']}")
        for m in t['q']:
            seen[m] += 1
            if m not in index:
                errors.append(f"{t['id']}: 없는 문항 {m}")
    errors += [f'두 주제에 배정: {m}' for m, n in seen.items() if n > 1]
    missing = sorted(set(index) - set(seen))
    if missing:
        errors.append('배정되지 않은 문항 %d건: %s' % (len(missing), ', '.join(missing)))
    if errors:
        print('\n'.join(errors))
        return 1

    # 필기 문항 본문+선지 — kw 등장 횟수
    written = [' '.join(filter(None, (q.text, q.choice_1, q.choice_2, q.choice_3, q.choice_4)))
               for q in GisaQuestion.objects.filter(exam__certification__name='조경기사')
               .only('text', 'choice_1', 'choice_2', 'choice_3', 'choice_4')]

    def df(word):
        return sum(1 for s in written if word in s)

    plan, per_group = [], Counter()
    for t in topics:
        members = [index[m] for m in t['q']]
        sheets = {(q.certification_id, q.year, q.round) for q in members if q.source == '기출'}
        wf = max([d for d in (df(k) for k in t.get('kw', [])) if d <= DF_CAP] or [0])
        plan.append((t, topic_key(t['id']), members, len(sheets), wf))
        per_group[t['g']] += 1

    print(f'주제 {len(topics)}개 · 문항 {len(seen)}건 (기출 {sum(1 for m in seen if not m.startswith("학"))}, '
          f'학원 {sum(1 for m in seen if m.startswith("학"))})')
    for g, name in data['groups']:
        print(f'  {g}. {name}: {per_group[g]}주제')
    dist = Counter(p[3] for p in plan)
    print('  시험지 수 분포:', dict(sorted(dist.items(), reverse=True)))
    print('  필기 10회 이상 + 실기 1회:', sum(1 for p in plan if p[3] <= 1 and p[4] >= 10))

    if not apply_:
        print('검사만 했습니다 (--apply 로 반영)')
        return 0

    with transaction.atomic():
        for t, key, members, freq, wf in plan:
            for q in members:
                q.topic_key, q.topic_group = key, t['g']
                q.freq_rounds, q.written_freq = freq, wf
                q.save(update_fields=['topic_key', 'topic_group', 'freq_rounds', 'written_freq'])

    titles = json.load(io.open(TITLES, encoding='utf-8'))
    for t, key, *_ in plan:
        titles['key:' + key] = t['title']
    with io.open(TITLES, 'w', encoding='utf-8') as f:
        json.dump(titles, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('반영 완료 — 제목 %d개를 %s 에 적었다' % (len(plan), os.path.relpath(TITLES, HERE)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
