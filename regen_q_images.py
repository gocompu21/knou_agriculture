# -*- coding: utf-8 -*-
"""저화질 보기 이미지를 Gemini 로 깨끗하게 다시 그린다.

원본 이미지를 함께 넘겨(image-to-image) 형태가 바뀌지 않도록 한다.
텍스트 프롬프트만 쓰면 해석이 한 번 더 끼어들어 곡선 모양이 달라질 수 있다.

생성만 하고 DB 는 건드리지 않는다. 결과를 사람이(또는 LLM 이) 눈으로 검증한 뒤
apply_q_images.py 로 반영한다.

사용법:
    python regen_q_images.py --cert 자연생태복원기사 --year 2022 --round 1 --number 16 \
        --out-dir _regen/2022-1-16
    # 특정 보기만 재시도
    python regen_q_images.py ... --only 2,4 --attempt 2
"""
import argparse
import base64
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.conf import settings

from gisa.models import Certification, GisaQuestion

MODEL = "gemini-3-pro-image-preview"

# 그래프 문항 공통 지시. 원본을 그대로 두고 '화질만' 올리는 게 목적이다.
BASE_PROMPT = """This is a low-resolution scanned figure from a Korean certification exam question.

Redraw it as a clean, high-resolution line chart. This is a REPRODUCTION task,
not a redesign task.

ABSOLUTE REQUIREMENTS — the meaning must not change:
- Keep the EXACT same curve shape and trend as the original. Do not smooth away,
  exaggerate, or reinterpret the shape. If the original curve rises then falls,
  the new one must rise then fall at the same relative position.
- Keep the same axes: vertical axis on the left, horizontal axis at the bottom,
  forming an L shape. Do not add a box/frame around the plot.
- Keep the Korean axis labels EXACTLY as they are:
  vertical axis label "종다양성" (written vertically, one character per line,
  placed to the left of the vertical axis),
  horizontal axis label "이질성" (placed at the right end, below the horizontal axis).
- Do NOT add: gridlines, tick marks, numbers, scales, legends, titles, colors,
  arrows, annotations, extra curves, or any English text.

STYLE:
- Pure white background. Solid black thin lines only (no color, no shading).
- Clean vector-like appearance, crisp edges, no scan noise, no JPEG artifacts.
- Simple and minimal, like a textbook diagram.

THE CURVE IN THIS PARTICULAR IMAGE: %s
"""

# 보기별 곡선 형태 (원본을 직접 판독한 결과)
SHAPES = {}


def load_shapes(path):
    """--shapes 파일에서 보기별 곡선 서술을 읽는다. `1: 설명` 형식."""
    if not path or not os.path.exists(path):
        return {}
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        if k.isdigit():
            out[int(k)] = v.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--shapes", help="보기별 곡선 서술 파일 (`1: ...` 형식)")
    ap.add_argument("--only", help="재생성할 보기 번호 (예: 2,4)")
    ap.add_argument("--attempt", type=int, default=1, help="시도 회차 (파일명에 붙는다)")
    args = ap.parse_args()

    shapes = load_shapes(args.shapes)
    if not shapes:
        print("[경고] --shapes 파일이 없어 곡선 서술 없이 진행한다")

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

    os.makedirs(args.out_dir, exist_ok=True)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    cfg = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="4:3"),
    )

    print("문항: %d-%d #%d  %s" % (args.year, args.round, args.number, q.text[:44]))
    print()

    for i in range(1, 5):
        if only and i not in only:
            continue
        field = getattr(q, "choice_%d_image" % i)
        if not field:
            print("보기%d: 이미지 없음 — 건너뜀" % i)
            continue

        src = os.path.join(settings.MEDIA_ROOT, field.name)
        if not os.path.exists(src):
            print("보기%d: 파일 없음 %s" % (i, src))
            continue

        raw = open(src, "rb").read()
        desc = shapes.get(i, "(no description provided — follow the original exactly)")
        prompt = BASE_PROMPT % desc

        contents = [types.Content(role="user", parts=[
            types.Part.from_bytes(data=raw, mime_type="image/png"),
            types.Part.from_text(text=prompt),
        ])]

        got = None
        err = None
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=MODEL, contents=contents, config=cfg)
                if resp.candidates and resp.candidates[0].content:
                    for part in resp.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            got = part.inline_data.data
                            break
                if got:
                    break
                err = "이미지 없는 응답"
            except Exception as e:  # noqa: BLE001
                err = str(e)[:120]
            time.sleep(2)

        if not got:
            print("보기%d: 생성 실패 (%s)" % (i, err))
            continue

        dst = os.path.join(args.out_dir, "c%d_a%d.png" % (i, args.attempt))
        open(dst, "wb").write(got)
        print("보기%d → %s (%s bytes)"
              % (i, os.path.basename(dst), format(len(got), ",")))

    print()
    print("출력:", os.path.abspath(args.out_dir))
    print("→ 이미지를 눈으로 검증한 뒤 apply_q_images.py 로 반영할 것")


if __name__ == "__main__":
    main()
