# -*- coding: utf-8 -*-
"""조경(산업)기사 실기 답의 계산식을 [eq] 블록으로 감싼다.

qtext 필터가 [eq]…[/eq] 안의 'a / b' 를 세로 분수로 바꿔 준다(frac_span).
교재처럼 식이 분수로 보이게 하려면 답의 계산식 줄을 이 블록에 넣어야 한다.

  python wrap_ls_eq.py             # 바뀔 답만 보여 준다
  python wrap_ls_eq.py --apply     # DB 반영
  python wrap_ls_eq.py --cert 조경기사 --show 3   # 앞 3건의 전후를 자세히

원칙
  - '=' 가 있고 숫자가 둘 이상인 줄만 수식으로 본다. 설명 문장은 그대로 둔다.
  - 잇따른 수식 줄은 하나의 [eq] 로 묶는다 — 줄마다 상자가 생기면 답이 산만해진다.
  - 이미 [eq] 가 있는 답은 건드리지 않는다.
"""
import argparse
import os
import re
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import GisaEssayQuestion          # noqa: E402

NUM = re.compile(r'\d')
HAN = re.compile(r'[가-힣]')


def is_formula(line):
    """수식 줄인가 — '=' 와 숫자가 있고, 한글이 글자의 35%를 넘지 않는 줄.

    '계획고가 40m이므로 h = 표고 − 40으로 잡고 …' 처럼 등호가 섞인 설명 문장까지
    수식 상자에 넣으면 답이 읽기 어려워진다. 한글 비율로 가른다 —
    '① 삽날의 용량 q = q° × e = 3.2 × 0.8 = 2.56m³' 같은 라벨 붙은 식은 남는다.
    """
    s = line.strip()
    if not s or '=' not in s:
        return False
    if '[box]' in s or '[svg]' in s or s.startswith('|'):
        return False
    if len(NUM.findall(s)) < 2:
        return False
    return len(HAN.findall(s)) / max(len(s), 1) <= 0.35


# 분자가 '·' 로 이어진 공식은 괄호로 묶어야 통째로 분수가 된다. qtext 의 분수 규칙
# (_FRAC_TERM)이 '·' 를 한 덩어리로 보지 않아, Q = 60·q·f·E / Cm 은 E/Cm 만 분수가 된다.
_DOT_NUM = re.compile(r'(?<![(\w])([A-Za-z0-9,.°₀-₉]*·[A-Za-z0-9,.·°₀-₉]*)\s*/\s*')


def parenthesize(text):
    """'60·q·f·E / Cm' → '(60·q·f·E) / Cm'. 바뀐 게 없으면 None."""
    if not text:
        return None
    new = _DOT_NUM.sub(lambda m: f'({m.group(1)}) / ', text)
    return new if new != text else None


def wrap(text):
    """잇따른 수식 줄을 [eq] 로 묶은 새 본문. 바뀐 게 없으면 None."""
    if not text or '[eq]' in text:
        return None
    lines = text.split('\n')
    out, buf, changed = [], [], False

    def flush():
        nonlocal changed
        if buf:
            out.append('[eq]' + '\n'.join(buf) + '[/eq]')
            buf.clear()
            changed = True

    for ln in lines:
        if is_formula(ln):
            buf.append(ln.rstrip())
        else:
            flush()
            out.append(ln)
    flush()
    return '\n'.join(out) if changed else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--cert', default='조경')
    ap.add_argument('--show', type=int, default=0, help='앞 N건의 전후를 자세히 본다')
    args = ap.parse_args()

    qs = GisaEssayQuestion.objects.filter(
        certification__name__startswith=args.cert).order_by('certification_id', 'year', 'round', 'number')
    n_done, shown = 0, 0
    for q in qs:
        cur = q.answer_text
        par = parenthesize(cur)          # ① 분자 괄호 보정 (두 번 돌려도 그대로)
        if par:
            cur = par
        new = wrap(cur) or (par and cur)  # ② 수식 줄을 [eq] 로 묶기
        if not new:
            continue
        n_done += 1
        tag = f'{q.certification.name} {q.year}-{q.round} {q.number}번({q.qtype})'
        if shown < args.show:
            shown += 1
            print(f'\n── {tag}\n[전]\n{q.answer_text}\n[후]\n{new}')
        else:
            print(f'  {"바꿈" if args.apply else "바꿀 것"}: {tag}')
        if args.apply:
            q.answer_text = new
            q.save(update_fields=['answer_text'])
    print(f'\n{n_done}건' + (' 반영했다.' if args.apply else ' (미반영 — --apply 로 넣는다)'))


if __name__ == '__main__':
    main()
