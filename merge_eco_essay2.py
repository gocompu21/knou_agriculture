# -*- coding: utf-8 -*-
"""2015~2019 실기 필답 기출 판독 배치 병합 + 검증

사용:
  python merge_eco_essay2.py           # 검증 + 병합 (_eco_essay_questions2.json)
  python merge_eco_essay2.py --crop    # 그림 플래그된 부분을 PDF에서 크롭
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

SRC_DIR = '_eco_essay_parsed2'
PDF = 'data/comcbt/자연생태복원기사_실기필답_기출_2015-2019.pdf'
OUT = '_eco_essay_questions2.json'
IMG_DIR = os.path.join(SRC_DIR, 'images')

# 이 자료에 있어야 할 회차
EXPECT_ROUNDS = [
    (2019, 1), (2019, 2), (2019, 3),
    (2018, 2), (2018, 3),
    (2017, 1), (2017, 3),
    (2016, 1), (2016, 3),
    (2015, 1), (2015, 2),
]
TYPES = {'열거', '서술', '단답', '빈칸', '계산', '표그림'}
REQUIRED = ['id', 'source', 'section', 'year', 'round', 'number', 'page', 'type',
            'text', 'answer_items', 'answer_text', 'reference', 'images', 'notes']


def load_all():
    rows, problems = [], []
    for f in sorted(glob.glob(os.path.join(SRC_DIR, '*.json'))):
        try:
            data = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            problems.append(f'{os.path.basename(f)}: JSON 파싱 실패 {e}')
            continue
        if not isinstance(data, list):
            problems.append(f'{os.path.basename(f)}: 배열이 아님')
            continue
        for q in data:
            q['_file'] = os.path.basename(f)
            rows.append(q)
    return rows, problems


def validate(rows):
    problems = []
    ids = Counter(q.get('id') for q in rows)
    for i, c in ids.items():
        if c > 1:
            problems.append(f'중복 id: {i} ×{c}')

    for q in rows:
        qid = q.get('id', '?')
        for k in REQUIRED:
            if k not in q:
                problems.append(f'{qid}: 필드 누락 {k}')
        if q.get('type') not in TYPES:
            problems.append(f'{qid}: type 이상 "{q.get("type")}"')
        if not (q.get('text') or '').strip():
            problems.append(f'{qid}: text 비어 있음')
        if not q.get('answer_items') and not (q.get('answer_text') or '').strip():
            problems.append(f'{qid}: 답 없음')
        if not re.match(r'^E-\d{4}-\d-\d{2}$', qid):
            problems.append(f'{qid}: id 형식 이상')
        # 문제문이 제목형으로 남아 있지 않은지 (지침대로 어미를 붙여야 함)
        t = (q.get('text') or '').rstrip()
        if t and not re.search(r'(오|까|가|？|\?|다)[.?]?$', t):
            problems.append(f'{qid}: 문제문 어미 확인 필요 — "{t[:40]}"')
        for im in q.get('images', []):
            bb = im.get('bbox')
            if not (isinstance(bb, list) and len(bb) == 4 and all(0 <= v <= 1 for v in bb)):
                problems.append(f'{qid}: bbox 이상 {bb}')

    by_round = defaultdict(list)
    for q in rows:
        by_round[(q.get('year'), q.get('round'))].append(q.get('number'))

    for key in EXPECT_ROUNDS:
        nums = sorted(n for n in by_round.get(key, []) if isinstance(n, int))
        if not nums:
            problems.append(f'{key[0]}-{key[1]}: 결과 없음')
            continue
        gaps = [n for n in range(1, max(nums) + 1) if n not in nums]
        if gaps:
            problems.append(f'{key[0]}-{key[1]}: 번호 빠짐 {gaps}')
        dup = [n for n, c in Counter(nums).items() if c > 1]
        if dup:
            problems.append(f'{key[0]}-{key[1]}: 번호 중복 {dup}')

    extra = set(by_round) - set(EXPECT_ROUNDS)
    for key in sorted(extra):
        problems.append(f'예상 밖 회차: {key}')

    return problems, by_round


def crop_images(rows):
    import fitz
    os.makedirs(IMG_DIR, exist_ok=True)
    pdf = fitz.open(PDF)
    n = 0
    for q in rows:
        for k, im in enumerate(q.get('images', [])):
            page = pdf[im['page'] - 1]
            r = page.rect
            x0, y0, x1, y1 = im['bbox']
            clip = fitz.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=clip)
            fname = f"{q['id']}_{im.get('role', 'answer')}_{k + 1}.png"
            pix.save(os.path.join(IMG_DIR, fname))
            im['file'] = fname
            n += 1
    print(f'이미지 {n}장 저장 → {IMG_DIR}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crop', action='store_true')
    args = ap.parse_args()

    rows, problems = load_all()
    print(f'로드: {len(rows)}문항 / 파일 {len(set(q["_file"] for q in rows))}개')

    p2, by_round = validate(rows)
    problems += p2

    print('\n[회차별 문항 수]')
    total = 0
    for key in EXPECT_ROUNDS:
        c = len(by_round.get(key, []))
        total += c
        print(f'  {key[0]}-{key[1]}: {c}문항')
    print(f'  합계: {total}문항')

    print('\n[유형]', dict(Counter(q.get('type') for q in rows)))
    print('[이미지]', sum(len(q.get('images', [])) for q in rows), '개')
    print('[notes]', sum(1 for q in rows if q.get('notes')), '개')

    if problems:
        print(f'\n[문제점 {len(problems)}건]')
        for p in problems[:40]:
            print('  -', p)
        if len(problems) > 40:
            print(f'  … 외 {len(problems) - 40}건')
    else:
        print('\n문제점 없음')

    if args.crop:
        crop_images(rows)

    rows.sort(key=lambda q: (-(q.get('year') or 0), q.get('round') or 0, q.get('number') or 0))
    for q in rows:
        q.pop('_file', None)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f'\n저장: {OUT} ({len(rows)}문항)')


if __name__ == '__main__':
    main()
