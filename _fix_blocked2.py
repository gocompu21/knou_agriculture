# -*- coding: utf-8 -*-
"""동기화에서 차단된 2건 처리.

2021-2-99  서버 값이 이미 목표와 동일 — 조치 불필요 (stale before 때문에 차단됐을 뿐)
2021-3-70  서버가 '도시 전체', 목표는 '토지 전체'.
           문항은 '포괄적 지도화'(전 지역 빠짐없이 조사)를 묻고 정답이 이 선지다.
           개념상 '토지 전체'가 맞다.
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

apply = "--apply" in sys.argv
q = GisaQuestion.objects.filter(
    exam__certification__name="자연생태복원기사",
    exam__year=2021, exam__round=3, number=70).first()
cur = q.choice_2 or ""
if cur.startswith("도시 전체"):
    new = "토지" + cur[2:]
    print("2021-3-70 보기2")
    print("  전:", cur[:44])
    print("  후:", new[:44])
    if apply:
        q.choice_2 = new
        q.save(update_fields=["choice_2"])
        print("  → 반영")
elif cur.startswith("토지 전체"):
    print("2021-3-70 이미 '토지 전체' — 조치 불필요")
else:
    print("2021-3-70 예상 밖의 값:", repr(cur[:44]))

q2 = GisaQuestion.objects.filter(
    exam__certification__name="자연생태복원기사",
    exam__year=2021, exam__round=2, number=99).first()
print()
print("2021-2-99 '지 형도' 잔존:", "지 형도" in (q2.text or ""))
