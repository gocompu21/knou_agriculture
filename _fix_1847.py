# -*- coding: utf-8 -*-
"""식물보호기사 2012-2 #47 해설 복구.

낱자 단위로 흩어져 있어(형 태 적, 생 태 적) 기계적 재조립이 불가능했다.
공백을 모두 제거하면 원문이 온전히 남으므로, 그 내용을 그대로 두고
어절 경계만 되살려 다시 적었다. 내용은 추가·변경하지 않았다.
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

FIX = {
    "explanation": (
        "형질(trait)은 생물이 가지고 있는 형태적, 생태적, 생리적 특성 그 자체를 "
        "의미합니다. 숙기나 출수기는 작물의 생육 시기를 나타내는 생태적 형질에 "
        "해당합니다. 반면, 단간종, 조생종, 만생종은 이러한 형질의 발현 정도에 "
        "따라 구분된 품종의 명칭입니다."
    ),
    "choice_1_exp": (
        "단간종은 '간장(줄기의 길이)'이라는 형질이 짧은 특성을 가진 품종을 "
        "일컫는 용어입니다."
    ),
    "choice_2_exp": (
        "만생종은 '숙기(성숙기)'라는 형질이 늦은 특성을 가진 품종을 "
        "일컫는 용어입니다."
    ),
    "choice_3_exp": (
        "조생종은 '숙기(성숙기)'라는 형질이 빠른 특성을 가진 품종을 "
        "일컫는 용어입니다."
    ),
    "choice_4_exp": (
        "형질(trait)은 생물이 가지고 있는 형태적, 생태적, 생리적 특성 그 자체를 "
        "의미합니다. 숙기나 출수기는 작물의 생육 시기를 나타내는 생태적 형질에 "
        "해당합니다. 반면, 단간종, 조생종, 만생종은 이러한 형질의 "
        "발현 정도에 따라 구분된 품종의 명칭입니다."
    ),
}

apply = "--apply" in sys.argv
q = GisaQuestion.objects.get(pk=1847)

# 안전 확인: 공백 제거 후 내용이 같은지 대조 (내용을 바꾸지 않았는지)
for f, new in FIX.items():
    old = (getattr(q, f) or "").replace(" ", "")
    same = old == new.replace(" ", "")
    print("[%s] 내용 동일: %s" % (f, same))
    if not same:
        print("   전: %s" % old[:70])
        print("   후: %s" % new.replace(" ", "")[:70])

if apply:
    for f, new in FIX.items():
        setattr(q, f, new)
    q.save(update_fields=list(FIX))
    print()
    print("반영 완료")
else:
    print()
    print("확인만 (--apply 로 반영)")
