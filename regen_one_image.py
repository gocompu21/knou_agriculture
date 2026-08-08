# -*- coding: utf-8 -*-
"""지문 이미지 1건을 Gemini 로 다시 그린다 (보기 4개짜리가 아닌 단일 그림용).

원본을 함께 넘기고, 그림 내용을 서술한 프롬프트 파일을 별도로 준다.
격자·도면처럼 값의 배치가 곧 문제 조건인 그림은 서술을 아주 구체적으로
적어야 한다.

사용법:
    python regen_one_image.py --cert 자연생태복원기사 --year 2022 --round 2 \
        --number 46 --prompt _regen_2022-2-46.txt --out-dir _regen/2022-2-46 --attempt 1
"""
import argparse
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.conf import settings
from PIL import Image

from gisa.models import Certification, GisaQuestion

MODEL = "gemini-3-pro-image-preview"

HEADER = """The attached image is a low-resolution scanned figure from a Korean
certification exam question.

Redraw it cleanly at high resolution. This is a REPRODUCTION task, not a redesign.
The figure IS the question data — if any number or its position changes, the
question becomes unanswerable. Reproduce it exactly.

STYLE:
- Pure white background, solid black thin lines, crisp vector-like edges.
- No color, no shading, no scan noise, no drop shadows.
- Clean sans-serif text, all labels the same size, clearly legible.
- No title, no caption, no legend, no extra annotation of any kind.

%s
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--prompt", required=True, help="그림 내용 서술 파일")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--aspect", default="4:3")
    args = ap.parse_args()

    cert = Certification.objects.get(name=args.cert)
    q = GisaQuestion.objects.filter(
        exam__certification=cert, exam__year=args.year,
        exam__round=args.round, number=args.number).first()
    if q is None or not q.text_image:
        print("문항 또는 이미지 없음")
        return

    src = os.path.join(settings.MEDIA_ROOT, q.text_image.name)
    if os.path.exists(src + ".orig"):
        src = src + ".orig"
    if not os.path.exists(src):
        print("원본 파일 없음:", src)
        return

    desc = open(args.prompt, encoding="utf-8").read().strip()
    prompt = HEADER % desc

    os.makedirs(args.out_dir, exist_ok=True)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    cfg = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=args.aspect),
    )

    parts = [
        types.Part.from_bytes(data=open(src, "rb").read(), mime_type="image/png"),
        types.Part.from_text(text=prompt),
    ]

    print("문항: %d-%d #%d" % (args.year, args.round, args.number))
    print("원본: %s" % os.path.basename(src))

    got = None
    err = None
    for _ in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=[types.Content(role="user", parts=parts)],
                config=cfg)
            if resp.candidates and resp.candidates[0].content:
                for p in resp.candidates[0].content.parts:
                    if p.inline_data and p.inline_data.data:
                        got = p.inline_data.data
                        break
            if got:
                break
            err = "이미지 없는 응답"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:140]
        time.sleep(2)

    if not got:
        print("생성 실패:", err)
        return

    dst = os.path.join(args.out_dir, "a%d.png" % args.attempt)
    open(dst, "wb").write(got)
    im = Image.open(dst)
    print("생성 %dx%d → %s (%s bytes)"
          % (im.width, im.height, os.path.basename(dst), format(len(got), ",")))
    print()
    print("→ 반드시 눈으로 원본과 대조할 것")


if __name__ == "__main__":
    main()
