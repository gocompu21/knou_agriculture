# -*- coding: utf-8 -*-
"""텍스트 레이어가 있는 필답 기출 PDF를 파싱한다.

다음카페에 올라온 기출 복원 자료는 스캔이 아니라 텍스트 PDF라
이미지 판독 없이 바로 추출할 수 있다. 다만 조판이 거칠어서
줄바꿈이 문장 중간에 들어가 있으므로 이어 붙여야 한다.

문항 형태:
    1. 문제문
     A. 답
     ※ 보충 설명(참고)

사용:
  python parse_eco_essay_text.py --pdf <경로> --year 2021 --round 3
  python parse_eco_essay_text.py --pdf <경로> --year 2021 --round 3 --out a.json
"""
import argparse
import json
import re
import sys

import fitz

sys.stdout.reconfigure(encoding='utf-8')

# 문항 시작: 줄머리의 "12." / "12)" — 앞에 공백이 없어야 한다
Q_START = re.compile(r'^(\d{1,2})[.)]\s*(.*)$')
# 답 시작: " A." / " 답." / "▶"
A_START = re.compile(r'^\s*(?:A|답)\s*[.)]\s*(.*)$|^\s*▶\s*(.*)$')
# 참고: "※"
REF_START = re.compile(r'^\s*※\s*(.*)$')
# 페이지 머리말·꼬리말
NOISE = re.compile(r'(다음카페|cafe\.daum|^-\s*\d+\s*-$|^\d+$)')


def join_lines(lines):
    """조판으로 끊긴 줄을 문장으로 잇는다.

    한글 PDF는 폭에 맞춰 문장 중간에서 줄을 끊는다. 다음 줄이
    소문자·한글로 이어지면 붙이고, 새 항목 기호로 시작하면 줄을 유지한다.
    """
    out = []
    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            continue
        # 새 항목으로 보이는 줄은 그대로 시작
        if re.match(r'^\s*(?:[-•*]|\d+[).]|[①-⑮]|[가-힣]\))', s):
            out.append(s.strip())
            continue
        if out and not re.search(r'[.。:：]$', out[-1]):
            # 앞 줄이 끝나지 않았으면 이어 붙인다
            out[-1] = out[-1].rstrip() + ' ' + s.strip()
        else:
            out.append(s.strip())
    return out


def parse(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for pg in doc:
        for ln in pg.get_text().split('\n'):
            if NOISE.search(ln.strip()):
                continue
            lines.append(ln)

    items, cur, mode = [], None, None
    for ln in lines:
        m = Q_START.match(ln)
        if m and int(m.group(1)) <= 30:
            if cur:
                items.append(cur)
            cur = {'number': int(m.group(1)), 'q': [m.group(2)], 'a': [], 'ref': []}
            mode = 'q'
            continue
        if cur is None:
            continue
        m = A_START.match(ln)
        if m:
            mode = 'a'
            txt = m.group(1) or m.group(2) or ''
            if txt.strip():
                cur['a'].append(txt)
            continue
        m = REF_START.match(ln)
        if m:
            mode = 'ref'
            if m.group(1).strip():
                cur['ref'].append(m.group(1))
            continue
        cur[{'q': 'q', 'a': 'a', 'ref': 'ref'}[mode]].append(ln)
    if cur:
        items.append(cur)

    for it in items:
        it['q'] = join_lines(it['q'])
        it['a'] = join_lines(it['a'])
        it['ref'] = join_lines(it['ref'])
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    items = parse(args.pdf)
    print(f'추출 {len(items)}문항\n')
    rows = []
    for it in items:
        qtext = '\n'.join(it['q']).strip()
        atext = '\n'.join(it['a']).strip()
        rtext = '\n'.join(it['ref']).strip()
        print(f'[{it["number"]:2d}] {qtext[:70]}')
        print(f'     답: {atext[:70] or "(없음)"}')
        if rtext:
            print(f'     참고: {rtext[:60]}')
        rows.append({
            'id': f'E-{args.year}-{args.round}-{it["number"]:02d}',
            'source': '기출', 'section': '기출',
            'year': args.year, 'round': args.round, 'number': it['number'],
            'page': 0, 'type': '', 'text': qtext,
            'answer_items': [], 'answer_text': atext,
            'reference': rtext, 'images': [], 'notes': '',
        })

    if args.out:
        json.dump(rows, open(args.out, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f'\n저장: {args.out}')


if __name__ == '__main__':
    main()
