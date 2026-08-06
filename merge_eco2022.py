# -*- coding: utf-8 -*-
"""자연생태복원기사 2020-3/2021-2/2022-1 출판사 해설 병합·검증.

이 세 회차는 이미 DB에 문항이 있으나 해설이 Gemini 생성분(평균 131~141자)이다.
출판사 문제집 PDF에서 추출한 해설(평균 300~500자)로 교체한다.

원칙
  - 문항·보기 텍스트는 DB 값을 유지한다 (파싱 오차보다 기존 데이터가 안정적)
  - 정답이 다르면 교체하지 않고 **보고만** 한다 (사람이 판단할 사안)
  - 출판사 해설이 없는 문항은 기존 해설을 **그대로 둔다**

사용법:
    python merge_eco2022.py --src <파싱디렉토리>           # 검증만
    python merge_eco2022.py --src <파싱디렉토리> --apply   # DB 반영
"""
import argparse
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaQuestion

CERT = "자연생태복원기사"


def norm(s):
    """비교용 정규화 — 공백·괄호·기호 제거"""
    return re.sub(r"[^\w가-힣]", "", re.sub(r"\[/?box\]", "", s or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT)

    pool = {}          # (year, round, number) -> parsed question
    for fp in sorted(glob.glob(os.path.join(args.src, "*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        for q in d.get("questions", []):
            key = (d["year"], d["round"], q["number"])
            # 같은 문항이 두 파일에 있으면 해설이 긴 쪽을 취한다
            old = pool.get(key)
            if old and len(old.get("explanation") or "") >= len(q.get("explanation") or ""):
                continue
            pool[key] = q

    print("파싱 문항 %d개" % len(pool))
    print()

    ans_diff = []      # 정답 불일치
    txt_diff = []      # 문항 텍스트 불일치
    no_exp = []        # 출판사 해설 없음
    n_upd = 0

    for (y, r, n), pq in sorted(pool.items()):
        dq = GisaQuestion.objects.filter(
            exam__certification=cert, exam__year=y, exam__round=r, number=n
        ).first()
        if dq is None:
            print("  [DB 없음] %d-%d-%d" % (y, r, n))
            continue

        if pq.get("answer") not in ("0", "", None) and pq["answer"] != dq.answer:
            ans_diff.append((y, r, n, dq.answer, pq["answer"], dq.text[:46]))

        if norm(pq.get("text", ""))[:40] != norm(dq.text)[:40]:
            txt_diff.append((y, r, n, dq.text[:40], pq.get("text", "")[:40]))

        exp = (pq.get("explanation") or "").strip()
        if not exp:
            no_exp.append("%d-%d-%d" % (y, r, n))
            continue

        if args.apply:
            dq.explanation = exp
            dq.save(update_fields=["explanation"])
        n_upd += 1

    print("[정답 불일치] %d건" % len(ans_diff))
    for y, r, n, a, b, t in ans_diff:
        print("   %d-%d-%d  DB=%s / 문제집=%s   %s" % (y, r, n, a, b, t))

    print()
    print("[문항 텍스트 불일치] %d건" % len(txt_diff))
    for y, r, n, a, b in txt_diff[:12]:
        print("   %d-%d-%d" % (y, r, n))
        print("      DB  : %s" % a)
        print("      PDF : %s" % b)

    print()
    print("[출판사 해설 없음] %d건 — 기존 해설 유지" % len(no_exp))
    if no_exp:
        print("   %s%s" % (", ".join(no_exp[:20]), " ..." if len(no_exp) > 20 else ""))

    print()
    if args.apply:
        print("해설 교체 완료: %d문항" % n_upd)
    else:
        print("교체 대상: %d문항 (--apply 로 반영)" % n_upd)


if __name__ == "__main__":
    main()
