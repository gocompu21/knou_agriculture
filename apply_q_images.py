# -*- coding: utf-8 -*-
"""검증을 마친 재생성 이미지를 문항 보기 이미지로 반영한다.

여백을 잘라내고 화면 표시 크기(.choice-image 는 최대 300px)에 맞춰
적당한 해상도로 줄인 뒤 저장한다. 원본은 `_orig` 접미사로 백업한다.

사용법:
    python apply_q_images.py --cert 자연생태복원기사 --year 2022 --round 1 \
        --number 16 --src _regen/2022-1-16 --attempt 1
    python apply_q_images.py ... --apply
"""
import argparse
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.conf import settings
from PIL import Image

from gisa.models import Certification, GisaQuestion

TARGET_W = 600      # .choice-image 표시 상한 300px 의 2배
MARGIN = 18         # 잘라낸 뒤 남길 흰 여백(px)


def trim(im, margin=MARGIN):
    """흰 여백을 잘라낸다."""
    g = im.convert("L")
    # 250 이상은 흰색으로 보고, 그보다 어두운 픽셀의 경계를 찾는다
    mask = g.point(lambda p: 255 if p < 250 else 0)
    box = mask.getbbox()
    if not box:
        return im
    l, t, r, b = box
    l = max(l - margin, 0)
    t = max(t - margin, 0)
    r = min(r + margin, im.width)
    b = min(b + margin, im.height)
    return im.crop((l, t, r, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--only", help="반영할 보기 번호 (예: 2,4)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    only = None
    if args.only:
        only = {int(x) for x in args.only.split(",") if x.strip()}

    cert = Certification.objects.get(name=args.cert)
    q = GisaQuestion.objects.filter(
        exam__certification=cert, exam__year=args.year,
        exam__round=args.round, number=args.number).first()
    if q is None:
        print("문항 없음")
        return

    for i in range(1, 5):
        if only and i not in only:
            continue
        src = os.path.join(args.src, "c%d_a%d.png" % (i, args.attempt))
        if not os.path.exists(src):
            print("보기%d: 생성본 없음 %s" % (i, src))
            continue

        field = getattr(q, "choice_%d_image" % i)
        if not field:
            print("보기%d: 대상 필드 비어 있음" % i)
            continue

        dst_rel = field.name
        dst = os.path.join(settings.MEDIA_ROOT, dst_rel)

        im = Image.open(src).convert("RGB")
        before = im.size
        im = trim(im)
        if im.width > TARGET_W:
            h = round(im.height * TARGET_W / im.width)
            im = im.resize((TARGET_W, h), Image.LANCZOS)

        print("보기%d  %dx%d → %dx%d  → %s"
              % (i, before[0], before[1], im.width, im.height, dst_rel))

        if args.apply:
            bak = dst + ".orig"
            if os.path.exists(dst) and not os.path.exists(bak):
                shutil.copy(dst, bak)
            im.save(dst, "PNG", optimize=True)

    print()
    if args.apply:
        print("반영 완료 (원본은 .orig 로 백업)")
    else:
        print("미리보기만 수행 (--apply 로 반영)")


if __name__ == "__main__":
    main()
