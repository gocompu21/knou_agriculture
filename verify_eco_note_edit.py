# -*- coding: utf-8 -*-
"""노트 보강 전후를 대조해 손상 여부를 검증한다.

에이전트가 국소 Edit 로 노트를 보강한 뒤, 다음을 확인한다.
  1) 관련 문제 ref 가 하나도 사라지지 않았는가 (커버리지 유지)
  2) 장/절/항 구조가 깨지지 않았는가
  3) 실제로 얼마나 늘었는가

사용법:
    python verify_eco_note_edit.py --orig _eco_note_v2_orig --new _eco_note_v2
"""
import argparse
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILES = {
    "생태환경조사분석": "new_survey.md",
    "생태복원계획": "new_plan.md",
    "생태복원설계·시공": "new_design.md",
    "생태복원 사후관리·평가": "new_mgmt.md",
}


def stats(path):
    txt = open(path, encoding="utf-8").read()
    refs = re.findall(r"(?<!\w)(\d{4}-\d+-\d+)(?!\w)", txt)
    return {
        "size": len(txt),
        "refs": set(refs),
        "nref": len(refs),
        "ch": len(re.findall(r"^##\s+제\d+장", txt, re.M)),
        "app": len(re.findall(r"^##\s+부록", txt, re.M)),
        "sec": len(re.findall(r"^###\s+", txt, re.M)),
        "sub": len(re.findall(r"^####\s+", txt, re.M)),
        "tbl": len(re.findall(r"^\|", txt, re.M)),
        "warn": txt.count("⚠️"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--new", required=True)
    args = ap.parse_args()

    ok = True
    for subj, fn in FILES.items():
        po, pn = os.path.join(args.orig, fn), os.path.join(args.new, fn)
        if not (os.path.exists(po) and os.path.exists(pn)):
            print("[없음] %s" % subj)
            ok = False
            continue

        a, b = stats(po), stats(pn)
        lost = a["refs"] - b["refs"]
        add = b["refs"] - a["refs"]
        d = b["size"] - a["size"]

        flag = "OK " if not lost and b["ch"] == a["ch"] and b["sec"] == a["sec"] else "!! "
        if lost or b["ch"] != a["ch"] or b["sec"] != a["sec"]:
            ok = False

        print("%s%-22s %9s자 (%+7s)  장%d→%d 절%d→%d 항%d→%d 표%d→%d ⚠️%d→%d"
              % (flag, subj, format(b["size"], ","), format(d, ","),
                 a["ch"], b["ch"], a["sec"], b["sec"], a["sub"], b["sub"],
                 a["tbl"], b["tbl"], a["warn"], b["warn"]))
        print("    ref 고유 %d→%d" % (len(a["refs"]), len(b["refs"])))
        if lost:
            s = sorted(lost, key=lambda r: tuple(int(x) for x in r.split("-")))
            print("    [유실 %d건] %s" % (len(lost), ", ".join(s[:20])))
        if add:
            s = sorted(add, key=lambda r: tuple(int(x) for x in r.split("-")))
            print("    [추가 %d건] %s" % (len(add), ", ".join(s[:20])))
        print()

    print("=" * 60)
    print("검증 결과:", "정상 — 배포 가능" if ok else "이상 있음 — 확인 필요")


if __name__ == "__main__":
    main()
