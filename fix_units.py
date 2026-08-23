# -*- coding: utf-8 -*-
"""기사 문항·쪽집게 노트의 면적/부피 단위 표기를 윗첨자로 통일한다.

  km2 → km²   m2 → m²   cm2 → cm²   mm2 → mm²   ㎢ → km²
  km3 → km³   m3 → m³   cm3 → cm³   mm3 → mm³
  (노트) km^2, m^2, m^3 → 윗첨자

규칙: 단위 앞에 영문자가 오지 않고(ppm2 보호), 지수 뒤에 숫자가 이어지지 않는 경우만(m20 보호).
로컬·서버 모두 이 스크립트를 그대로 실행한다.
  python fix_units.py           # 대상 확인
  python fix_units.py --apply   # 반영 (백업 _units_backup.json)
  python fix_units.py --restore # 되돌리기
"""
import io, json, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion, GisaTextbook

BACKUP = "_units_backup.json"
FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp"]
S2, S3 = chr(0xB2), chr(0xB3)
RULES = [
    (re.compile(r"(?<![A-Za-z])(k?m|cm|mm)\^?\{?([23])\}?(?![0-9])"),
     lambda m: m.group(1) + (S2 if m.group(2) == "2" else S3)),
    (re.compile(chr(0x33A2)), lambda m: "km" + S2),   # ㎢
]


def convert(s):
    for pat, rep in RULES:
        s = pat.sub(rep, s)
    return s


def hits(s):
    return [m for pat, _ in RULES for m in pat.finditer(s)]


if "--restore" in sys.argv:
    rows = json.load(open(BACKUP, encoding="utf-8"))
    for r in rows:
        M = GisaTextbook if r["model"] == "textbook" else GisaQuestion
        o = M.objects.filter(pk=r["pk"]).first()
        if o:
            setattr(o, r["field"], r["before"]); o.save(update_fields=[r["field"]])
    print("복원 %d건" % len(rows)); sys.exit()

apply = "--apply" in sys.argv
verbose = "-v" in sys.argv
changes, n_hits = [], 0
for q in GisaQuestion.objects.select_related("exam__certification").iterator():
    for f in FIELDS:
        cur = getattr(q, f) or ""
        h = hits(cur)
        if not h:
            continue
        ref = "%s %d-%d-%d" % (q.exam.certification.name, q.exam.year, q.exam.round, q.number)
        changes.append({"model": "question", "pk": q.pk, "ref": ref, "field": f,
                        "before": cur, "after": convert(cur)})
        n_hits += len(h)
        if verbose:
            for m in h:
                s = max(0, m.start() - 16); e = min(len(cur), m.end() + 10)
                print("%-30s %-12s …%s…" % (ref, f, cur[s:e].replace("\n", " ")))
for tb in GisaTextbook.objects.select_related("certification", "subject"):
    cur = tb.content or ""
    h = hits(cur)
    if not h:
        continue
    ref = "[노트] %s/%s" % (tb.certification.name, tb.subject.name)
    changes.append({"model": "textbook", "pk": tb.pk, "ref": ref, "field": "content",
                    "before": cur, "after": convert(cur)})
    n_hits += len(h)
    if verbose:
        for m in h:
            s = max(0, m.start() - 16); e = min(len(cur), m.end() + 10)
            print("%-30s %-12s …%s…" % (ref, "content", cur[s:e].replace("\n", " ")))

print("대상 %d필드 (치환 %d곳)" % (len(changes), n_hits))
if apply and changes:
    json.dump(changes, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in changes:
        M = GisaTextbook if c["model"] == "textbook" else GisaQuestion
        o = M.objects.get(pk=c["pk"])
        setattr(o, c["field"], c["after"]); o.save(update_fields=[c["field"]])
    print("반영 완료 (백업 %s)" % BACKUP)
elif not apply:
    print("확인만 수행 (--apply 로 반영)")
