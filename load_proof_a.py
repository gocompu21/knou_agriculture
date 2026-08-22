# -*- coding: utf-8 -*-
"""A(공백만 조정) 안전분을 DB에 반영한다.

불변식: before 와 after 는 공백을 제거하면 완전히 동일해야 한다.
        (원문 글자를 하나도 바꾸지 않는다)
반영 전 현재 DB 값이 before 와 일치하는지 확인한다.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_proof_A_backup.json"
SRC = "_proof_A_safe.json"
OK = {"text", "choice_1", "choice_2", "choice_3", "choice_4"}


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
    fixes = json.load(open(SRC, encoding="utf-8"))["fixes"]
    ready, mismatch, bad = [], [], []

    for f in fixes:
        ref, field = f.get("ref", ""), f.get("field", "")
        b, a = f.get("before", ""), f.get("after", "")
        if field not in OK:
            bad.append((ref, field, "필드 이상"))
            continue
        if b.replace(" ", "") != a.replace(" ", ""):
            bad.append((ref, field, "글자 변경됨 — 불변식 위반"))
            continue
        try:
            y, r, n = (int(x) for x in ref.split("-"))
        except ValueError:
            bad.append((ref, field, "ref 이상"))
            continue
        q = GisaQuestion.objects.filter(
            exam__certification__name="자연생태복원기사",
            exam__year=y, exam__round=r, number=n).first()
        if q is None:
            bad.append((ref, field, "문항 없음"))
            continue
        if (getattr(q, field) or "") != b:
            mismatch.append((ref, field))
            continue
        ready.append((q, field, b, a))

    print("반영 가능 %d · DB불일치 %d · 이상 %d" % (len(ready), len(mismatch), len(bad)))
    for x in bad[:8]:
        print("   [이상] %s" % (x,))
    for x in mismatch[:8]:
        print("   [불일치] %s %s" % x)

    if not apply:
        print()
        print("검증만 (--apply 로 반영)")
        return

    done = []
    for q, field, b, a in ready:
        done.append({"pk": q.pk, "field": field, "before": b})
        setattr(q, field, a)
        q.save(update_fields=[field])
    json.dump(done, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("반영 완료 %d건 (백업 %s)" % (len(done), BACKUP))


main()
