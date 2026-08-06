# -*- coding: utf-8 -*-
"""이미지로만 있던 [보기] 지문을 텍스트로 보강.

comcbt PDF 파싱 당시 [보기] 박스가 그림으로 추출돼 DB text 에는
발문만 들어가고 지문은 text_image 로만 남은 문항이 있다.
출판사 문제집 PDF 에는 지문이 텍스트로 실려 있어 이를 옮긴다.

원칙
  - 발문(DB text)은 유지하고 그 뒤에 [box]지문[/box] 만 덧붙인다
  - 이미지(text_image)는 지우지 않는다 (원본 조판 확인용)
  - 이미 [box] 가 있는 문항은 건드리지 않는다

사용법:
    python merge_eco2022_box.py --src <파싱디렉토리>
    python merge_eco2022_box.py --src <파싱디렉토리> --apply
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT)

    pool = {}
    for fp in glob.glob(os.path.join(args.src, "*.json")):
        d = json.load(open(fp, encoding="utf-8"))
        for q in d.get("questions", []):
            k = (d["year"], d["round"], q["number"])
            if k not in pool or len(q.get("text") or "") > len(pool[k].get("text") or ""):
                pool[k] = q

    n_add = 0
    for (y, r, num), pq in sorted(pool.items()):
        ptext = pq.get("text") or ""
        m = re.search(r"\[box\](.+?)\[/box\]", ptext, re.DOTALL)
        if not m:
            continue

        dq = GisaQuestion.objects.filter(
            exam__certification=cert, exam__year=y, exam__round=r, number=num
        ).first()
        if dq is None or "[box]" in (dq.text or ""):
            continue

        box = m.group(1).strip()
        new_text = "%s\n[box]%s[/box]" % (dq.text.strip(), box)

        n_add += 1
        print("%d-%d-%d  +%d자" % (y, r, num, len(box)))
        print("    %s" % box[:78].replace("\n", " "))

        if args.apply:
            dq.text = new_text
            dq.save(update_fields=["text"])

    print()
    if args.apply:
        print("지문 보강 완료: %d문항" % n_add)
    else:
        print("보강 대상: %d문항 (--apply 로 반영)" % n_add)


if __name__ == "__main__":
    main()
