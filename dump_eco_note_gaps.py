# -*- coding: utf-8 -*-
"""출판사 해설(2020-3/2021-2/2022-1)을 노트의 어느 절에 반영할지 배분.

노트 본문의 `**관련 문제**: (YYYY-R-N)` 를 읽어 절↔문항 매핑을 만들고,
그 절에 걸린 문항 중 출판사 해설이 있는 것만 모아 장 단위 배치로 낸다.

에이전트는 이 배치를 받아 해당 절의 서술을 출판사 근거로 정밀화한다.

사용법:
    python dump_eco_note_gaps.py --note-dir _eco_note_v2 --out-dir _eco_note_gap
"""
import argparse
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 통합 4과목 노트 파일 (숨김 처리된 구 체계는 대상 아님)
NOTES = {
    "생태환경조사분석": "new_survey.md",
    "생태복원계획": "new_plan.md",
    "생태복원설계·시공": "new_design.md",
    "생태복원 사후관리·평가": "new_mgmt.md",
}

SRC_ROUNDS = {(2020, 3), (2021, 2), (2022, 1)}


def load_pub(src):
    """출판사 해설 풀: ref -> {text, choices, answer, explanation}"""
    pool = {}
    for fp in glob.glob(os.path.join(src, "*_a.json")) + \
              glob.glob(os.path.join(src, "*_b.json")):
        d = json.load(open(fp, encoding="utf-8"))
        y, r = d["year"], d["round"]
        if (y, r) not in SRC_ROUNDS:
            continue
        for q in d.get("questions", []):
            exp = (q.get("explanation") or "").strip()
            if not exp:
                continue
            ref = "%d-%d-%d" % (y, r, q["number"])
            old = pool.get(ref)
            if old and len(old["explanation"]) >= len(exp):
                continue
            pool[ref] = {
                "ref": ref,
                "subject": q.get("subject", ""),
                "text": q.get("text", ""),
                "choices": q.get("choices", []),
                "answer": q.get("answer", ""),
                "explanation": exp,
            }
    return pool


def parse_note(path):
    """노트를 (장, 절, 절본문시작줄, ref목록) 단위로 쪼갠다."""
    lines = open(path, encoding="utf-8").read().split("\n")
    chapters = []      # {no, title, line, sections:[...]}
    cur_ch = cur_sec = None

    for i, ln in enumerate(lines):
        m = re.match(r"^##\s+(제(\d+)장\.?\s*(.*))$", ln)
        if m:
            cur_ch = {"no": int(m.group(2)), "title": m.group(1).strip(),
                      "line": i, "sections": []}
            chapters.append(cur_ch)
            cur_sec = None
            continue
        m = re.match(r"^###\s+(.+)$", ln)
        if m and cur_ch is not None:
            cur_sec = {"title": m.group(1).strip(), "line": i, "refs": []}
            cur_ch["sections"].append(cur_sec)
            continue
        if "관련 문제" in ln:
            refs = re.findall(r"(?<!\w)(\d{4}-\d+-\d+)(?!\w)", ln)
            tgt = cur_sec if cur_sec is not None else None
            if tgt is not None:
                tgt["refs"].extend(refs)
    return lines, chapters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--note-dir", required=True)
    ap.add_argument("--src", default="_eco2022_backup")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    pub = load_pub(args.src)
    print("출판사 해설 보유: %d문항" % len(pub))
    print()

    os.makedirs(args.out_dir, exist_ok=True)
    grand = 0

    for subj, fname in NOTES.items():
        path = os.path.join(args.note_dir, fname)
        if not os.path.exists(path):
            print("[없음]", path)
            continue

        lines, chapters = parse_note(path)
        safe = subj.replace("·", "_").replace(" ", "_")

        n_hit = 0
        batches = []
        for ch in chapters:
            items = []
            for sec in ch["sections"]:
                hits = [pub[r] for r in dict.fromkeys(sec["refs"]) if r in pub]
                if hits:
                    items.append({"section": sec["title"],
                                  "line": sec["line"] + 1,
                                  "questions": hits})
                    n_hit += len(hits)
            if items:
                batches.append({"chapter": ch["title"], "line": ch["line"] + 1,
                                "sections": items})

        if not batches:
            print("%-22s  대상 없음" % subj)
            continue

        fp = os.path.join(args.out_dir, "%s.json" % safe)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"subject": subj, "note_file": fname,
                       "chapters": batches}, f, ensure_ascii=False, indent=1)

        n_sec = sum(len(b["sections"]) for b in batches)
        grand += n_hit
        print("%-22s  장 %2d · 절 %3d · 문항 %3d  → %s"
              % (subj, len(batches), n_sec, n_hit, os.path.basename(fp)))

    print()
    print("총 배분 문항: %d" % grand)

    # 어느 절에도 안 걸린 출판사 해설 문항 확인
    used = set()
    for fp in glob.glob(os.path.join(args.out_dir, "*.json")):
        d = json.load(open(fp, encoding="utf-8"))
        for ch in d["chapters"]:
            for s in ch["sections"]:
                for q in s["questions"]:
                    used.add(q["ref"])
    miss = sorted(set(pub) - used, key=lambda r: tuple(int(x) for x in r.split("-")))
    print("절에 미연결: %d문항" % len(miss))
    if miss:
        print("   %s%s" % (", ".join(miss[:30]), " ..." if len(miss) > 30 else ""))


if __name__ == "__main__":
    main()
