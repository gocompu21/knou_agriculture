# -*- coding: utf-8 -*-
"""검증을 마친 단일 지문 이미지를 반영한다. 원본은 .orig 로 백업."""
import argparse, io, os, shutil, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.conf import settings
from PIL import Image
from gisa.models import Certification, GisaQuestion

TARGET_W = 640  # .q-image 표시 상한 420px 의 약 1.5배
MARGIN = 20

def trim(im, margin=MARGIN):
    g = im.convert("L")
    mask = g.point(lambda p: 255 if p < 250 else 0)
    box = mask.getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(l-margin,0), max(t-margin,0),
                    min(r+margin,im.width), min(b+margin,im.height)))

ap = argparse.ArgumentParser()
ap.add_argument("--cert", required=True)
ap.add_argument("--year", type=int, required=True)
ap.add_argument("--round", type=int, required=True)
ap.add_argument("--number", type=int, required=True)
ap.add_argument("--src", required=True)
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()

cert = Certification.objects.get(name=a.cert)
q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=a.year,
                                exam__round=a.round, number=a.number).first()
dst_rel = q.text_image.name
dst = os.path.join(settings.MEDIA_ROOT, dst_rel)
im = Image.open(a.src).convert("RGB")
before = im.size
im = trim(im)
if im.width > TARGET_W:
    im = im.resize((TARGET_W, round(im.height*TARGET_W/im.width)), Image.LANCZOS)
print("%dx%d → %dx%d  → %s" % (before[0], before[1], im.width, im.height, dst_rel))
if a.apply:
    bak = dst + ".orig"
    if os.path.exists(dst) and not os.path.exists(bak):
        shutil.copy(dst, bak)
    im.save(dst, "PNG", optimize=True)
    print("반영 완료 (원본 .orig 백업) · %s bytes" % format(os.path.getsize(dst), ","))
else:
    print("미리보기 (--apply 로 반영)")
