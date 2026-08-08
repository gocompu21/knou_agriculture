# -*- coding: utf-8 -*-
"""저화질 보기 이미지를 Gemini 로 깨끗하게 다시 그린다.

원본 이미지를 함께 넘겨(image-to-image) 형태가 바뀌지 않도록 한다.
텍스트 프롬프트만 쓰면 해석이 한 번 더 끼어들어 곡선 모양이 달라질 수 있다.

★ 4개 보기를 한 장에 함께 그린 뒤 4등분한다.
   보기를 한 장씩 따로 생성하면 폰트 크기·선 굵기가 제각각이 된다
   (실제로 그렇게 나왔다). 한 번에 그리면 같은 스타일이 강제된다.

생성만 하고 DB 는 건드리지 않는다. 결과를 눈으로 검증한 뒤
apply_q_images.py 로 반영한다.

사용법:
    python regen_q_images.py --cert 자연생태복원기사 --year 2022 --round 1 --number 16 \
        --shapes _regen_q16_shapes.txt --out-dir _regen/2022-1-16 --attempt 2
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

GRID_PROMPT = """The 4 attached images are the four answer choices of a single
Korean certification exam question. They are low-resolution scans.

Redraw ALL FOUR as one image: a 2x2 grid of four line charts.
This is a REPRODUCTION task, not a redesign.

=== CRITICAL: ALL FOUR PANELS MUST LOOK IDENTICAL IN STYLE ===
They sit side by side as answer choices, so any style difference between panels
is a defect. Every panel must use:
- the SAME axis line thickness
- the SAME curve line thickness (same as or slightly thicker than the axes)
- the SAME Korean label font size
- the SAME plot area size and the SAME position within its cell
- the SAME margins
Do not make one panel's text bigger than another's. Do not vary line weights.

=== LAYOUT OF EACH PANEL ===
- L-shaped axes only: one vertical line on the left, one horizontal line at the
  bottom. No box, no frame, no border around the plot.
- Vertical axis label "종다양성" written vertically (one character per line),
  placed to the LEFT of the vertical axis, vertically centered on the axis.
- Horizontal axis label "이질성" placed BELOW the horizontal axis at its right end.
- Labels must be small and unobtrusive — clearly smaller than the plot itself.

=== CURVES MUST STAY INSIDE THE PLOT ===
Every curve and line must begin and end INSIDE the plot area.
- No line may cross, touch, or extend past the right edge of the plot.
  Stop it clearly short of the right end (leave a visible gap).
- No line may go below the horizontal axis. A line that reaches zero must
  stop exactly ON the horizontal axis, never below it.
- No line may extend past the vertical axis on the left.
Drawing outside the axes is a defect.

=== FORBIDDEN in every panel ===
gridlines, tick marks, numbers, scales, legends, titles, colors, arrows,
annotations, extra curves, English text, panel numbers, captions, and any
separating lines between the four cells.

=== STYLE ===
Pure white background. Thin solid black lines only. Crisp vector-like edges.
No scan noise, no shading, no anti-aliasing artifacts.

=== THE CURVE IN EACH PANEL (keep the exact shape of the original) ===
Top-left panel (choice 1): %s

Top-right panel (choice 2): %s

Bottom-left panel (choice 3): %s

Bottom-right panel (choice 4): %s

=== FINAL CHECK BEFORE YOU FINISH ===
Look at the bottom-right panel again. Its descending straight line must END
exactly where it meets the horizontal axis, and that meeting point must be
clearly to the LEFT of the right end of the axis. The line must not continue
below or past the axis. If it does, redraw that panel.
"""


def load_shapes(path):
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().isdigit():
            out[int(k.strip())] = v.strip()
    return out


def split_grid(path, out_dir, attempt):
    """2x2 격자 이미지를 4장으로 자른다."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    cw, ch = w // 2, h // 2
    boxes = {
        1: (0, 0, cw, ch),
        2: (cw, 0, w, ch),
        3: (0, ch, cw, h),
        4: (cw, ch, w, h),
    }
    made = []
    for i, box in boxes.items():
        p = os.path.join(out_dir, "c%d_a%d.png" % (i, attempt))
        im.crop(box).save(p, "PNG")
        made.append(p)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--shapes")
    ap.add_argument("--attempt", type=int, default=1)
    ap.add_argument("--aspect", default="16:9", help="격자 전체 비율")
    args = ap.parse_args()

    shapes = load_shapes(args.shapes)

    cert = Certification.objects.get(name=args.cert)
    q = GisaQuestion.objects.filter(
        exam__certification=cert, exam__year=args.year,
        exam__round=args.round, number=args.number).first()
    if q is None:
        print("문항 없음")
        return

    os.makedirs(args.out_dir, exist_ok=True)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    # 2x2 격자를 16:9 로 만들면 각 칸이 8:9... 가 아니라 가로형이 된다.
    # 원본 보기 이미지가 가로형(비율 약 1.3)이라 정사각으로 자르면
    # 세로 여백이 커 보인다. 격자 전체를 가로로 길게 뽑아 맞춘다.
    cfg = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=args.aspect),
    )

    parts = []
    for i in range(1, 5):
        field = getattr(q, "choice_%d_image" % i)
        src = os.path.join(settings.MEDIA_ROOT, field.name)
        # 원본이 이미 교체됐다면 .orig 백업을 쓴다
        if os.path.exists(src + ".orig"):
            src = src + ".orig"
        if not os.path.exists(src):
            print("보기%d: 원본 없음" % i)
            return
        parts.append(types.Part.from_bytes(
            data=open(src, "rb").read(), mime_type="image/png"))

    prompt = GRID_PROMPT % tuple(
        shapes.get(i, "(follow the attached original exactly)") for i in range(1, 5))
    parts.append(types.Part.from_text(text=prompt))

    print("문항: %d-%d #%d" % (args.year, args.round, args.number))
    print("4개 보기를 한 장에 함께 생성 (스타일 통일)")

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

    grid = os.path.join(args.out_dir, "grid_a%d.png" % args.attempt)
    open(grid, "wb").write(got)
    im = Image.open(grid)
    print("격자 %dx%d → %s" % (im.width, im.height, os.path.basename(grid)))

    for p in split_grid(grid, args.out_dir, args.attempt):
        print("  %s" % os.path.basename(p))

    print()
    print("출력:", os.path.abspath(args.out_dir))
    print("→ 격자 이미지를 먼저 보고 4개 패널의 스타일이 같은지 확인할 것")


if __name__ == "__main__":
    main()
