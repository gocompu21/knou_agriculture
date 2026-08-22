# -*- coding: utf-8 -*-
"""A low 중 '띄우는 방향' 36건만 반영한다.

A low 85건은 두 부류로 갈린다.
  붙이는 쪽 49건 — '수변 생태계'->'수변생태계' 처럼 복합명사 띄어쓰기.
                   한국어 맞춤법상 둘 다 허용되므로 손대지 않는다.
                   고치면 맞는 텍스트를 바꾸는 셈이다.
  띄우는 쪽 36건 — '먼것은'->'먼 것은', '세가지'->'세 가지' 처럼
                   의존명사가 앞말에 붙어버린 것. 띄어야 맞다.

불변식은 A 와 동일: 공백을 제외하면 before/after 가 완전히 같아야 한다.

사용법:
    python load_proof_a_low.py            # 검증만
    python load_proof_a_low.py --apply
    python load_proof_a_low.py --restore
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_proof_A_low_backup.json"
OK = {"text", "choice_1", "choice_2", "choice_3", "choice_4"}
DANGER = {"2013-3-54"}   # 선지 2·3 동일 — 파싱 붕괴 문항


def main():
    if "--restore" in sys.argv:
        rows = json.load(open(BACKUP, encoding="utf-8"))
        for r in rows:
            q = GisaQuestion.objects.filter(pk=r["pk"]).first()
            if q:
                setattr(q, r["field"], r["before"])
                q.save(update_fields=[r["field"]])
        print("복원 %d건" % len(rows))
        return

    apply = "--apply" in sys.argv
    A = json.load(open("_proof_A_spacing.json", encoding="utf-8"))["fixes"]
    lo = [f for f in A if f.get("confidence") != "high"]
    # 띄우는 방향만 (길이가 늘어남)
    cand = [f for f in lo if len(f["after"]) > len(f["before"])
            and f["ref"] not in DANGER]

    ready, mismatch, bad = [], [], []
    for f in cand:
        ref, field = f["ref"], f["field"]
        b, a = f["before"], f["after"]
        if field not in OK or b.replace(" ", "") != a.replace(" ", ""):
            bad.append((ref, field))
            continue
        y, r, n = (int(x) for x in ref.split("-"))
        q = GisaQuestion.objects.filter(
            exam__certification__name="자연생태복원기사",
            exam__year=y, exam__round=r, number=n).first()
        if q is None:
            bad.append((ref, field))
            continue
        cur = getattr(q, field) or ""
        if cur.replace("\r", "") != b.replace("\r", ""):
            mismatch.append((ref, field))
            continue
        ready.append((q, field, cur, a))

    print("대상 %d · 반영가능 %d · DB불일치 %d · 이상 %d"
          % (len(cand), len(ready), len(mismatch), len(bad)))
    for x in mismatch[:6]:
        print("   [불일치] %s %s" % x)

    if not apply:
        print()
        print("검증만 (--apply 로 반영)")
        return

    done = []
    for q, field, cur, a in ready:
        done.append({"pk": q.pk, "field": field, "before": cur})
        setattr(q, field, a)
        q.save(update_fields=[field])
    json.dump(done, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("반영 완료 %d건 (백업 %s)" % (len(done), BACKUP))


main()
