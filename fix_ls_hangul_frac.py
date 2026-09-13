# -*- coding: utf-8 -*-
"""한글 항이 든 나눗셈을 세로 분수([frac])로 고친다.

[eq] 안의 `a / b` 는 자동으로 세로 분수가 되지만, **한글 항은 일부러 건드리지
않는다** — `480kg/일`·`14주/m²` 처럼 단위 표기에 쓰인 `/` 까지 분수로 만들면
안 되고, 띄어쓰기가 있는 한글 항은 어디까지가 분자인지 기계가 가를 수 없다.
그래서 한글 분수는 `[frac]분자|분모[/frac]` 로 손수 적어 둔다.

같은 수식 안에서 숫자 분수만 세로로 쌓이고 한글 분수는 한 줄로 남아 보기
사나웠다(조경산업기사 2023-2 1번: `(1/50,000)² = 4 / 실제면적`).

  python fix_ls_hangul_frac.py           # 검증만
  python fix_ls_hangul_frac.py --apply   # DB 반영
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

from gisa.models import GisaEssayQuestion  # noqa: E402

# (자격증, source, year, round, number) → [(찾을 것, 바꿀 것), …]
# 분수 막대가 묶어 주므로 분자를 감싸던 괄호는 뗀다.
FIX = {
    ('조경기사', '기출', 2025, 3, 7): [
        ('총운반량 / 1인 1회 운반량', '[frac]총운반량|1인 1회 운반량[/frac]'),
    ],
    ('조경기사', '기출', 2024, 1, 3): [
        ('총운반량 / 1인 1회 운반량', '[frac]총운반량|1인 1회 운반량[/frac]'),
    ],
    ('조경산업기사', '기출', 2023, 1, 10): [
        ('(표건상태중량 − 기건상태중량) / 절건상태중량',
         '[frac]표건상태중량 − 기건상태중량|절건상태중량[/frac]'),
    ],
    ('조경기사', '적산', None, None, 22): [
        ('초점거리 / (촬영고도 − 표고)', '[frac]초점거리|촬영고도 − 표고[/frac]'),
    ],
    ('조경기사', '적산', None, None, 35): [
        ('수직거리 / 수평거리', '[frac]수직거리|수평거리[/frac]'),
        ('수직거리 / 5', '[frac]수직거리|5[/frac]'),
    ],
    ('조경기사', '적산', None, None, 51): [
        ('초점거리(f) / 고도(H)', '[frac]초점거리(f)|고도(H)[/frac]'),
    ],
    ('조경기사', '적산', None, None, 65): [
        ('단위수량/1,000', '[frac]단위수량|1,000[/frac]'),
        ('단위시멘트양/(시멘트비중 × 1,000)',
         '[frac]단위시멘트양|시멘트비중 × 1,000[/frac]'),
        ('공기량/100', '[frac]공기량|100[/frac]'),
    ],
    ('조경기사', '적산', None, None, 66): [
        ('총 운반량 / 1인당 1회 운반량', '[frac]총 운반량|1인당 1회 운반량[/frac]'),
    ],
    ('조경기사', '적산', None, None, 73): [
        ('(습윤상태 − 절건상태) / 절건상태',
         '[frac]습윤상태 − 절건상태|절건상태[/frac]'),
        ('(습윤상태 − 표면건조 내부포수상태) / 표면건조 내부포수상태',
         '[frac]습윤상태 − 표면건조 내부포수상태|표면건조 내부포수상태[/frac]'),
        ('(표면건조 내부포수상태 − 절건상태) / 절건상태',
         '[frac]표면건조 내부포수상태 − 절건상태|절건상태[/frac]'),
        ('(표면건조 내부포수상태 − 기건상태) / 절건상태',
         '[frac]표면건조 내부포수상태 − 기건상태|절건상태[/frac]'),
    ],
    ('조경기사', '적산', None, None, 74): [
        ('측량면적 / (B × C)', '[frac]측량면적|B × C[/frac]'),
    ],
    ('조경기사', '적산', None, None, 76): [
        ('공사량 / 1일 작업량', '[frac]공사량|1일 작업량[/frac]'),
    ],
}


def main():
    apply_ = '--apply' in sys.argv
    hit = miss = 0
    for (cert, src, y, r, n), pairs in FIX.items():
        q = GisaEssayQuestion.objects.filter(
            certification__name=cert, source=src, year=y, round=r, number=n).first()
        if not q:
            print(f'  !! 문항 없음: {cert} {src} {y}-{r} {n}번')
            miss += 1
            continue
        items, changed = list(q.answer_items or []), []
        for old, new in pairs:
            found = False
            for i, a in enumerate(items):
                if old in a:
                    items[i] = a.replace(old, new)
                    found = True
            if found:
                hit += 1
                changed.append(old)
            else:
                miss += 1
                print(f'  !! 못 찾음: {cert} {src} {y}-{r} {n}번 | {old}')
        if changed:
            print(f'  {cert} {src} {y}-{r} {n}번 — {len(changed)}곳')
            for c in changed:
                print(f'      {c}')
            if apply_:
                q.answer_items = items
                q.save(update_fields=['answer_items'])

    print(f'\n{hit}곳 고침, {miss}곳 실패'
          + (' — 반영했다.' if apply_ else ' (미반영 — --apply 로 넣는다)'))
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
