# -*- coding: utf-8 -*-
"""재서술할 필답 문항을 배치 파일로 추출한다.

교재 풀이를 그대로 싣지 않고 자체 서술로 바꾸기 위한 준비 작업.
LLM API를 쓰지 않고 사람(또는 이 세션의 에이전트)이 직접 읽고 쓴다.

재서술 대상은 **문장으로 된 답**이다. 단답·빈칸의 단순 정답이나 계산식은
사실 자체라 표현을 바꿀 것이 없고 저작물성도 없으므로 제외한다.

사용:
  python dump_essay_for_rewrite.py                    # 현황만 보기
  python dump_essay_for_rewrite.py --out-dir _rewrite # 배치 파일 생성
"""
import argparse
import json
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import Certification, GisaEssayQuestion   # noqa: E402

# 재서술 대상 유형 — 문장으로 서술된 답을 가진 것들
REWRITE_TYPES = {'서술', '열거', '표그림'}
# 단답·빈칸이라도 답이 이만큼 길면 서술로 보고 대상에 포함한다
LONG_ANSWER_CHARS = 60


def answer_len(q):
    return len('\n'.join(q.answer_items or [])) + len(q.answer_text or '')


def needs_rewrite(q):
    # 계산형은 제외한다. 답이 계산식과 수치라 표현을 바꿀 것이 없고,
    # 억지로 바꾸면 오히려 계산 과정이 틀어질 위험이 있다.
    if q.qtype == '계산':
        return False
    if q.qtype in REWRITE_TYPES:
        return True
    # 단답·빈칸이라도 설명이 길게 붙어 있으면 대상
    return answer_len(q) >= LONG_ANSWER_CHARS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cert', default='자연생태복원기사')
    ap.add_argument('--out-dir', default='')
    ap.add_argument('--batch-size', type=int, default=30)
    args = ap.parse_args()

    cert = Certification.objects.filter(name=args.cert).first()
    if not cert:
        print(f'자격증 없음: {args.cert}')
        return

    qs = list(GisaEssayQuestion.objects.filter(certification=cert)
              .order_by('source', 'section', 'year', 'round', 'number'))

    targets = [q for q in qs if needs_rewrite(q)]
    skipped = [q for q in qs if not needs_rewrite(q)]

    print(f'전체 {len(qs)}문항')
    print(f'  재서술 대상 {len(targets)}')
    print(f'  유지(단순 정답·계산식) {len(skipped)}')

    from collections import Counter
    print('\n[대상 유형]', dict(Counter(q.qtype for q in targets)))
    print('[유지 유형]', dict(Counter(q.qtype for q in skipped)))

    # 영역/회차별 분포
    print('\n[대상 분포]')
    grp = Counter()
    for q in targets:
        grp[q.section if q.source == '예상' else f'기출 {q.year}-{q.round}'] += 1
    for k, v in sorted(grp.items(), key=lambda x: -x[1]):
        print(f'  {k}: {v}')

    if not args.out_dir:
        print('\n--out-dir 을 주면 배치 파일을 만듭니다')
        return

    os.makedirs(args.out_dir, exist_ok=True)

    # 영역/회차 단위로 묶되, 너무 크면 batch-size로 쪼갠다
    groups = {}
    for q in targets:
        key = q.section if q.source == '예상' else f'{q.year}-{q.round}'
        groups.setdefault(key, []).append(q)

    made = 0
    for key, items in groups.items():
        chunks = [items[i:i + args.batch_size]
                  for i in range(0, len(items), args.batch_size)]
        for ci, chunk in enumerate(chunks, 1):
            safe = key.replace('·', '_').replace(' ', '_')
            name = f'{safe}_{ci}.json' if len(chunks) > 1 else f'{safe}.json'
            rows = [{
                'pk': q.pk,
                'id': f'{q.source}-{q.section}-{q.year or ""}-{q.round or ""}-{q.number}',
                'label': q.label,
                'number': q.number,
                'qtype': q.qtype,
                'points': q.points,
                'text': q.text,
                'answer_items': q.answer_items or [],
                'answer_text': q.answer_text or '',
                'reference': (q.reference or '')[:3000],
                'notes': q.notes or '',
            } for q in chunk]
            with open(os.path.join(args.out_dir, name), 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=1)
            made += 1

    print(f'\n배치 파일 {made}개 생성 → {args.out_dir}')


if __name__ == '__main__':
    main()
