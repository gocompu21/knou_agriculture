# -*- coding: utf-8 -*-
"""지문이 [box] 텍스트로 복원된 문항의 중복 이미지를 제거한다.

같은 내용이 텍스트와 이미지로 두 번 표시되므로 이미지를 떼어낸다.
`text_image` 필드만 비우고 **파일은 지우지 않는다** — 되돌릴 수 있게 남긴다.

안전장치
  - 판독 결과에서 kind="image" 로 판정된 문항은 대상에서 제외 (진짜 그림)
  - [box] 텍스트가 없는 문항은 대상 아님
  - 보기 이미지(choice_N_image)는 건드리지 않는다 (그림 선택지일 수 있다)
  - 텍스트가 지나치게 짧으면(20자 미만) 보고만 하고 건너뛴다

사용법:
    python clear_dup_images.py                # 대상 확인만
    python clear_dup_images.py --apply        # 필드 비우기
    python clear_dup_images.py --restore      # 되돌리기 (백업 JSON 필요)
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

from gisa.models import Certification, GisaQuestion

CERT = "자연생태복원기사"
BACKUP = "_dup_image_backup.json"
MIN_BOX_LEN = 20


def load_image_refs():
    """판독 결과에서 kind="image" 로 남긴 ref = 진짜 그림이라 건드리면 안 된다."""
    keep = set()
    for fp in glob.glob("_eco_boximg/*_done.json"):
        for q in json.load(open(fp, encoding="utf-8")).get("questions", []):
            if q.get("kind") == "image":
                keep.add(q["ref"])
    return keep


def box_text(text):
    import re
    m = re.search(r"\[box\](.*?)\[/box\]", text or "", re.DOTALL)
    return m.group(1).strip() if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT)

    if args.restore:
        if not os.path.exists(BACKUP):
            print("백업 없음:", BACKUP)
            return
        rows = json.load(open(BACKUP, encoding="utf-8"))
        n = 0
        for r in rows:
            q = GisaQuestion.objects.filter(pk=r["pk"]).first()
            if q and not q.text_image:
                q.text_image = r["text_image"]
                q.save(update_fields=["text_image"])
                n += 1
        print("복원 %d문항" % n)
        return

    keep = load_image_refs()
    print("진짜 그림으로 판정돼 보존할 문항: %d" % len(keep))
    print()

    qs = (GisaQuestion.objects
          .filter(exam__certification=cert, text__contains="[box]")
          .exclude(text_image="")
          .select_related("exam"))

    targets = []
    skipped = []
    for q in qs:
        ref = "%d-%d-%d" % (q.exam.year, q.exam.round, q.number)
        if ref in keep:
            skipped.append((ref, "그림으로 판정됨"))
            continue
        box = box_text(q.text)
        if len(box) < MIN_BOX_LEN:
            skipped.append((ref, "박스 텍스트 %d자 — 확인 필요" % len(box)))
            continue
        targets.append((ref, q))

    print("중복 이미지 제거 대상: %d문항" % len(targets))
    print("건너뜀: %d문항" % len(skipped))
    for ref, why in skipped[:15]:
        print("   %-10s %s" % (ref, why))

    if not args.apply:
        print()
        print("확인만 수행 (--apply 로 반영)")
        return

    backup = []
    for ref, q in targets:
        backup.append({"pk": q.pk, "ref": ref, "text_image": q.text_image.name})
    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=1)

    for ref, q in targets:
        q.text_image = ""
        q.save(update_fields=["text_image"])

    print()
    print("제거 완료: %d문항 (파일은 그대로, 필드만 비움)" % len(targets))
    print("백업: %s → --restore 로 되돌릴 수 있다" % BACKUP)


if __name__ == "__main__":
    main()
