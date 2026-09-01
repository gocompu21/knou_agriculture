# -*- coding: utf-8 -*-
"""2015~2019 복원 노트 문항의 답을 교과서(537문항) 답으로 교체한다.

복원 노트의 답은 수험생이 정리한 것이라 누락·오류가 있을 수 있다.
같은 주제를 다루는 문항이 교과서(영역별 예상문제 + 기출)에 있으면
그쪽 답을 정답으로 쓰고, 출처를 notes에 남긴다.

사용:
  python match_eco_essay2.py                 # 매칭 결과만 보기 (dry-run)
  python match_eco_essay2.py --apply         # _eco_essay_questions2.json 갱신
  python match_eco_essay2.py --threshold 0.5 # 유사도 기준 조정
"""
import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding='utf-8')

NOTE_JSON = '_eco_essay_questions2.json'      # 2015~2019 복원 노트 (판독 결과)
BOOK_JSON = '_eco_essay_questions.json'       # 교과서 537문항
DEFAULT_THRESHOLD = 0.45

# 매칭 정확도를 높이기 위해 제거하는 상투어
STOP_PAT = re.compile(
    r'(에\s*대하여|에\s*대해|대하여|대해|관하여|관해|다음|아래|위의|각각|모두|간단히|'
    r'설명하시오|설명하라|쓰시오|쓰라|기술하시오|서술하시오|구하시오|채우시오|고르시오|'
    r'무엇인가|무엇이라|하는가|것은|것을|하시오|한다|이다)')
NUM_PAT = re.compile(r'[0-9]+')


def norm(s):
    """비교용 정규화 — 조사·상투어·기호 제거."""
    s = re.sub(r'\[box\].*?\[/box\]', ' ', s or '', flags=re.S)
    s = re.sub(r'[①-⑮㉠-㉦]', ' ', s)
    s = STOP_PAT.sub(' ', s)
    s = re.sub(r'[^\w가-힣]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def tokens(s):
    """2글자 이상 한글 낱말 + 영문 약어 + 숫자."""
    t = set(re.findall(r'[가-힣]{2,}', s))
    t |= set(w.upper() for w in re.findall(r'[A-Za-z]{2,}', s))
    t |= set(NUM_PAT.findall(s))
    return t


def similarity(a, b):
    """문제문 유사도 — 토큰 자카드와 문자열 비율의 가중 평균."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    ta, tb = tokens(na), tokens(nb)
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    return jac * 0.65 + seq * 0.35


def book_label(b):
    """교과서 문항의 출처 표기 — 출판사명은 쓰지 않는다."""
    if b.get('source') == '기출':
        return f"{b['year']}년 {b['round']}회 {b['number']}번"
    return f"{b.get('section', '')} {b['number']}번"


def answer_len(q):
    return len('\n'.join(q.get('answer_items') or [])) + len(q.get('answer_text') or '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--threshold', type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument('--note', default=NOTE_JSON)
    ap.add_argument('--book', default=BOOK_JSON)
    args = ap.parse_args()

    if not os.path.exists(args.note):
        print(f'파일 없음: {args.note} — 먼저 merge_eco_essay2.py 를 실행하세요')
        return
    notes = json.load(open(args.note, encoding='utf-8'))
    book = json.load(open(args.book, encoding='utf-8'))
    print(f'복원 노트 {len(notes)}문항 / 교과서 {len(book)}문항')

    # 교과서 쪽 토큰을 미리 계산
    book_pre = [(b, norm(b.get('text', '')), tokens(norm(b.get('text', '')))) for b in book]

    replaced = kept = 0
    rows = []
    for q in notes:
        qn = norm(q.get('text', ''))
        qt = tokens(qn)
        best, best_sc = None, 0.0
        for b, bn, bt in book_pre:
            if not (qt & bt):            # 공통 낱말이 하나도 없으면 건너뜀
                continue
            jac = len(qt & bt) / len(qt | bt) if (qt | bt) else 0.0
            if jac < 0.12:               # 저렴한 사전 필터
                continue
            sc = jac * 0.65 + SequenceMatcher(None, qn, bn).ratio() * 0.35
            if sc > best_sc:
                best, best_sc = b, sc

        if best and best_sc >= args.threshold:
            rows.append((q, best, best_sc))
            replaced += 1
        else:
            rows.append((q, None, best_sc))
            kept += 1

    print(f'\n[매칭] 교체 대상 {replaced} / 노트 답 유지 {kept} '
          f'(기준 {args.threshold})')
    print('\n[교체될 문항]')
    for q, b, sc in rows:
        if not b:
            continue
        print(f'  {sc:.2f} {q["id"]}  {q["text"][:38]}')
        print(f'        ← 교과서 {book_label(b)}  {b["text"][:38]}')
        print(f'        답 길이 {answer_len(q)} → {answer_len(b)}')

    print('\n[노트 답을 유지하는 문항 (유사도 상위 10)]')
    for q, b, sc in sorted([r for r in rows if not r[1]], key=lambda r: -r[2])[:10]:
        print(f'  {sc:.2f} {q["id"]}  {q["text"][:50]}')

    if not args.apply:
        print('\n[dry-run] --apply 를 붙이면 파일을 갱신합니다')
        return

    out = []
    for q, b, sc in rows:
        if b:
            q['answer_items'] = b.get('answer_items') or []
            q['answer_text'] = b.get('answer_text') or ''
            if b.get('reference'):
                q['reference'] = b['reference']
            q['qtype'] = b.get('type', q.get('type'))
            src = f"답 출처: 교과서 {book_label(b)} (유사도 {sc:.2f})"
            q['notes'] = (q.get('notes', '') + ' ' + src).strip()
        else:
            q['notes'] = (q.get('notes', '') + ' 답 출처: 복원 노트').strip()
        out.append(q)

    json.dump(out, open(args.note, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(f'\n갱신 완료: {args.note} (교체 {replaced} / 유지 {kept})')


if __name__ == '__main__':
    main()
