import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup(); sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict
from gisa.models import GisaEssayQuestion, Certification

cert = Certification.objects.get(pk=6)
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
from gisa.essay_topics import TOPIC_GROUPS
NAME = dict(TOPIC_GROUPS['자연생태복원기사'])
for g, c in Counter(q.topic_group for q in recent).most_common():
    p = sum(float(q.points or 0) for q in recent if q.topic_group == g)
    print(f'  {NAME.get(g,"?"):14s} {c:3d}건  {p/rp*100:5.1f}%')
print()
print('회차당 문항 수(최근 10):', [len(by_round[yr]) for yr in rounds[-10:]])
