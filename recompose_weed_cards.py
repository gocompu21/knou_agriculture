"""등록 기능으로 만든 잡초 카드 사진을 새 합성 방식으로 다시 붙인다.

합성은 등록할 때 한 번만 하므로, 여백을 줄이는 수정 전에 만든 카드는
그대로 벌어져 있다. 이 스크립트가 낱장을 잘라내 다시 붙인다.

배열은 낱장 좌표에서 되짚는다(가로로 나뉘었는지 세로로 나뉘었는지).
  python recompose_weed_cards.py            # 무엇을 고칠지 보여만 준다
  python recompose_weed_cards.py --apply    # 실제로 고친다
"""
import io
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files.base import ContentFile
from PIL import Image

from exam.models import WeedCard
from main.views import _weed_compose, _weed_photo_boxes

APPLY = '--apply' in sys.argv
FROM_NO = 144          # 등록 기능으로 만든 첫 카드

# 낱장 가르기가 헷갈리는 카드는 배열을 직접 일러 준다.
# 양미역취의 잎 표본 사진은 배경이 희어 잎 세 장으로 잘게 갈린다
FORCE = {'양미역취': ('1t2b', 3)}


def guess_layout(boxes, size):
    """낱장 좌표로 배열을 되짚는다."""
    w, h = size
    n = len(boxes)
    if n == 1:
        return '1'
    rows = sorted({b[1] for b in boxes})
    cols = sorted({b[0] for b in boxes})
    if n == 2:
        return '1t1b' if len(rows) == 2 else None      # 좌우 2칸 배열은 없다
    if n == 3:
        if len(rows) == 2 and len(cols) == 2:
            # 위가 한 장이면 상1·하2, 왼쪽이 한 장이면 좌1·우2
            top = [b for b in boxes if b[1] == rows[0]]
            return '1t2b' if len(top) == 1 else '1l2r'
        return None
    if n == 4:
        return '2t2b' if len(rows) == 2 else None
    return None


def order_for(layout, boxes):
    """서버 _WEED_LAYOUTS 의 칸 차례대로 낱장을 늘어놓는다."""
    if layout in ('1', '1t1b', '1t2b', '2t2b'):
        return sorted(boxes, key=lambda b: (b[1], b[0]))       # 위→아래, 왼→오른
    if layout == '1l2r':
        left = sorted([b for b in boxes if b[0] == min(x[0] for x in boxes)],
                      key=lambda b: b[1])
        right = sorted([b for b in boxes if b not in left], key=lambda b: b[1])
        return left[:1] + right
    if layout == '2l2r':
        cols = sorted({b[0] for b in boxes})
        left = sorted([b for b in boxes if b[0] == cols[0]], key=lambda b: b[1])
        right = sorted([b for b in boxes if b[0] != cols[0]], key=lambda b: b[1])
        return left + right
    return sorted(boxes, key=lambda b: (b[1], b[0]))


done = skip = 0
for card in WeedCard.objects.filter(subject_id=51, card_no__gte=FROM_NO).order_by('card_no'):
    if not card.q_image:
        continue
    path = card.q_image.path
    im = Image.open(path).convert('RGB')
    boxes = _weed_photo_boxes(path)

    if card.name in FORCE:
        # 잘게 갈린 것을 사람이 일러 준 칸 수로 묶는다 — 가까이 붙은 것끼리 합친다
        _, want = FORCE[card.name]
        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        while len(boxes) > want:
            # 세로로 가장 가까운 두 낱장을 하나로 합친다
            best, gapmin = None, None
            for i in range(len(boxes) - 1):
                a, c = boxes[i], boxes[i + 1]
                if abs(a[0] - c[0]) > 40:          # 다른 열이면 합치지 않는다
                    continue
                d = c[1] - a[3]
                if gapmin is None or d < gapmin:
                    best, gapmin = i, d
            if best is None:
                break
            a, c = boxes[best], boxes[best + 1]
            boxes[best:best + 2] = [[min(a[0], c[0]), min(a[1], c[1]),
                                     max(a[2], c[2]), max(a[3], c[3])]]
    layout = FORCE[card.name][0] if card.name in FORCE else guess_layout(boxes, im.size)
    if not layout:
        print(f'  {card.card_no} {card.name:12s} 낱장 {len(boxes)} — 배열을 알 수 없어 건너뜀')
        skip += 1
        continue

    parts = []
    for b in order_for(layout, boxes):
        buf = io.BytesIO()
        im.crop(tuple(b)).save(buf, format='JPEG', quality=95)
        buf.seek(0)
        parts.append(buf)

    new = _weed_compose(parts, layout)
    print(f'  {card.card_no} {card.name:12s} {layout:5s} {im.size} -> {new.size}', end='')
    if APPLY:
        out = io.BytesIO()
        new.save(out, format='JPEG', quality=92)
        card.q_image.save(os.path.basename(path), ContentFile(out.getvalue()), save=True)
        print('  고침')
    else:
        print('  (미적용)')
    done += 1

print(f'\n{done}장 대상 / {skip}장 건너뜀' + ('' if APPLY else '  — 실제로 고치려면 --apply'))
