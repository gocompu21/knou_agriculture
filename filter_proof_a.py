# -*- coding: utf-8 -*-
"""A(공백만 조정) 중 안전한 것만 추린다.

제외 대상
  1. confidence: low
  2. 파싱이 붕괴돼 추정 복원이 들어간 문항 (에이전트가 원본 확인 필요로 표시)
  3. 내용이 이미 유실된 문항
"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 에이전트들이 "원본 대조 필수" 로 지목한 문항
DANGER = {
    # 선지 4칸이 서로 밀려 잘림 / 문제 텍스트가 선지로 넘어감
    "2012-1-63", "2012-2-73", "2012-2-84", "2012-2-90",
    "2013-1-100", "2013-2-92", "2013-3-14", "2013-3-81",
    "2013-3-93", "2013-3-98",
    "2016-3-94", "2020-2-99", "2020-2-38",
    # 내용 유실
    "2013-2-65", "2013-3-54", "2012-2-100",
    # 제안 자체가 오류
    "2022-2-41",
    # 2024-1-18 은 발문이 다른 문항 것으로 보임
    "2024-1-18",
}

A = json.load(open("_proof_A_spacing.json", encoding="utf-8"))["fixes"]
keep, drop_low, drop_danger = [], [], []
for f in A:
    if f.get("ref") in DANGER:
        drop_danger.append(f)
    elif f.get("confidence") != "high":
        drop_low.append(f)
    else:
        keep.append(f)

json.dump({"fixes": keep}, open("_proof_A_safe.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("A 전체        %d건" % len(A))
print("  제외 low     %d건" % len(drop_low))
print("  제외 위험문항 %d건 (%s)" % (len(drop_danger),
      ", ".join(sorted({f["ref"] for f in drop_danger})) or "없음"))
print("  → 반영 대상  %d건  (_proof_A_safe.json)" % len(keep))
