# -*- coding: utf-8 -*-
"""차단된 2건의 정확한 차이 지점을 찾는다."""
import io, json, os, sys, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

CR = chr(13); BAD = chr(0x2219); GOOD = chr(0x318D)
def norm(s):
    return (s or "").replace(" ", "").replace(CR, "").replace(BAD, GOOD)

rows = {(r["ref"], r["field"]): r["value"]
        for r in json.load(open("_deploy_round3.json", encoding="utf-8"))}

for ref, field in [("2016-2-85", "choice_3"), ("2021-2-99", "text")]:
    y, r, n = (int(x) for x in ref.split("-"))
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=r, number=n).first()
    cur = getattr(q, field) or ""
    tgt = rows.get((ref, field), "")
    print("=" * 60)
    print(ref, field)
    print("  현재(로컬) len=%d  목표 len=%d" % (len(cur), len(tgt)))
    print("  norm 일치:", norm(cur) == norm(tgt))
    if norm(cur) != norm(tgt):
        a, b = norm(cur), norm(tgt)
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if t == "equal":
                continue
            print("    %-8s 현재%r → 목표%r" % (t, a[i1:i2][:30], b[j1:j2][:30]))
