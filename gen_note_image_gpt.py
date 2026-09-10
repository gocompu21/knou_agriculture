"""쪽집게 노트용 인포그래픽·삽화를 OpenAI 이미지 모델로 만든다.

  python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png
  python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png --ref 참고.png
  python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png --size 1536x1024 --quality max

- 모델: gpt-image-2.5-sunburst (품질·편집 정밀도 우선. 속도를 원하면 --model 로 flare)
- --ref 를 주면 그 그림을 바탕으로 고쳐 그린다(images.edits). 없으면 새로 그린다.

**만든 뒤에는 반드시 Claude 가 그림을 직접 열어 보고 합격을 판정한다.**
사람 눈으로만 볼 일이 아니다 — 한글 오타는 작게 박혀 있어 놓치기 쉽다.
검증 기준과 고치는 법은 CLAUDE.md 의 "노트 인포그래픽 생성" 절에 있다.
회차마다 파일이 남도록 --out 에 _r2, _r3 를 붙이거나 --round 를 쓴다.

Gemini 판(gen_note_image.py)과 인자를 맞춰 두었다. 다른 점은 --aspect 대신
--size 를 쓴다는 것뿐이다(OpenAI 는 픽셀 크기를 받는다).
"""
import argparse
import base64
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from django.conf import settings  # noqa: E402

# 가로가 긴 인포그래픽이 기본. 세로는 1024x1536, 정사각은 1024x1024.
# 커스텀도 되지만 폭·높이가 16의 배수여야 하고 비율은 1:3~3:1 안이어야 한다.
DEFAULT_SIZE = "1536x1024"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="", help="참고 그림 — 주면 이것을 고쳐 그린다")
    ap.add_argument("--size", default=DEFAULT_SIZE)
    ap.add_argument("--quality", default="high",
                    choices=["low", "medium", "high", "xhigh", "max", "auto"])
    ap.add_argument("--model", default="")
    ap.add_argument("--round", type=int, default=0,
                    help="다시 만들 때 회차. 2 를 주면 out 이름 뒤에 _r2 가 붙어 "
                         "앞 회차를 덮지 않는다(무엇이 나아졌는지 견줄 수 있다)")
    args = ap.parse_args()

    out = args.out
    if args.round:
        stem, ext = os.path.splitext(out)
        out = f"{stem}_r{args.round}{ext}"

    key = getattr(settings, "OPENAI_API_KEY", "")
    if not key:
        print("OPENAI_API_KEY 가 없습니다. .env 에 넣어 주세요.")
        sys.exit(1)

    from openai import OpenAI

    model = args.model or settings.OPENAI_IMAGE_MODEL
    prompt = open(args.prompt_file, encoding="utf-8").read()
    client = OpenAI(api_key=key)

    print(f"모델 {model} | 크기 {args.size} | 품질 {args.quality}")
    if args.ref:
        print("참고 그림:", args.ref)
        with open(args.ref, "rb") as f:
            resp = client.images.edit(
                model=model, image=f, prompt=prompt,
                size=args.size, quality=args.quality,
            )
    else:
        resp = client.images.generate(
            model=model, prompt=prompt,
            size=args.size, quality=args.quality,
        )

    data = resp.data[0].b64_json
    if not data:
        print("이미지를 받지 못했습니다.")
        sys.exit(1)
    with open(out, "wb") as f:
        f.write(base64.b64decode(data))
    print("저장", out, os.path.getsize(out) // 1024, "KB")

    # 쓴 만큼만 확인 — 토큰 단가가 이미지 출력 $30/1M 이라 장당 비용이 여기서 나온다
    u = getattr(resp, "usage", None)
    if u:
        n = getattr(u, "output_tokens", 0) or 0
        print("토큰: 입력", getattr(u, "input_tokens", "?"), "/ 출력", n,
              f"(약 ${n * 30 / 1_000_000:.3f})" if n else "")
    print("→ 이제 이 그림을 열어 글자·내용을 확인할 것 (CLAUDE.md 검증 기준)")


main()
