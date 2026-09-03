# -*- coding: utf-8 -*-
"""계산 문항의 풀이를 수식 박스([eq])로 감싸고 위첨자 표기를 통일한다.

풀이가 본문 글줄에 그대로 섞여 있어 한쪽으로 치우쳐 보이고 읽기 나빴다.
수식 줄만 골라 [eq] 로 묶으면 여백을 준 박스에 세리프체로 나온다.

표기도 네 갈래로 섞여 있었다(1.01ⁿ, e^(rt), 2^{2}, ^x). 필터가 ^ 표기를
모두 위첨자로 바꾸므로 유니코드 위첨자를 ^ 표기로 통일한다.
"""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

# 유니코드 위첨자 → ^ 표기 (필터가 <sup> 로 바꾼다)
SUP = {'ⁿ': '^n', '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4',
       '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9'}

# 수식으로 볼 줄 — 등호·부등호가 있고 한글 서술이 거의 없는 줄
KOREAN = re.compile(r'[가-힣]')


def is_eq(line):
    s = line.strip()
    if not s or s.startswith('|'):          # 표는 그대로 둔다
        return False
    if not re.search(r'[=><]', s):
        return False
    ko = len(KOREAN.findall(s))
    return ko <= 3                          # '답 :', '이므로' 정도만 허용


def normalize(text):
    for k, v in SUP.items():
        text = text.replace(k, v)
    return text


def wrap(text):
    """이어지는 수식 줄들을 한 [eq] 박스로 묶는다."""
    if not text or '[eq]' in text:
        return text
    out, buf = [], []

    def flush():
        if buf:
            out.append('[eq]' + '\n'.join(buf) + '[/eq]')
            buf.clear()

    for line in text.split('\n'):
        if is_eq(line):
            buf.append(line.strip())
        else:
            flush()
            out.append(line)
    flush()
    return '\n'.join(out)


def main():
    apply = '--apply' in sys.argv
    n = 0
    for q in Q.objects.filter(source='기출', qtype='계산'):
        before = (q.answer_text or '', q.reference or '')
        at = wrap(normalize(q.answer_text or ''))
        rf = normalize(q.reference or '')     # 해설은 서술이라 박스를 씌우지 않는다
        if (at, rf) == before:
            continue
        n += 1
        print(f'  {q.year}-{q.round} #{q.number}')
        if apply:
            q.answer_text, q.reference = at, rf
            q.save(update_fields=['answer_text', 'reference'])
    print(f'{"반영" if apply else "대상"} {n}건')
    if not apply:
        print('(--apply 로 반영)')


if __name__ == '__main__':
    main()
