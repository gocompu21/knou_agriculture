# -*- coding: utf-8 -*-
"""B low 재검토(229건) + 개별 교정 5건의 로컬 최종값을 배포 JSON 으로 추출한다.

형식은 _deploy_proof_b.json 과 같다: {ref, field, value(목표), before(교정 전)}
sync_blow.py 가 서버에서 before→value 로만 덮어쓴다.
"""
import io, json, os, sys, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

OUT = "_deploy_blow.json"
rows = []

# 1) B low 반영분 (load_blow.py --apply 백업)
for r in json.load(open("_blow_backup.json", encoding="utf-8")):
    rows.append({"pk": r["pk"], "ref": r["ref"], "field": r["field"],
                 "before": r["before"], "src": "blow"})

# 2) 개별 교정 5건 (_fix_YYYY_R_N_backup.json) — before 만 있으므로 ref 는 DB 에서
for fp in sorted(glob.glob("_fix_*_backup.json")):
    tag = os.path.basename(fp)[5:-12]          # 2013_3_93
    ref = tag.replace("_", "-")
    for r in json.load(open(fp, encoding="utf-8")):
        rows.append({"pk": r["pk"], "ref": ref, "field": r["field"],
                     "before": r["before"], "src": os.path.basename(fp)})

out, stale, missing = [], [], []
for r in rows:
    q = GisaQuestion.objects.filter(pk=r["pk"]).first()
    if q is None:
        missing.append(r); continue
    ref = "%d-%d-%d" % (q.exam.year, q.exam.round, q.number)
    if ref != r["ref"] or q.exam.certification.name != "자연생태복원기사":
        missing.append(r); continue
    val = getattr(q, r["field"]) or ""
    if val == r["before"]:
        stale.append(r); continue          # 로컬에 반영 안 된 것 — 보낼 값이 없다
    out.append({"ref": ref, "field": r["field"], "value": val, "before": r["before"]})

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print("추출 %d건 → %s" % (len(out), OUT))
print("  필드별:", dict(Counter(o["field"] for o in out)))
print("  원천별:", dict(Counter(r["src"] if r["src"] == "blow" else "fix" for r in rows)))
if stale:
    print("미반영(로컬값==before) %d건:" % len(stale))
    for r in stale: print("   ", r["ref"], r["field"])
if missing:
    print("문항 불일치 %d건:" % len(missing))
    for r in missing: print("   ", r["ref"], r["field"], r["pk"])
