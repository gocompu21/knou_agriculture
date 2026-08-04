# -*- coding: utf-8 -*-
"""선지별 해설 보강 결과를 DB에 반영.

에이전트가 만든 `{id, choice_1_exp, ..., choice_4_exp}` 배열 JSON 들을 읽어
GisaQuestion 에 저장한다. `explanation`(PDF 원본 해설)은 건드리지 않는다.

사용법:
    python load_eco2325_exp.py --src DIR
    python load_eco2325_exp.py --src DIR --dry
"""
import argparse
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import GisaQuestion

FIELDS = ("choice_1_exp", "choice_2_exp", "choice_3_exp", "choice_4_exp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="보강 결과 JSON 디렉토리")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, "*.json")))
    if not files:
        print("결과 JSON 없음:", args.src)
        return

    n_ok = n_skip = 0
    problems = []

    for fp in files:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        items = data["questions"] if isinstance(data, dict) else data

        for it in items:
            qid = it.get("id")
            q = GisaQuestion.objects.filter(pk=qid).first()
            if q is None:
                problems.append("%s: id=%s 문항 없음" % (os.path.basename(fp), qid))
                continue

            vals = {f: (it.get(f) or "").strip() for f in FIELDS}
            if not all(vals.values()):
                empty = [f for f, v in vals.items() if not v]
                problems.append("%s ref=%s: %s 비어있음"
                                % (os.path.basename(fp), it.get("ref"), ",".join(empty)))

            if args.dry:
                n_skip += 1
                continue

            for f, v in vals.items():
                if v:
                    setattr(q, f, v)
            q.save(update_fields=[f for f, v in vals.items() if v])
            n_ok += 1

        print("%-32s %3d문항" % (os.path.basename(fp), len(items)))

    if args.dry:
        print("\n[dry] 대상 %d문항 (저장 안 함)" % n_skip)
    else:
        print("\n저장 완료: %d문항" % n_ok)

    if problems:
        print("\n[점검 %d건]" % len(problems))
        for p in problems[:40]:
            print("  ", p)
        if len(problems) > 40:
            print("   ... 외 %d건" % (len(problems) - 40))


if __name__ == "__main__":
    main()
