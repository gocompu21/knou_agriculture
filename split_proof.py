# -*- coding: utf-8 -*-
"""교정 제안을 두 부류로 나눈다. DB 는 건드리지 않는다.

  A. 공백만 조정  — before/after 가 공백 제외하고 동일. 원문 글자 불변.
  B. 글자 변경 포함 — 원문 오식 수정이 섞임. 사람 판단 필요.
"""
import glob, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

A, B = [], []
for fp in sorted(glob.glob("_proof/*_fix.json")):
    d = json.load(open(fp, encoding="utf-8"))
    for f in d.get("fixes", []):
        b, a = f.get("before", ""), f.get("after", "")
        (A if b.replace(" ", "") == a.replace(" ", "") else B).append(f)

json.dump({"fixes": A}, open("_proof_A_spacing.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"fixes": B}, open("_proof_B_chars.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("A 공백만 조정   %d건 → _proof_A_spacing.json" % len(A))
print("B 글자 변경 포함 %d건 → _proof_B_chars.json" % len(B))
