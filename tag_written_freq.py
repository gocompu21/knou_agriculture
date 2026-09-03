# -*- coding: utf-8 -*-
"""실기 필답 문항 주제어의 필기 등장 횟수를 계산해 written_freq 에 저장한다.

실기에 1회만 나온 주제라도 필기에서 수십 번 다뤄졌다면 재출제 유력 후보다
(최근 3개 회차 신규 주제 역검증에서 81%가 필기 빈출 영역 출신).
"재출제 유력" 학습 모드가 이 값으로 문항을 고른다.

주제어는 답의 머리말에서 뽑는다 — 단답·빈칸형은 답 자체가 주제어라 정확하고,
'정의·개념' 같은 라벨이나 숫자·일반어가 걸리면 측정 불능으로 0을 남긴다.
서버에도 같은 데이터가 있으므로 배포 파일 없이 서버에서 직접 실행하면 된다.
"""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import Certification, GisaEssayQuestion as EQ, GisaQuestion as MQ

CERT = '자연생태복원기사'

# 답의 라벨(주제어가 아님)과 일반어
LABEL = set('정의 개념 특징 목적 기능 종류 방법 이유 장점 단점 답 계산식 공식 '
            '명칭 순서 구분 내용 원인 효과 사례 요건 기준 절차 대상'.split())


def head(q):
    a = (q.answer_items or [None])[0] or q.answer_text or ''
    a = re.sub(r'^[①-⑮㉠-㉦\s]+', '', a)
    a = re.split(r'[:：(（/·,]', a)[0].strip()
    a = re.sub(r'(이다|입니다|한다)\.?$', '', a).strip()
    if a in LABEL or not (2 <= len(a) <= 14):
        return None
    if re.fullmatch(r'[\d\s.%-]+', a):        # 숫자만인 답은 주제어가 아니다
        return None
    return a if re.fullmatch(r'[가-힣A-Za-z0-9\s-]+', a) else None


def main():
    cert = Certification.objects.get(name=CERT)
    mtxt = [' '.join([q.text or '', q.choice_1 or '', q.choice_2 or '',
                      q.choice_3 or '', q.choice_4 or ''])
            for q in MQ.objects.filter(exam__certification=cert)
                               .only('text', 'choice_1', 'choice_2',
                                     'choice_3', 'choice_4')]

    def df(k):
        return sum(1 for t in mtxt if k in t)

    tagged = skipped = 0
    for q in EQ.objects.filter(source='기출'):
        h = head(q)
        val = 0
        if h:
            # 일반어(필기 100문항 초과 등장)는 변별력이 없어 세지 않는다.
            # 여러 단어면 가장 긴 토큰으로도 시도한다.
            for c in [h] + sorted((w for w in h.split() if len(w) >= 2),
                                  key=len, reverse=True):
                if c in LABEL or re.fullmatch(r'[\d\s.%-]+', c):
                    continue
                d = df(c)
                if d <= 100:
                    val = d
                    break
        if q.written_freq != val:
            q.written_freq = val
            q.save(update_fields=['written_freq'])
            tagged += 1
        else:
            skipped += 1

    n10 = EQ.objects.filter(source='기출', freq_rounds=1,
                            written_freq__gte=10).count()
    print(f'갱신 {tagged} / 동일 {skipped}')
    print(f'재출제 유력(실기 1회 + 필기 10회 이상): {n10}문항')


if __name__ == '__main__':
    main()
