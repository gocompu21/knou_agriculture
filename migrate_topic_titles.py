# -*- coding: utf-8 -*-
"""쪽집게 노트 주제 제목 파일의 키에 자격증을 붙인다(한 번만 돌리는 스크립트).

키가 대표 문항의 "연도-회차-번호"뿐이라 **자격증이 다르면 충돌한다.**
식물보호를 붙이자마자 드러났다 — 식물보호기사 2023-1회 1번 주제에
자연생태복원의 "도시생태계 왜곡의 원인"이 제목으로 달렸다. 2023-1-1 이
두 자격증에 모두 있기 때문이다.

그래서 키를 `자격증|연도-회차-번호` 로 바꾼다. 기존 키는 모두
자연생태복원기사 것이므로 앞머리만 붙이면 된다.

  python migrate_topic_titles.py            # 바뀔 내용만 보여 준다
  python migrate_topic_titles.py --apply    # 파일을 고친다
"""
import io
import json
import os
import sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding='utf-8')

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'gisa', 'essay_topic_titles.json')
OWNER = '자연생태복원기사'


def main():
    apply_ = '--apply' in sys.argv
    data = json.load(io.open(PATH, encoding='utf-8'), object_pairs_hook=OrderedDict)

    out, moved, kept = OrderedDict(), 0, 0
    for k, v in data.items():
        if k.startswith('_'):
            out[k] = v
            continue
        if '|' in k:
            out[k] = v
            kept += 1
            continue
        out['%s|%s' % (OWNER, k)] = v
        moved += 1

    out['_comment'] = (
        '실기 쪽집게 노트 주제 제목. 키는 "자격증|대표 문항의 연도-회차-번호"다. '
        '자격증을 앞에 붙이는 까닭은 연도-회차-번호만으로는 자격증끼리 충돌하기 '
        '때문이다(식물보호기사 2023-1회 1번에 자연생태복원 제목이 달린 적이 있다). '
        '정리 자료(freq58·calc)가 없는 주제는 발문에서 제목을 규칙으로 뽑는데 '
        "'문제의 부분집합'이 되기 쉬워, 문제가 묻는 뜻을 제목으로 직접 적어 둔다. "
        '여기 있으면 규칙보다 우선.')

    print('자격증을 붙인 키 %d개 · 이미 붙어 있던 키 %d개' % (moved, kept))
    if not apply_:
        for k in list(out)[1:4]:
            print('  예) %s' % k)
        print('(--apply 를 붙여야 파일을 고친다)')
        return 0
    io.open(PATH, 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('고쳤다: %s' % PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
