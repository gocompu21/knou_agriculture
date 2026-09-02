"""필답 기출 문항을 주제순으로 다시 번호 매긴다.

회차 안에서 주제 분류(topic_group) 오름차순 → 원래 번호 순으로 정렬해
1번부터 새로 매긴다. 생태학 기초가 앞에 오고 법규가 뒤에 온다.

실제 시험지 번호는 orig_number 에 남긴다. 다른 수험 자료와 대조하거나
원본을 확인할 때 필요하다.
"""
import argparse, glob, json, os, sys, collections, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction
from gisa.models import GisaEssayQuestion as Q

LABEL = dict(Q.TOPIC_CHOICES)


def load_topics(src):
    rows = []
    for p in sorted(glob.glob(os.path.join(src, 'done_*.json'))):
        rows.extend(json.load(open(p, encoding='utf-8')))
    return {r['pk']: int(r['topic']) for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_essay_topic')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    topics = load_topics(args.src)
    qs = list(Q.objects.filter(source='기출'))
    missing = [q.pk for q in qs if q.pk not in topics]
    bad = {pk: t for pk, t in topics.items() if not 1 <= t <= 8}

    print(f'문항 {len(qs)} / 분류 결과 {len(topics)}')
    if missing:
        print(f'  분류 안 된 문항 {len(missing)}개 — 중단'); return
    if bad:
        print(f'  범위 밖 값 {bad} — 중단'); return

    dist = collections.Counter(topics.values())
    print('\n주제별 분포')
    for k in range(1, 9):
        n = dist[k]
        bar = '█' * round(n / max(dist.values()) * 30)
        print(f'  {k} {LABEL[k]:<14} {n:>4}  {bar}')

    # 회차별로 주제순 정렬 후 1번부터 다시 매긴다
    by_round = collections.defaultdict(list)
    for q in qs:
        by_round[(q.year, q.round)].append(q)

    plan = []
    for key in sorted(by_round):
        grp = sorted(by_round[key],
                     key=lambda q: (topics[q.pk], q.orig_number or q.number))
        for i, q in enumerate(grp, 1):
            plan.append((q, i, topics[q.pk]))

    moved = sum(1 for q, n, t in plan if (q.orig_number or q.number) != n)
    print(f'\n회차 {len(by_round)}개 / 번호가 바뀌는 문항 {moved}개')

    y, r = sorted(by_round)[-1]
    print(f'\n예시 — {y}년 {r}회')
    for q, n, t in [p for p in plan if p[0].year == y and p[0].round == r]:
        print(f'  {n:>2}번 ({LABEL[t]})  ← 원본 {q.orig_number or q.number}번  '
              f'{(q.text or "")[:44]}')

    if not args.apply:
        print('\n(--apply 를 붙이면 반영합니다)'); return

    with transaction.atomic():
        # unique_together(…, number) 충돌을 피하려고 음수로 비켰다가 되돌린다
        for q, n, t in plan:
            if q.orig_number is None:
                q.orig_number = q.number
            q.topic_group = t
            q.number = -n
            q.save(update_fields=['orig_number', 'topic_group', 'number'])
        for q, n, t in plan:
            q.number = n
            q.save(update_fields=['number'])
    print(f'\n반영 {len(plan)}건')


if __name__ == '__main__':
    main()
