"""교수 메모가 없던 잡초 카드에 짧은 메모를 넣는다.

메모는 **사진 위에 흰 글씨로 겹쳐** 보이므로 12자 안팎의 구(句)여야 한다.
`_weed_memo_new.json` 의 내용은 각 카드의 식별 포인트를 읽고 사진으로 바로
확인되는 것만 골라 손으로 썼다(AI 일괄 생성이 아니다).

  python load_weed_memo.py            # 무엇이 들어갈지 보여만 준다
  python load_weed_memo.py --apply    # 실제로 넣는다

이미 메모가 있는 카드는 건드리지 않는다.
"""
import json
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from exam.models import WeedCard

APPLY = '--apply' in sys.argv
SUBJECT = 51

data = json.load(open('_weed_memo_new.json', encoding='utf-8'))
memos = {k: v for k, v in data.items() if not k.startswith('_')}

done = skip = miss = 0
for name, lines in memos.items():
    card = WeedCard.objects.filter(subject_id=SUBJECT, name=name).first()
    if not card:
        print(f'  {name:12s} 카드 없음')
        miss += 1
        continue
    if card.notes.strip():
        print(f'  {name:12s} 이미 메모가 있어 건너뜀')
        skip += 1
        continue
    text = '\n'.join(lines)
    print(f'  {card.card_no:3d} {name:12s} {" / ".join(lines)}')
    if APPLY:
        card.notes = text
        card.save(update_fields=['notes'])
    done += 1

print(f'\n{done}종 대상 / {skip}종 건너뜀 / {miss}종 카드 없음'
      + ('  — 넣었다' if APPLY else '  — 실제로 넣으려면 --apply'))
