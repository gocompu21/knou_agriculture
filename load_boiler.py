# -*- coding: utf-8 -*-
"""서버를 로컬 최종값과 일치시킨다 (선지 해설 상투 문구 정리 691필드).

안전장치: 현재 서버 값이 before 또는 목표값과 일치할 때만 덮어쓴다.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

CR = chr(13)
OK = {"choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp"}
rows = json.load(open("_boiler_changes.json", encoding="utf-8"))
same = upd = blocked = 0
for r in rows:
    if r["field"] not in OK:
        blocked += 1; print("  [차단] %s %s — 허용되지 않은 필드" % (r["ref"], r["field"])); continue
    y, rd, n = (int(x) for x in r["ref"].split("-"))
    q = GisaQuestion.objects.filter(
        exam__certification__name=r["cert"],
        exam__year=y, exam__round=rd, number=n).first()
    if q is None:
        blocked += 1; print("  [차단] %s %s — 문항 없음" % (r["cert"], r["ref"])); continue
    cur = (getattr(q, r["field"]) or "").replace(CR, "")
    tgt = (r["value"] if "value" in r else r["after"] or "").replace(CR, "")
    bef = (r["before"] or "").replace(CR, "")
    if cur == tgt:
        same += 1; continue
    if cur != bef:
        blocked += 1; print("  [차단] %s %s %s — 서버 값이 예상과 다름" % (r["cert"][:4], r["ref"], r["field"])); continue
    setattr(q, r["field"], r["after"])
    q.save(update_fields=[r["field"]])
    upd += 1
print("이미 일치 %d · 갱신 %d · 차단 %d" % (same, upd, blocked))
