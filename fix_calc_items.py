# -*- coding: utf-8 -*-
"""계산 문항의 답을 「계산」과 「답」 두 항목으로 정리한다.

서술·열거형은 ①②③이 채점 포인트 단위라 맞지만, 계산은 성격이 다르다 —
풀이는 하나의 흐름이고 최종 답이 따로 있다. ①②③으로 쪼개면 한 계산이
여러 조각으로 흩어져 읽기 나쁘다.

계산형 채점은 grade_calc_by_rule / grade_calc_by_llm 이 최종 답 수치를
기준으로 하므로(항목 수는 배점 분할에만 쓰인다) 2항목으로 바꿔도 안전하다.

  answer_items = ['계산\n[eq]…풀이…[/eq]', '답 : …']
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

# ①②③ 머리표와 '답 :' 앞의 번호를 떼어낸다
NUM = re.compile(r'^\s*[①-⑮]\s*')
# 마지막 항목이 답인지 판정
ANS = re.compile(r'^(답|정답)\s*[:：]|^\s*∴')


def split_answer(q):
    """기존 답을 (계산 본문, 최종 답) 으로 가른다."""
    items = [NUM.sub('', s).strip() for s in (q.answer_items or []) if s.strip()]
    if not items:
        text = (q.answer_text or '').strip()
        if not text:
            return None
        # 한 덩어리로 저장된 풀이는 '∴' 나 마지막 '=' 뒤를 답으로 가른다
        m = re.search(r'∴\s*(.+)$', text, re.S)
        if m:
            body = text[:m.start()].strip()
            return ([body] if body else []), m.group(1).strip()
        m = re.search(r'=\s*([^\s=]+(?:\s*[^\s=,]*)?)\s*$', text)
        if m:
            return [text], m.group(1).strip()
        items = [s.strip() for s in text.split('\n\n') if s.strip()] or [text]

    # 뒤에서부터 '답 :' 또는 '∴' 로 시작하는 항목을 찾는다
    idx = None
    for i in range(len(items) - 1, -1, -1):
        if ANS.search(items[i]):
            idx = i
            break

    if idx is None:
        # 답 표시가 없는 문항은 구하는 값이 여럿이라 항목마다 답이 붙어 있다
        # (파종량 4종, 부담금 2개 등). 마지막을 잘라내면 답이 사라지므로
        # 전체를 계산으로 두고 각 항목의 최종 수치를 모아 답을 만든다.
        nums = []
        for it in items:
            m = re.findall(r'=\s*([\d,]+(?:\.\d+)?\s*[^\s,)]*)\s*$', it.strip())
            if m:
                label = re.split(r'[=:：]', it.strip())[0].strip()
                label = re.sub(r'\s*\(.*?\)\s*$', '', label)[:20]
                nums.append(f'{label} {m[0]}' if label else m[0])
        if len(nums) >= 2:
            return items, ' / '.join(nums)
        idx = len(items) - 1

    calc = items[:idx]
    ans = items[idx]
    # '계산식 :' 같은 라벨은 본문에 흡수되므로 떼어 준다
    calc = [re.sub(r'^(계산식|식|풀이)\s*[:：]\s*', '', c) for c in calc]
    ans = re.sub(r'^(답|정답)\s*[:：]\s*', '', ans).strip()
    return calc, ans


# 자동 규칙이 중간값을 답으로 잡는 문항은 답을 직접 지정한다
# (year, round, number) → 최종 답
MANUAL = {
    (2024, 1, 10): '20%',
    (2008, 4, 12): '40%',
    (2012, 2, 5): '60종 감소',
    # answer_text 한 덩어리로 저장돼 자동 분리가 어려운 문항들
    (2025, 1, 9): '25,000개체',
    (2025, 2, 9): '0.2',
    (2025, 3, 6): '180%',
    (2024, 1, 4): '7/27 ≒ 0.26',
    (2023, 3, 3): '0.8',
    (2022, 1, 4): '800마리',
    (2017, 3, 1): '0.8',
    (2009, 4, 7): 'R₁ = (S − 1) / ln N',
    (2008, 4, 1): '0.8',
}


def main():
    apply = '--apply' in sys.argv
    n = 0
    for q in Q.objects.filter(source='기출', qtype='계산').order_by('-year', '-round'):
        r = split_answer(q)
        if not r:
            continue
        calc, ans = r
        fixed = MANUAL.get((q.year, q.round, q.number))
        if fixed:
            # 원본 풀이를 그대로 계산 본문으로 쓰고 답만 지정값으로 바꾼다.
            # 답 표시(∴ …)는 중복되므로 떼어 낸다.
            src = [s for s in (q.answer_items or []) if s.strip()]
            if not src:
                body = re.split(r'∴', (q.answer_text or '').strip())[0].strip()
                src = [body] if body else calc
            calc = [NUM.sub('', s).strip() for s in src]
            ans = fixed
        if not calc:                       # 풀이 없이 답만 있는 문항은 그대로
            continue
        new = ['계산\n' + '\n'.join(calc), '답 : ' + ans]
        if q.answer_items == new and not q.answer_text:
            continue
        n += 1
        print(f'  {q.year}-{q.round} #{q.number}')
        if apply:
            q.answer_items = new
            q.answer_text = ''
            q.save(update_fields=['answer_items', 'answer_text'])
    print(f'{"반영" if apply else "대상"} {n}건')
    if not apply:
        print('(--apply 로 반영)')


if __name__ == '__main__':
    main()
