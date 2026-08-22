# -*- coding: utf-8 -*-
"""3라운드 교정(기호 정규화 + 잔존 오류 + A low 띄움)을 서버에 반영한다.

안전장치: 현재 서버 값과 목표값이 '공백·캐리지리턴을 뺀 글자열' 기준으로
          같거나, 손상 기호(∙)만 다를 때만 덮어쓴다.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

CR = chr(13)
BAD = chr(0x2219)   # ∙
GOOD = chr(0x318D)  # ㆍ


def norm(s):
    return (s or "").replace(" ", "").replace(CR, "").replace(BAD, GOOD)


rows = json.load(open("_deploy_round3.json", encoding="utf-8"))
same = upd = blocked = 0
for r in rows:
    y, rd, n = (int(x) for x in r["ref"].split("-"))
    q = GisaQuestion.objects.filter(
        exam__certification__name="자연생태복원기사",
        exam__year=y, exam__round=rd, number=n).first()
    if q is None:
        blocked += 1
        continue
    cur = getattr(q, r["field"]) or ""
    tgt = r["value"] or ""
    if cur == tgt:
        same += 1
        continue
    if norm(cur) != norm(tgt):
        blocked += 1
        print("  [차단] %s %s" % (r["ref"], r["field"]))
        continue
    setattr(q, r["field"], tgt)
    q.save(update_fields=[r["field"]])
    upd += 1
print("이미 일치 %d · 갱신 %d · 차단 %d" % (same, upd, blocked))
