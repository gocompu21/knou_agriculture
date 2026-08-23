# -*- coding: utf-8 -*-
"""기사 문항의 'km2' 표기를 'km²'(윗첨자)로 통일한다.

대상: GisaQuestion 전 자격증의 문제·보기·해설 필드
규칙: km2 뒤에 숫자가 이어지지 않는 경우만 (km20 같은 값 보호)
로컬·서버 모두 이 스크립트를 그대로 실행한다 (결정적 치환이라 동기화 JSON 불필요).
  python fix_km2.py           # 대상 확인
  python fix_km2.py --apply   # 반영 (백업 _km2_backup.json)
  python fix_km2.py --restore # 되돌리기
"""
import io, json, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_km2_backup.json"
FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp"]
PAT = re.compile(r"km2(?!\d)")
SUP2 = "km" + chr(0xB2)   # km²

if "--restore" in sys.argv:
    rows = json.load(open(BACKUP, encoding="utf-8"))
    for r in rows:
        q = GisaQuestion.objects.filter(pk=r["pk"]).first()
        if q:
            setattr(q, r["field"], r["before"]); q.save(update_fields=[r["field"]])
    print("복원 %d건" % len(rows)); sys.exit()

apply = "--apply" in sys.argv
changes = []
for q in GisaQuestion.objects.select_related("exam__certification").iterator():
    for f in FIELDS:
        cur = getattr(q, f) or ""
        if not PAT.search(cur):
            continue
        new = PAT.sub(SUP2, cur)
        ref = "%s %d-%d-%d" % (q.exam.certification.name, q.exam.year, q.exam.round, q.number)
        changes.append({"pk": q.pk, "ref": ref, "field": f, "before": cur, "after": new})
        for m in PAT.finditer(cur):
            s = max(0, m.start() - 18); e = min(len(cur), m.end() + 12)
            print("%-28s %-12s …%s…" % (ref, f, cur[s:e].replace("\n", " ")))

print("대상 %d필드 (치환 %d곳)" % (len(changes), sum(len(PAT.findall(c["before"])) for c in changes)))
if apply and changes:
    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in changes:
        q = GisaQuestion.objects.get(pk=c["pk"])
        setattr(q, c["field"], c["after"]); q.save(update_fields=[c["field"]])
    print("반영 완료 (백업 %s)" % BACKUP)
elif not apply:
    print("확인만 수행 (--apply 로 반영)")
