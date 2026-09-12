# -*- coding: utf-8 -*-
"""조경(산업)기사 실기 계산 답을 자연생태복원 실기와 같은 형식으로 바꾼다.

자연생태복원 실기는 계산 문항의 답을 answer_items 두 항목으로 나눠 둔다.

    항목 1  계산)
            <풀이 방향 한두 줄>
            [eq]<식> = <대입> = **<결과>**[/eq]
    항목 2  답) <최종 답만 짧게>

이렇게 두면 화면에서 과정과 답이 갈려 보이고, 채점도 항목마다 점수가 붙는다.
조경 실기는 answer_text 에 통짜로 들어가 있어 같은 꼴로 맞춘다.

'답)' 문구는 문제가 무엇을 물었는지 보고 사람이 정한다 — 마지막 식의 값을 기계로
뽑으면 중간값(예: 삽날 용량)이 답으로 올라간다. 2023-1 7번이 그렇다:
①2.56m³ 를 거쳐 계산하지만 묻는 것은 ②사이클시간과 ③시간당 작업량이다.

  python ls_calc_to_items.py           # 바뀔 문항만 보여 준다
  python ls_calc_to_items.py --apply
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

GI, SI = '조경기사', '조경산업기사'

# (자격증, 연도, 회차, 번호) → 답) 에 쓸 문구
FINAL = {
    (GI, 2023, 1, 5): '트럭 운반연대수 185대',
    (GI, 2023, 1, 7): '1회 사이클시간 2.2분, 시간당 작업량 32.64m³/hr',
    (GI, 2023, 1, 10): '절토량 4.8m³',
    (GI, 2023, 2, 6): '시간당 작업량 7.2m³/hr',
    (GI, 2023, 2, 7): '최대 시 이용자수 1,471인',
    (GI, 2023, 4, 2): '시간당 작업량 40.32m³/hr',
    (GI, 2023, 4, 9): '각재 정미량 2.16m³·소요량 2.27m³, 판재 정미량 0.90m³·소요량 0.99m³',
    (GI, 2024, 1, 3): '운반비 95,555원',
    (GI, 2024, 1, 5): '독립기초 터파기양 1.79m³',
    (GI, 2024, 2, 4): '자연석 총 중량 352.45ton',
    (GI, 2024, 2, 5): '덤프트럭 소요대수 380대, 성토량 1,340m³',
    (GI, 2024, 3, 11): '덤프트럭 총 소요대수 2,500대',
    (GI, 2024, 3, 12): '접선장 96.87m, 곡선장 153.90m',
    (GI, 2025, 1, 1): '각관 정미량 2.44t·총소요량 2.56t, 강관 정미량 2.97t·총소요량 3.12t',
    (GI, 2025, 1, 2): '완성된 야장',          # 표가 곧 답이라 아래에 표를 붙인다
    (GI, 2025, 1, 11): '최대시이용자수 6,666명',
    (GI, 2025, 2, 6): '1일 운반량 6.38m³',
    (GI, 2025, 2, 8): '잔디 식재매수 45,728장',
    (GI, 2025, 2, 9): '주차장 필요면적 3,600m²',
    (GI, 2025, 3, 4): '우수유출량 16m³/sec',
    (GI, 2025, 3, 7): '운반비 260,000원',
    (SI, 2022, 4, 2): '1회 사이클시간 2.21분, 시간당 작업량 26.06m³/hr',
    (SI, 2022, 4, 8): '㉠ 1.1주, ㉡ 0.0015인, ㉢ 0.0008인',
    (SI, 2022, 4, 10): 'V = L/6 × (A₁ + 4A_m + A₂)',     # 공식 자체를 묻는 문항
    (SI, 2023, 1, 1): '절토량 1,000m³',
    (SI, 2023, 1, 9): '총공사원가 130,866,000원',
    (SI, 2023, 1, 10): '유효흡수율 25%',
    (SI, 2023, 2, 1): '실제면적 100ha',
    (SI, 2023, 2, 5): '시간당 작업량 104.91m³/hr',
    (SI, 2023, 2, 8): '총 수목량 280주',
    (SI, 2023, 4, 4): '헤드열 사이의 간격 2.78m',
    (SI, 2023, 4, 7): '㉠ 1.1주, ㉡ 0.01인, ㉢ 0.003인',
    (SI, 2023, 4, 8): '토량 17.67m³',
}

_EQ = re.compile(r'\[eq\](.*?)\[/eq\]', re.DOTALL)
_LAST = re.compile(r'(=\s*)([^=\n]+)$')


def bold_result(eq_body):
    """[eq] 블록 마지막 줄의 마지막 '= 값' 을 볼드로 — 결과가 한눈에 들어온다."""
    lines = eq_body.rstrip().split('\n')
    for i in range(len(lines) - 1, -1, -1):
        if '=' in lines[i]:
            lines[i] = _LAST.sub(lambda m: f'{m.group(1)}**{m.group(2).strip()}**', lines[i])
            break
    return '\n'.join(lines)


def split_table(text):
    """본문 끝에 붙은 마크다운 표를 떼어 낸다 → (본문, 표 또는 '').

    야장 채우기처럼 '완성된 표'가 곧 답인 문항이 있다. 표를 풀이 쪽에 남기면
    답 항목이 '10.0 / 9.9 / …' 같은 숫자 나열이 되어 무엇을 채운 것인지 안 보인다.
    """
    lines = text.rstrip().split('\n')
    i = len(lines)
    while i and (lines[i - 1].lstrip().startswith('|') or not lines[i - 1].strip()):
        i -= 1
    table = '\n'.join(lines[i:]).strip()
    if table.startswith('|'):
        return '\n'.join(lines[:i]).rstrip(), table
    return text.rstrip(), ''


def convert(q):
    """answer_text → answer_items 두 항목. 바꿀 게 없으면 None."""
    text = (q.answer_text or '').strip()
    if not text or q.answer_items:
        return None
    key = (q.certification.name, q.year, q.round, q.number)
    if key not in FINAL:
        return None
    body, table = split_table(text)
    if not table:
        # 표가 답인 문항은 볼드를 넣지 않는다 — 마지막 식의 값은 표를 채우는
        # 중간 단계일 뿐이라 강조하면 그것이 답처럼 보인다.
        body = _EQ.sub(lambda m: '[eq]' + bold_result(m.group(1)) + '[/eq]', body)
    answer = '답) ' + FINAL[key] + ('\n' + table if table else '')
    return ['계산)\n' + body, answer]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--show', type=int, default=0)
    args = ap.parse_args()

    qs = list(GisaEssayQuestion.objects.filter(certification__name__startswith='조경')
              .select_related('certification')
              .order_by('certification__name', 'year', 'round', 'number'))
    n, shown = 0, 0
    for q in qs:
        items = convert(q)
        if not items:
            continue
        n += 1
        tag = f'{q.certification.name} {q.year}-{q.round} {q.number}번'
        if shown < args.show:
            shown += 1
            print(f'\n── {tag}')
            for it in items:
                print(it)
        else:
            print(f'  {"바꿈" if args.apply else "바꿀 것"}: {tag} → {items[1].splitlines()[0]}')
        if args.apply:
            q.answer_items = items
            q.answer_text = ''
            q.save(update_fields=['answer_items', 'answer_text'])

    missed = [f'{q.certification.name} {q.year}-{q.round} {q.number}번' for q in qs
              if (q.answer_text or '').strip() and '[eq]' in (q.answer_text or '')
              and (q.certification.name, q.year, q.round, q.number) not in FINAL]
    if missed:
        print('\n!! 답) 문구를 안 정한 문항:', ', '.join(missed))
    print(f'\n{n}건' + (' 반영했다.' if args.apply else ' (미반영 — --apply 로 넣는다)'))


if __name__ == '__main__':
    main()
