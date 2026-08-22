# -*- coding: utf-8 -*-
"""서버를 로컬 최종값과 일치시킨다.

load_proof_a.py 는 before 일치를 요구해서, 서버가 이미 일부만 반영된
상태였다면 나머지를 건너뛴다. 이 스크립트는 최종값을 그대로 덮어써
로컬과 서버를 같게 만든다.

안전장치: 현재 값과 목표값이 공백을 빼고 동일할 때만 덮어쓴다.
          (원문 글자를 바꾸는 일이 절대 없도록)
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

rows = json.load(open("_deploy_proof_a.json", encoding="utf-8"))
same = upd = blocked = miss = 0
for r in rows:
    y, rd, n = (int(x) for x in r["ref"].split("-"))
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=rd, number=n).first()
    if q is None:
        miss += 1
        continue
    cur = getattr(q, r["field"]) or ""
    tgt = r["value"] or ""
    if cur == tgt:
        same += 1
        continue
    if cur.replace(" ", "") != tgt.replace(" ", ""):
        blocked += 1
        print("  [차단] %s %s — 글자가 다름" % (r["ref"], r["field"]))
        continue
    setattr(q, r["field"], tgt)
    q.save(update_fields=[r["field"]])
    upd += 1

print("이미 일치 %d · 갱신 %d · 차단 %d · 문항없음 %d" % (same, upd, blocked, miss))
