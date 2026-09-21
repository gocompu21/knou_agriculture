# -*- coding: utf-8 -*-
"""자연생태복원기사 실기 작업형 — 연도별 출제 도면과제를 넣는다.

출처는 사용자가 준 `년도별_도면_기출.png`(연도별 출제경향 표, 2013~2026)다.
Claude 가 **직접 읽어** 옮겼다. 표에서 읽은 그대로이며, 고친 것은 하나뿐이다 —
2016-2 의 `폐도록복원` 은 원문 오타라 `폐도로복원` 으로 적었다.

**과제 이름을 분류로 삼는다.** 조경기사는 도면마다 번호(319·444…)가 있지만 이쪽은
없고, 대신 다섯 가지 유형이 돌아가며 나온다. `(변형)` 은 같은 유형의 변주이므로
제목을 나누지 않고 `note` 에 적는다 — 제목을 나누면 출제 빈도가 흩어진다.

    python load_eco_drawings.py            # 무엇이 바뀌는지만 본다
    python load_eco_drawings.py --apply    # DB 에 넣는다

자격증은 **이름으로 찾는다**(로컬 pk 6 · 서버 pk 3).
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import Certification, GisaDrawingTask   # noqa: E402

ROOF = '옥상잠자리 · 벽면녹화 · 우수체계'
POND = '적지분석 · 생태연못'
CORR = '적지분석 · 생태통로'
BIRD = '조류관찰 생태공원'
ROAD = '폐도로복원'
ROAD_CORR = '폐도로복원 · 생태통로'

# (연도, 회차, 과제, 비고)
ROWS = [
    (2013, 1, ROOF, ''), (2013, 2, ROOF, ''), (2013, 3, POND, ''),
    (2014, 1, ROOF, ''), (2014, 2, BIRD, ''), (2014, 3, POND, ''),
    (2015, 1, CORR, '변형'), (2015, 2, POND, ''), (2015, 3, BIRD, ''),
    (2016, 1, POND, ''), (2016, 2, ROAD_CORR, ''), (2016, 3, ROOF, ''),
    (2017, 1, CORR, '변형'), (2017, 2, ROOF, ''), (2017, 3, BIRD, ''),
    (2018, 1, ROOF, ''), (2018, 2, CORR, '변형'), (2018, 3, BIRD, ''),
    (2019, 1, ROAD, ''), (2019, 2, CORR, '변형'), (2019, 3, BIRD, ''),
    (2020, 1, ROOF, ''), (2020, 2, POND, ''), (2020, 3, CORR, '변형'),
    (2020, 4, BIRD, '4·5회 공통'),
    (2021, 1, ROAD, ''), (2021, 2, ROOF, ''), (2021, 3, POND, ''),
    (2022, 1, CORR, ''), (2022, 2, BIRD, ''), (2022, 3, ROAD, ''),
    (2023, 1, ROOF, '옥상잠자리 변형'), (2023, 2, POND, ''), (2023, 3, CORR, ''),
    (2024, 1, BIRD, ''), (2024, 2, ROAD, ''), (2024, 3, CORR, ''),
    (2025, 1, ROOF, ''), (2025, 2, POND, ''),
    # 표에서 붉은 글씨로 덧쓰여 있던 칸 — 회색으로 깔려 있던 예상과 다르게 나왔다는 뜻으로 읽었다
    (2025, 3, ROAD, '표에 붉게 덧쓰임 (회색 예상은 적지분석·생태통로였다)'),
    (2026, 1, BIRD, '표에 붉게 덧쓰임'),
    (2026, 2, ROAD, '표에 회색으로만 적혀 있음'),
]


def main():
    apply = '--apply' in sys.argv
    cert = Certification.objects.filter(name='자연생태복원기사').first()
    if not cert:
        print('자연생태복원기사 자격증이 없습니다.')
        return 1
    print(f'자격증 pk={cert.pk}')

    made = same = changed = 0
    for year, rnd, title, note in ROWS:
        obj = GisaDrawingTask.objects.filter(
            certification=cert, year=year, round=rnd).first()
        if obj is None:
            made += 1
            print(f'  + {year}-{rnd}회  {title}{"  (" + note + ")" if note else ""}')
            if apply:
                GisaDrawingTask.objects.create(
                    certification=cert, year=year, round=rnd, title=title, note=note)
        elif (obj.title, obj.note) != (title, note):
            changed += 1
            print(f'  ~ {year}-{rnd}회  {obj.title} → {title}')
            if apply:
                obj.title, obj.note = title, note
                obj.save(update_fields=['title', 'note'])
        else:
            same += 1

    print(f'\n새로 {made} · 고침 {changed} · 그대로 {same}'
          f'{"" if apply else "   (--apply 를 붙여야 저장됩니다)"}')
    if apply:
        n = GisaDrawingTask.objects.filter(certification=cert).count()
        print(f'지금 {cert.name} 도면과제 {n}건')
    return 0


if __name__ == '__main__':
    sys.exit(main())
