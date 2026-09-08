"""잡초 카드에서 빠져 있던 교수 메모를 채운다.

처음 카드를 옮길 때 메모 상자가 사진 오른쪽에 따로 떨어져 있는 카드 몇 장을
놓쳤다. 슬라이드 글자 층과 대조해 찾았고, 고들빼기의 부제는 글자 층이 아니라
제목 이미지에 박혀 있어 눈으로 읽어 넣었다.

  python fix_weed_notes_missing.py            # 확인만
  python fix_weed_notes_missing.py --apply    # DB 반영
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from exam.models import WeedCard  # noqa: E402

SUBJECT_PK = 51

# 카드번호: 메모 줄 목록 (기존 메모가 있으면 앞에 붙인다)
ADD = {
    49:  ['군락을 이룬것을 보면 올방개보다는 신장이 작으며 강아지풀처럼 변한다.'],
    55:  ['잎 모양이 차이난다.'],
    59:  ['(비교) 돌콩과 잎의 모양으로 구분'],
    92:  ['잎이 가로는 좁고 세로는 길다.'],
    110: ['타원형 잎', '무질서 속의 질서'],
    # 제목 아래 부제(이미지에 박혀 있음)와 사진 옆 메모 상자, 둘 다 슬라이드에 있다
    117: ['꽃 수술이 꽃잎 색과 같다.', '꽃잎과 꽃술이 노란색이다'],
}


def main():
    apply = '--apply' in sys.argv
    n = 0
    for card_no, lines in sorted(ADD.items()):
        c = WeedCard.objects.get(subject_id=SUBJECT_PK, card_no=card_no)
        have = [x.strip() for x in c.notes.split('\n') if x.strip()]
        new = [x for x in lines if x not in have]
        if not new:
            print(f'  {card_no:4d} {c.name:12s} 이미 있음')
            continue
        merged = new + have
        print(f'  {card_no:4d} {c.name:12s} + {new}')
        n += 1
        if apply:
            c.notes = '\n'.join(merged)
            c.save(update_fields=['notes'])
    print(f'\n{n}개 카드', '반영함' if apply else '(--apply 로 반영)')


main()
