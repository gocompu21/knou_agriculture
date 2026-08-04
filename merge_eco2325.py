# -*- coding: utf-8 -*-
"""자연생태복원기사 2023~2025 회차별 파싱 JSON을 합쳐 import 형식으로 변환.

회차별 에이전트가 만든 `eco2325_out/YYYY-R.json` 들을 읽어
`import_eco_questions` 가 먹는 `_eco_parsed_2325.json` 을 만든다.

사용법:
    python merge_eco2325.py [--src DIR] [--out FILE]
"""
import argparse
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_SRC = os.path.join(
    os.environ.get("TEMP", ""), "claude",
    "c--Users-gocom-Documents-Antigravity-Django-BaseCamp-knou-agriculture",
    "7c55dddf-8e30-47d3-808a-796a5d5060bb", "scratchpad", "eco2325_out",
)

SUBJECTS = {
    (1, 20): "생태환경조사분석",
    (21, 40): "생태복원계획",
    (41, 60): "생태복원설계·시공",
    (61, 80): "생태복원 사후관리·평가",
}


def subject_of(num):
    for (lo, hi), name in SUBJECTS.items():
        if lo <= num <= hi:
            return name
    return None


# 에이전트가 회차 메타 없이 저장한 중간 파일의 소속.
# (문항 텍스트를 각 회차 데이터와 대조해 확정한 값)
ORPHAN_OWNER = {
    "2024-1.part2.json": (2024, 1),
    "chunk2.json": (2023, 1),
    "q21_45.json": (2023, 3),
    "q46_66.json": (2023, 3),
    "q67_80.json": (2023, 3),
    # 2024-3 은 1~31 / 32~80 을 나눠 작업했다
    "2024-3.tail.json": (2024, 3),
    "2024-3.tail.partial.json": (2024, 3),
}

