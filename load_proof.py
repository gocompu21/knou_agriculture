# -*- coding: utf-8 -*-
"""교정 결과(*_fix.json)를 DB에 반영한다.

에이전트 결과 형식:
  {"round": "2012-1",
   "fixes": [
     {"ref": "2012-1-5", "field": "choice_2",
      "before": "...저 항하거나...", "after": "...저항하거나...",
      "kind": "split", "note": "조판 줄바꿈"}
   ]}

안전장치
  - before 가 현재 DB 값과 정확히 일치할 때만 반영한다 (엉뚱한 덮어쓰기 방지)
  - 길이가 크게 달라지면(±5% 초과) 건너뛰고 보고한다 (내용 삭제 방지)
  - 반영분은 백업한다

사용법:
    python load_proof.py --src _proof            # 검증만
    python load_proof.py --src _proof --apply
    python load_proof.py --restore
"""
import argparse, glob, io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import GisaQuestion

BACKUP = "_proof_backup.json"
OKFIELDS = {"text", "choice_1", "choice_2", "choice_3", "choice_4"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="_proof")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    if args.restore:
        rows = json.load(open(BACKUP, encoding="utf-8"))
        for r in rows:
            q = GisaQuestion.objects.filter(pk=r["pk"]).first()
            if q:
                setattr(q, r["field"], r["before"])
                q.save(update_fields=[r["field"]])
        print("복원 %d건" % len(rows))
        return

    files = sorted(glob.glob(os.path.join(args.src, "*_fix.json")))
    if not files:
        print("결과 파일(*_fix.json) 없음:", args.src)
        return

    ok, skip, mismatch, applied = [], [], [], []
    for fp in files:
        d = json.load(open(fp, encoding="utf-8"))
        for fx in d.get("fixes", []):
            ref, field = fx.get("ref", ""), fx.get("field", "")
            before, after = fx.get("before", ""), fx.get("after", "")
            if field not in OKFIELDS:
                skip.append((ref, field, "필드 이상"))
                continue
            try:
                y, r, n = (int(x) for x in ref.split("-"))
            except ValueError:
                skip.append((ref, field, "ref 이상"))
                continue
            q = GisaQuestion.objects.filter(
                exam__certification__name="자연생태복원기사",
                exam__year=y, exam__round=r, number=n).first()
            if q is None:
                skip.append((ref, field, "문항 없음"))
                continue
            cur = getattr(q, field) or ""
            if cur != before:
                mismatch.append((ref, field))
                continue
            if before == after:
                skip.append((ref, field, "변화 없음"))
                continue
            if abs(len(after) - len(before)) > max(8, len(before) * 0.05):
                skip.append((ref, field, "길이 변화 큼 %d->%d" % (len(before), len(after))))
                continue
            ok.append((q, field, before, after, fx.get("kind", ""), fx.get("note", "")))

    print("반영 가능 %d건 · 건너뜀 %d건 · DB불일치 %d건"
          % (len(ok), len(skip), len(mismatch)))
    for ref, field, why in skip[:12]:
        print("   [건너뜀] %-11s %-10s %s" % (ref, field, why))
    for ref, field in mismatch[:12]:
        print("   [불일치] %-11s %s" % (ref, field))

    if not args.apply:
        print()
        print("검증만 (--apply 로 반영)")
        return

    for q, field, before, after, kind, note in ok:
        applied.append({"pk": q.pk, "field": field, "before": before})
        setattr(q, field, after)
        q.save(update_fields=[field])
    json.dump(applied, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("반영 완료 %d건 (백업 %s)" % (len(applied), BACKUP))


main()
