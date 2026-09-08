"""쪽집게 노트용 인포그래픽·삽화를 Gemini 이미지 모델로 만든다.

  python gen_note_image.py --prompt-file _p.txt --out _out.png [--ref 참고.png] [--aspect 16:9]

- 모델: gemini-3-pro-image-preview (1장 약 $0.13)
- 결과는 그대로 저장한다. 오타·중복 검사는 사람이(또는 Claude가) 눈으로 하고
  필요하면 다시 돌린다 — 한글 글자는 자주 깨지므로 프롬프트에 정확한 문자열을 준다.
"""
import argparse
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from django.conf import settings  # noqa: E402

MODEL = "gemini-3-pro-image-preview"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="")
    ap.add_argument("--aspect", default="16:9")
    args = ap.parse_args()

    from google import genai
    from google.genai import types

    prompt = open(args.prompt_file, encoding="utf-8").read()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    cfg = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=args.aspect),
    )
    parts = []
    if args.ref:
        mime = "image/jpeg" if args.ref.lower().endswith((".jpg", ".jpeg")) else "image/png"
        parts.append(types.Part.from_bytes(data=open(args.ref, "rb").read(), mime_type=mime))
    parts.append(types.Part.from_text(text=prompt))

    resp = client.models.generate_content(model=MODEL, contents=parts, config=cfg)
    got = None
    for cand in resp.candidates or []:
        for p in cand.content.parts or []:
            if p.inline_data and p.inline_data.data:
                got = p.inline_data.data
                break
        if got:
            break
    if not got:
        print("이미지를 받지 못했습니다:", getattr(resp, "text", "")[:300])
        sys.exit(1)
    with open(args.out, "wb") as f:
        f.write(got)
    print("saved", args.out, len(got), "bytes")


if __name__ == "__main__":
    main()
