# -*- coding: utf-8 -*-
"""3라운드 동기화에서 차단된 2건 처리.

두 건 모두 글자 교정이 포함돼 있어 sync_round3.py 의 안전장치
(공백·기호만 다를 때 허용)에 정상적으로 걸린 것이다.
각각 근거를 확인했으므로 명시적으로 처리한다.

2016-2-85 choice_3  '당해 지경' -> '당해 지역'
    같은 문항 ②가 '당해 지역', ④가 '당해 행위'로 동일 구문.
    PDF 원본에도 '지경'으로 인쇄돼 있으나 comcbt 계통 오류.

2021-2-99 text  두 곳
    (1) '생태∙경관' -> '생태ㆍ경관'  (U+2219 기호 손상)
    (2) '보전역의' -> '보전지역의'   (글자 '지' 누락)
    (2)는 앞선 공백 교정 과정에서 유실된 것으로 보인다.
    같은 문장 앞부분이 '생태·경관보전지역'으로 정상 표기돼 있어 확정.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_blocked3_backup.json"
BAD = chr(0x2219)
GOOD = chr(0x318D)

CASES = [
    (2016, 2, 85, "choice_3", [("당해 지경", "당해 지역")]),
    (2021, 2, 99, "text", [(BAD, GOOD), ("보전역의", "보전지역의")]),
]

apply = "--apply" in sys.argv
changes = []
for y, r, n, field, subs in CASES:
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=r, number=n).first()
    if q is None:
        print("문항 없음 %d-%d-%d" % (y, r, n))
        continue
    cur = getattr(q, field) or ""
    new = cur
    applied = []
    for old, rep in subs:
        if old in new:
            new = new.replace(old, rep)
            applied.append("%s->%s" % (old, rep))
    if new == cur:
        print("%d-%d-%d %s: 이미 정리됨" % (y, r, n, field))
        continue
    changes.append({"pk": q.pk, "ref": "%d-%d-%d" % (y, r, n),
                    "field": field, "before": cur, "after": new})
    print("%d-%d-%d %s  [%s]" % (y, r, n, field, ", ".join(applied)))
    print("   후: %s" % new[:76].replace("\n", " "))

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
