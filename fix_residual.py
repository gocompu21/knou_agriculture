# -*- coding: utf-8 -*-
"""PDF 대조 검증 중 새로 발견된 잔존 오류.

2016-2-85 choice_3  '당해 지경' -> '당해 지역'
    같은 문항 ②가 '당해 지역', ④가 '당해 행위'로 동일 구문을 쓴다.
    '지경'은 이 자리에 올 수 없다. PDF 원본에도 '지경'으로 인쇄돼 있으나
    comcbt 계통 오류다.

2016-3-56 choice_2  '대손지' -> 보류
    ①의 '토양표층'과 대비되는 자리라 깊은 층을 뜻하는 말이 와야 하지만,
    원본 표기를 특정할 근거가 부족하다. 손대지 않고 보고만 한다.

사용법:
    python fix_residual.py            # 확인만
    python fix_residual.py --apply
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_residual_backup.json"
CASES = [
    (2016, 2, 85, "choice_3", "당해 지경", "당해 지역"),
]

apply = "--apply" in sys.argv
changes = []
for y, r, n, field, old, new in CASES:
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=r, number=n).first()
    if q is None:
        print("문항 없음 %d-%d-%d" % (y, r, n))
        continue
    v = getattr(q, field) or ""
    if old not in v:
        print("%d-%d-%d %s: '%s' 없음 (이미 처리됐거나 표기가 다름)" % (y, r, n, field, old))
        continue
    changes.append({"pk": q.pk, "ref": "%d-%d-%d" % (y, r, n),
                    "field": field, "before": v, "after": v.replace(old, new)})
    print("%d-%d-%d %s" % (y, r, n, field))
    print("   전: %s" % v[:64])
    print("   후: %s" % v.replace(old, new)[:64])

if apply and changes:
    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in changes:
        q = GisaQuestion.objects.get(pk=c["pk"])
        setattr(q, c["field"], c["after"])
        q.save(update_fields=[c["field"]])
    print()
    print("반영 완료 %d건 (백업 %s)" % (len(changes), BACKUP))
elif not apply:
    print()
    print("확인만 (--apply 로 반영)")

print()
print("[보류] 2016-3-56 choice_2 '대손지' — 원본 표기 특정 불가, 손대지 않음")
