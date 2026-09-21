# -*- coding: utf-8 -*-
"""실기 필답 합격 전략 문서(`docs/*_실기합격전략.md`)의 수치를 다시 센다.

**회차를 더 넣으면 문서의 숫자가 전부 달라진다.** 그때 손으로 세지 말고 이것을
돌린다. 핵심 셈은 하나다 — 회차마다 "그 문항의 `topic_key` 가 **앞선 회차에**
나온 적이 있나"를 보고, `points` 로 가중해 만점으로 환산한다.

    python analyze_essay_pass.py 6        # 자격증 pk (로컬 자연생태복원 = 6)

같은 방식을 식물보호(pk 1·2)에도 쓸 수 있으나, 그쪽은 기사·산업기사를 한 덩어리로
묶어 세야 한다(`essay_topics.SIBLING_GROUPS`).
"""
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup(); sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict
from gisa.models import GisaEssayQuestion, Certification

cert = Certification.objects.get(pk=int(sys.argv[1]) if len(sys.argv) > 1 else 6)
qs = list(GisaEssayQuestion.objects.filter(certification=cert, source='기출'))
rounds = sorted({(q.year, q.round) for q in qs})
by_round = defaultdict(list)
for q in qs:
    by_round[(q.year, q.round)].append(q)

vals = []
for yr in rounds[-8:]:
    prev = set()
    for r in rounds:
        if r >= yr: break
        prev |= {q.topic_key for q in by_round[r] if q.topic_key}
    items = by_round[yr]
    tot = sum(float(q.points or 0) for q in items)
    got = sum(float(q.points or 0) for q in items if q.topic_key in prev)
    vals.append(got)
print(f'최근 8회차 기출주제 득점: 평균 {sum(vals)/8:.1f}점 (최소 {min(vals):.1f} 최대 {max(vals):.1f}) / 45점'
      f' = {sum(vals)/8/45*100:.1f}%')

recent = [q for q in qs if (q.year, q.round) in rounds[-10:]]
rp = sum(float(q.points or 0) for q in recent)
print()
print('최근 10회차 유형별 배점 몫')
for t, c in Counter(q.qtype for q in recent).most_common():
    p = sum(float(q.points or 0) for q in recent if q.qtype == t)
    print(f'  {t:5s} {c:3d}건  배점 {p:5.1f}  {p/rp*100:5.1f}%')
print()
print('최근 10회차 분류별 배점 몫')
from gisa.essay_topics import topic_groups
NAME = dict(topic_groups(cert.name))
for g, c in Counter(q.topic_group for q in recent).most_common():
    p = sum(float(q.points or 0) for q in recent if q.topic_group == g)
    print(f'  {NAME.get(g,"?"):14s} {c:3d}건  {p/rp*100:5.1f}%')
print()
print('회차당 문항 수(최근 10):', [len(by_round[yr]) for yr in rounds[-10:]])
