# -*- coding: utf-8 -*-
"""실기 필답형 판독 배치 JSON 병합 + 검증 + 이미지 크롭

사용:
  python merge_eco_essay.py            # 검증 + 병합 (_eco_essay_questions.json)
  python merge_eco_essay.py --crop     # bbox 플래그된 그림을 PDF에서 잘라 images/ 에 저장
"""
import sys, json, glob, os, re, argparse
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')
SRC_DIR = '_eco_essay_parsed'
PDF = 'data/comcbt/자연생태복원기사_실기필답_예상+기출_2022-2025.pdf'
OUT = '_eco_essay_questions.json'
IMG_DIR = os.path.join(SRC_DIR, 'images')

# 배치별 기대 문항 수 (section/회차 단위)
EXPECT_SECTION = {
    '생태학': 60, '생태조사방법': 58, '법규': 64, '환경영향평가': 50,
    '환경계획A': 13, '환경계획B': 35, '생태복원': 115,
}
EXPECT_EXAM = {
    (2022, 1): 12, (2022, 2): 11, (2022, 3): 13, (2023, 1): 15, (2023, 3): 16,
    (2024, 1): 15, (2024, 2): 15, (2025, 1): 15, (2025, 2): 15, (2025, 3): 15,
}
TYPES = {'열거', '서술', '단답', '빈칸', '계산', '표그림'}
REQUIRED = ['id', 'source', 'section', 'year', 'round', 'number', 'page', 'type',
            'text', 'answer_items', 'answer_text', 'reference', 'images', 'notes']


def load_all():
    rows, problems = [], []
    for f in sorted(glob.glob(os.path.join(SRC_DIR, '*.json'))):
        try:
            data = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            problems.append(f'{f}: JSON 파싱 실패 {e}')
            continue
        if not isinstance(data, list):
            problems.append(f'{f}: 배열이 아님')
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
            problems.append(f'{qid}: type 값 이상 "{q.get("type")}"')
        if not q.get('text', '').strip():
            problems.append(f'{qid}: text 비어 있음')
        if not q.get('answer_items') and not q.get('answer_text', '').strip():
            problems.append(f'{qid}: 답 없음 (answer_items·answer_text 모두 비어 있음)')
        if q.get('source') == '기출' and not re.match(r'^E-\d{4}-\d-\d{2}$', qid):
            problems.append(f'{qid}: 기출 id 형식 이상')
        for im in q.get('images', []):
            bb = im.get('bbox')
            if not (isinstance(bb, list) and len(bb) == 4 and all(0 <= v <= 1 for v in bb)):
                problems.append(f'{qid}: images bbox 이상 {bb}')
    # 문항 수·연속성
    by_sec = defaultdict(list)
    for q in rows:
        key = (q['year'], q['round']) if q.get('source') == '기출' else q.get('section')
        by_sec[key].append(q.get('number'))
    for key, exp in {**EXPECT_SECTION, **EXPECT_EXAM}.items():
        nums = sorted(n for n in by_sec.get(key, []) if isinstance(n, int))
        if not nums:
            problems.append(f'{key}: 결과 없음 (기대 {exp})')
            continue
        missing = sorted(set(range(1, exp + 1)) - set(nums))
        extra = sorted(set(nums) - set(range(1, exp + 1)))
        if missing:
            problems.append(f'{key}: 누락 번호 {missing}')
        if extra:
            problems.append(f'{key}: 범위 밖 번호 {extra}')
        dup = [n for n, c in Counter(nums).items() if c > 1]
        if dup:
            problems.append(f'{key}: 중복 번호 {dup}')
    return problems, by_sec


def crop_images(rows):
    import fitz
    os.makedirs(IMG_DIR, exist_ok=True)
    pdf = fitz.open(PDF)
    n = 0
    for q in rows:
        for k, im in enumerate(q.get('images', [])):
            p = pdf[im['page'] - 1]
            r = p.rect
            x0, y0, x1, y1 = im['bbox']
            clip = fitz.Rect(r.width * x0, r.height * y0, r.width * x1, r.height * y1)
            pix = p.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=clip)
            fname = f"{q['id']}_{im.get('role', 'q')}_{k + 1}.png"
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
    p2, by_sec = validate(rows)
    problems += p2

    # 요약
    print('\n[문항 수]')
    for key in list(EXPECT_SECTION) + list(EXPECT_EXAM):
        got = len(by_sec.get(key, []))
        exp = {**EXPECT_SECTION, **EXPECT_EXAM}[key]
        mark = 'OK' if got == exp else '!!'
        print(f'  {mark} {key}: {got}/{exp}')
    tc = Counter(q.get('type') for q in rows)
    print('\n[유형 분포]', dict(tc))
    print('[이미지 플래그]', sum(len(q.get('images', [])) for q in rows), '개')
    print('[notes 있는 문항]', sum(1 for q in rows if q.get('notes')), '개')

    if problems:
        print(f'\n[문제점 {len(problems)}건]')
        for p in problems:
            print('  -', p)
    else:
        print('\n문제점 없음')

    # 크롭은 저장 전에 수행해야 images[].file 이 병합 파일에 반영된다
    if args.crop:
        crop_images(rows)

    def sort_key(q):
        if q['source'] == '기출':
            return (1, q['year'], q['round'], q['number'])
        order = list(EXPECT_SECTION)
        return (0, order.index(q['section']) if q['section'] in order else 99, 0, q['number'])
    rows.sort(key=sort_key)
    for q in rows:
        q.pop('_file', None)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f'\n저장: {OUT} ({len(rows)}문항)')


if __name__ == '__main__':
    main()
