# -*- coding: utf-8 -*-
import io, json, os, sys, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

rows = {(r["ref"], r["field"]): r["value"]
        for r in json.load(open("_deploy_round3.json", encoding="utf-8"))}
ref, field = "2021-2-99", "text"
y, r, n = 2021, 2, 99
q = GisaQuestion.objects.filter(
    exam__certification__name="자연생태복원기사",
    exam__year=y, exam__round=r, number=n).first()
cur = getattr(q, field) or ""
tgt = rows[(ref, field)]
print("현재 len=%d / 목표 len=%d" % (len(cur), len(tgt)))
for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, cur, tgt).get_opcodes():
    if t == "equal":
        continue
    print("%-8s 현재%r → 목표%r" % (t, cur[i1:i2], tgt[j1:j2]))
    print("   현재 문맥: ...%s..." % cur[max(0, i1-24):i2+24].replace("\n", " "))
    print("   목표 문맥: ...%s..." % tgt[max(0, j1-24):j2+24].replace("\n", " "))
