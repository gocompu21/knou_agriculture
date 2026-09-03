# -*- coding: utf-8 -*-
"""2024-2 계산 문항의 'ln=1.609' 오식을 정정한다.

밑수가 빠진 표기다. 값 1.609는 ln5(1.6094)이고, 같은 주제의 2015-1 문제도
ln2·ln3과 함께 ln5를 제시하므로 ln5=1.609가 맞다.
pk 가 로컬 6 / 서버 3 으로 달라 회차로 찾는다.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

NOTE = ("원문 'ln=1.609'는 밑수 누락 오식 — 값이 ln5(1.6094)이고 같은 주제의 "
        "2015-1 문제도 ln5를 함께 제시하므로 ln5=1.609로 정정(2026-09-03)")


def main():
    q = Q.objects.filter(source='기출', year=2024, round=2,
                         number=2, qtype='계산').first()
    if not q:
        print('대상 문항 없음')
        return
    if 'ln=1.609' not in q.text:
        print('이미 정정됨:', q.text[-30:])
        return
    q.text = q.text.replace('ln=1.609', 'ln5=1.609')
    q.notes = ((q.notes or '') + ' / ' + NOTE).strip(' /')
    q.save(update_fields=['text', 'notes'])
    print('정정:', q.text[-30:])


if __name__ == '__main__':
    main()
