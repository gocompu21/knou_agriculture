"""잡초 동정 카드를 한 장 새로 넣는다 (교수 카드 PDF 밖의 종).

PDF 122종 말고 따로 넣고 싶은 잡초가 생길 때 쓴다. 사진은 미리
media/weeds/s51/ 에 두고 파일명을 CARD 에 적는다.

  python add_weed_card.py            # 확인만
  python add_weed_card.py --apply    # DB 반영
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.conf import settings  # noqa: E402

from exam.models import WeedCard  # noqa: E402

SUBJECT_PK = 51

CARD = {
    'card_no': 143,
    'order': 123,
    'name': '털물참새피',
    'family': '벼과(화본과)',
    'life_form': '다년생',
    'habitat': '하천·수로·논둑·저수지 가장자리',
    'features': (
        '꽃대 끝에서 이삭 두 개가 V자로 갈라져 마주 서는 것이 한눈에 들어온다. '
        '이삭 한쪽에만 씨가 두 줄로 촘촘히 붙고 꽃필 때 검은 꽃밥이 매달린다. '
        '물가를 기며 마디마다 뿌리를 내려 매트처럼 덮고, 줄기 마디와 잎집에 흰 털이 '
        '빽빽해 만지면 까끌하다.'
    ),
    'similar': (
        '물참새피는 마디와 잎집에 털이 거의 없어 매끈하다. 털 유무가 가장 확실한 구별점이다. '
        '나도겨풀도 물가를 기지만 이삭이 V자로 갈라지지 않고 원추꽃차례로 퍼진다.'
    ),
    'control': (
        '생태계교란 생물로 지정된 외래잡초다. 마디마다 뿌리를 내려 줄기 조각 하나로도 번지므로 '
        '예초하면 오히려 퍼진다. 물길을 막고 논둑을 무너뜨려 피해가 크다. 뿌리째 걷어내 '
        '말려 없애고, 물이 없는 곳은 글리포세이트를 처리한다.'
    ),
    'notes': '',           # 교수 슬라이드가 없는 종이라 메모는 비운다
    'exam_count': 0,
    'q_image': 'weeds/s51/q143.jpg',
    'a_image': '',
    'sketch_image': '',
}


def main():
    apply = '--apply' in sys.argv
    exist = WeedCard.objects.filter(subject_id=SUBJECT_PK, name=CARD['name']).first()
    if exist:
        print('이미 있음: 카드 %d %s' % (exist.card_no, exist.name))
        return
    clash = WeedCard.objects.filter(subject_id=SUBJECT_PK, card_no=CARD['card_no']).first()
    if clash:
        print('카드 번호 %d 는 이미 %s 가 쓰고 있다' % (clash.card_no, clash.name))
        return

    for f in ('q_image', 'a_image', 'sketch_image'):
        rel = CARD[f]
        if rel and not os.path.exists(os.path.join(settings.MEDIA_ROOT, rel)):
            print('사진이 없다:', rel)
            return

    print('넣을 카드')
    for k, v in CARD.items():
        print('  %-12s %s' % (k, (v[:70] + '…') if isinstance(v, str) and len(v) > 70 else v))
    if not apply:
        print('\n--apply 를 붙이면 DB 에 넣는다.')
        return

    WeedCard.objects.create(subject_id=SUBJECT_PK, **CARD)
    print('\n넣었다. 이제 카드 %d 종' % WeedCard.objects.filter(subject_id=SUBJECT_PK).count())


main()
