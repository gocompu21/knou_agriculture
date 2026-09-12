# -*- coding: utf-8 -*-
"""조경(산업)기사 실기 필답형 판독 배치 → import용 JSON 병합·검증

『조경시공실무』 PART 7 Chapter 02(2022년 이후 기출)를 쪽 단위로 판독해 만든 배치
파일들을 하나로 모으고, import_essay_questions 가 받는 형태로 바꾼다.

  python merge_ls_essay.py --batches <배치 디렉토리>

만드는 것
  _ls_essay_gi.json   조경기사   실기 필답 문항
  _ls_essay_si.json   조경산업기사 실기 필답 문항

검증 (하나라도 걸리면 그 회차를 표시하고 계속)
  - 회차별 문항번호가 1부터 빠짐없이 이어지는가
  - 같은 (자격증, 연도, 회차, 번호)가 두 번 나오지 않는가
  - 문제문·답이 비어 있지 않은가
  - [svg]키[/svg] 로 자리만 잡아 둔 그림이 몇 건인가 (그림은 따로 그려 넣는다)
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

CERT_FILE = {'조경기사': '_ls_essay_gi.json', '조경산업기사': '_ls_essay_si.json'}
SVG_RE = re.compile(r'\[svg\]([\w-]+)\[/svg\]')


def load_batches(pattern):
    rows = []
    files = sorted(glob.glob(pattern))
    for f in files:
        rows += json.load(io.open(f, encoding='utf-8'))
    return files, rows


def to_import_row(q):
    """판독 배치의 한 줄을 import_essay_questions 가 받는 형태로."""
    notes = q.get('notes') or ''
    subject = q.get('subject') or ''
    if subject:
        # 과목(조경시공·조경관리…)은 아직 담을 필드가 없다. 관리자만 보는 판독 메모
        # 앞에 표식을 달아 두고, 분류 체계를 붙일 때 옮긴다.
        notes = f'[과목] {subject}' + (f'\n{notes}' if notes else '')
    return {
        'source': '기출',
        'section': '기출',
        'type': q['qtype'],
        'year': q['year'],
        'round': q['round'],
        'number': q['number'],
        'text': q['text'],
        'answer_items': q.get('answer_items') or [],
        'answer_text': q.get('answer_text') or '',
        'reference': q.get('reference') or '',
        'notes': notes,
    }


def verify(rows):
    """회차별로 훑어 이상한 곳을 알려 준다. (문제 건수, 경고 목록)"""
    warn = []
    by_round = collections.OrderedDict()
    for q in rows:
        by_round.setdefault((q['cert'], q['year'], q['round']), []).append(q)

    for key, items in by_round.items():
        cert, year, rnd = key
        nums = sorted(x['number'] for x in items)
        dup = [n for n, c in collections.Counter(nums).items() if c > 1]
        if dup:
            warn.append(f'{cert} {year}-{rnd} 문항번호 중복: {dup}')
        missing = [n for n in range(1, max(nums) + 1) if n not in nums]
        if missing:
            warn.append(f'{cert} {year}-{rnd} 문항번호 빠짐: {missing}')
        for q in items:
            where = f"{cert} {year}-{rnd} {q['number']}번"
            if not (q.get('text') or '').strip():
                warn.append(f'{where} 문제문 비어 있음')
            if not (q.get('answer_items') or (q.get('answer_text') or '').strip()):
                warn.append(f'{where} 답 비어 있음')
            if q['qtype'] not in ('열거', '서술', '단답', '빈칸', '계산', '표그림'):
                warn.append(f"{where} 알 수 없는 유형: {q['qtype']}")
    return by_round, warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batches', required=True, help='ls_batch_*.json 이 있는 디렉토리')
    ap.add_argument('--out-dir', default='.')
    args = ap.parse_args()

    files, rows = load_batches(os.path.join(args.batches, 'ls_batch_*.json'))
    print(f'배치 {len(files)}개에서 {len(rows)}문항을 읽었다.\n')

    by_round, warn = verify(rows)
    print(f"{'회차':<24}{'문항':>4}   유형")
    for (cert, year, rnd), items in by_round.items():
        t = collections.Counter(x['qtype'] for x in items)
        kinds = ' '.join(f'{k}{n}' for k, n in t.most_common())
        print(f'{cert} {year}년 {rnd}회{"":<6}{len(items):>4}   {kinds}')

    svg_keys = [m for q in rows for m in SVG_RE.findall(q['text'])]
    print(f'\n그림 자리표시 [svg] {len(svg_keys)}건: {", ".join(svg_keys)}')

    if warn:
        print(f'\n!! 확인할 것 {len(warn)}건')
        for w in warn:
            print('   -', w)
    else:
        print('\n검증 통과 — 번호 빠짐·중복 없고, 문제문과 답이 모두 차 있다.')

    for cert, fname in CERT_FILE.items():
        part = [to_import_row(q) for q in rows if q['cert'] == cert]
        part.sort(key=lambda r: (r['year'], r['round'], r['number']))
        path = os.path.join(args.out_dir, fname)
        json.dump(part, io.open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\n{path} — {len(part)}문항')


if __name__ == '__main__':
    main()
