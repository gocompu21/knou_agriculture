# -*- coding: utf-8 -*-
"""B(글자 변경) 중 high 확신분을 DB에 반영한다.

A(공백만)와 달리 원문 글자가 바뀌므로 안전장치를 더 건다.
  - 현재 DB 값이 before 와 정확히 일치할 때만 반영
  - 길이 변화가 3자를 넘으면 차단 (대량 치환 방지)
  - 반영 전량 백업
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_proof_B_backup.json"
SRC = "_proof_B_safe.json"
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
    ready, mismatch, blocked = [], [], []

    for f in fixes:
        ref, field = f.get("ref", ""), f.get("field", "")
        b, a = f.get("before", ""), f.get("after", "")
        if field not in OK or b == a:
            blocked.append((ref, field, "필드/무변화"))
            continue
        if abs(len(a) - len(b)) > 3:
            blocked.append((ref, field, "길이변화 %d→%d" % (len(b), len(a))))
            continue
        try:
            y, r, n = (int(x) for x in ref.split("-"))
        except ValueError:
            blocked.append((ref, field, "ref 이상"))
            continue
        q = GisaQuestion.objects.filter(
            exam__certification__name="자연생태복원기사",
            exam__year=y, exam__round=r, number=n).first()
        if q is None:
            blocked.append((ref, field, "문항 없음"))
            continue
        cur = getattr(q, field) or ""
        if cur.replace("\r", "") != b.replace("\r", ""):
            mismatch.append((ref, field))
            continue
        ready.append((q, field, cur, a))

    print("반영 가능 %d · DB불일치 %d · 차단 %d" % (len(ready), len(mismatch), len(blocked)))
    for x in blocked[:10]:
        print("   [차단] %s %s %s" % x)
    for x in mismatch[:10]:
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
