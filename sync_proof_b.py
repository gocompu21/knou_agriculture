# -*- coding: utf-8 -*-
"""서버를 로컬 최종값과 일치시킨다 (B: 글자 변경분).

안전장치: 현재 서버 값이 before 또는 목표값과 일치할 때만 덮어쓴다.
          제3의 값이면 차단하고 보고한다.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

CR = chr(13)
rows = json.load(open("_deploy_proof_b.json", encoding="utf-8"))
same = upd = blocked = 0
for r in rows:
    y, rd, n = (int(x) for x in r["ref"].split("-"))
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=rd, number=n).first()
    if q is None:
        blocked += 1
        continue
    cur = (getattr(q, r["field"]) or "").replace(CR, "")
    tgt = (r["value"] or "").replace(CR, "")
    bef = (r["before"] or "").replace(CR, "")
    if cur == tgt:
        same += 1
        continue
    if cur != bef:
        blocked += 1
        print("  [차단] %s %s — 서버 값이 예상과 다름" % (r["ref"], r["field"]))
        continue
    setattr(q, r["field"], r["value"])
    q.save(update_fields=[r["field"]])
    upd += 1
print("이미 일치 %d · 갱신 %d · 차단 %d" % (same, upd, blocked))