# 정답 띠와 해설이 충돌해 원본 확인 후 정정한 문항.
# (year, round, number) -> (정정 정답, 사유)
ANSWER_FIX = {
    (2025, 1, 49): ("2", "정답 띠는 ④(PP네트)이나, 해설 표에 '쥬트네트(jute net) = 황마 섬유'로 "
                         "명시되어 있다. PP네트는 폴리프로필렌(합성섬유)으로 황마와 무관하며 "
                         "해설 표에 등장하지도 않는다."),
    (2025, 1, 15): ("2", "정답 띠는 ③(취약 VU)이나, 해설 표 기준 CR은 '절멸 위급'이며 정의는 "
                         "'야생에서 절멸할 가능성이 대단히 높음'이다. 선지 ②는 명칭을 '절멸 위기'(EN의 명칭), "
                         "정의를 '가능성이 높음'(EN의 정의)으로 적어 둘 다 EN과 뒤바뀌었다. "
                         "선지 ③(VU)은 해설과 정확히 일치한다."),
    (2025, 1, 34): ("3", "정답 띠는 ④이나, 선지 ③이 적은 '특별시·광역시…의 개발·정비 및 보전을 위하여 "
                         "수립하는 계획'은 해설이 명시한 도시·군관리계획의 정의다. 국가계획은 "
                         "'중앙행정기관이 법률에 따라 수립하거나 국가의 정책적 목적을 이루기 위하여 "
                         "수립하는 계획'이다. 선지 ④는 「국토기본법」 환경친화적 국토관리 취지로 옳다."),
    (2025, 2, 29): ("3", "정답 띠는 ①(CBD)이나, CBD는 생물다양성협약(Convention on Biological "
                         "Diversity) 그 자체이므로 '생물다양성 관련 협약이 아닌 것'이 될 수 없다. "
                         "람사르협약(습지)·CITES(야생동식물 국제거래)도 생물다양성과 직결되나, "
                         "UNFCCC는 온실가스 규제를 목적으로 하는 기후변화협약이다."),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default="_eco_parsed_2325.json")
    ap.add_argument("--allow-partial", action="store_true",
                    help="80문항 미만 회차도 포함 (기본은 경고만)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, "*.json")))
    if not files:
        print("파싱 JSON 없음:", args.src)
        return

    # 회차별로 모든 조각을 모은다. 최종본(YYYY-R.json)이 중간본을 덮어쓴다.
    pool = {}          # (year, round) -> {number: q}
    for fp in files:
        name = os.path.basename(fp)
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list):
            qs, key = d, ORPHAN_OWNER.get(name)
        else:
            qs = d.get("questions", [])
            key = (d.get("year"), d.get("round")) if d.get("year") else ORPHAN_OWNER.get(name)
        if not key:
            print("  [소속 미상, 건너뜀] %s" % name)
            continue
        # 최종본이 나중에 처리되도록 정렬돼 있어 자연스럽게 덮어쓴다
        bucket = pool.setdefault(key, {})
        for q in qs:
            if q.get("number"):
                bucket[q["number"]] = q

    merged = []
    problems = []
    n_fixed = []
    total_q = 0

    for (year, rnd) in sorted(pool):
        qs = [pool[(year, rnd)][n] for n in sorted(pool[(year, rnd)])]
        tag = "%d-%d" % (year, rnd)

        seen = set()
        clean = []
        for q in qs:
            n = q["number"]
            if n in seen:
                problems.append("%s #%d 중복" % (tag, n))
                continue
            seen.add(n)

            # 과목은 번호 기준으로 재확정 (에이전트 값과 다르면 경고)
            want = subject_of(n)
            if want is None:
                problems.append("%s #%d 번호 범위 밖" % (tag, n))
                continue
            if q.get("subject") != want:
                problems.append("%s #%d 과목 보정: %s → %s"
                                % (tag, n, q.get("subject"), want))
            q["subject"] = want

            ch = q.get("choices") or []
            if len(ch) != 4:
                problems.append("%s #%d 보기 %d개" % (tag, n, len(ch)))
                ch = (ch + ["", "", "", ""])[:4]
                q["choices"] = ch

            if q.get("answer") in (None, "", "0"):
                problems.append("%s #%d 정답 미확인" % (tag, n))

            if not q.get("explanation"):
                problems.append("%s #%d 해설 없음" % (tag, n))

            # 원본 확인을 거친 정답 정정 적용
            fix = ANSWER_FIX.get((year, rnd, n))
            if fix:
                new_ans, reason = fix
                old = q.get("answer")
                if old != new_ans:
                    q["answer"] = new_ans
                    note = "\n\n※ 정답 정정: 이 문항은 문제집 정답표에 %s번으로 인쇄되어 있으나 %s번이 옳다. %s" % (
                        old, new_ans, reason)
                    q["explanation"] = (q.get("explanation") or "") + note
                    n_fixed.append("%s #%d  %s → %s" % (tag, n, old, new_ans))

            clean.append(q)

        missing = [n for n in range(1, 81) if n not in seen]
        if missing:
            problems.append("%s 누락 번호: %s" % (tag, missing))

        if len(clean) < 80 and not args.allow_partial:
            problems.append("%s 미완성(%d/80) — --allow-partial 없이는 제외" % (tag, len(clean)))
            print("%s  %2d문항  [미완성, 제외]" % (tag, len(clean)))
            continue

        clean.sort(key=lambda x: x["number"])
        merged.append({"year": year, "round": rnd, "questions": clean})
        total_q += len(clean)
        print("%s  %2d문항" % (tag, len(clean)))

    merged.sort(key=lambda d: (d["year"], d["round"]))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)

    print("\n합계: %d회차 · %d문항" % (len(merged), total_q))
    print("저장:", os.path.abspath(args.out))

    if n_fixed:
        print("\n[정답 정정 %d건 — 원본 확인 완료]" % len(n_fixed))
        for x in n_fixed:
            print("  ", x)

    if problems:
        print("\n[점검 필요 %d건]" % len(problems))
        for p in problems[:80]:
            print("  ", p)
        if len(problems) > 80:
            print("   ... 외 %d건" % (len(problems) - 80))
    else:
        print("\n점검 사항 없음")


if __name__ == "__main__":
    main()
