# -*- coding: utf-8 -*-
"""이미지로만 있던 지문을 판독 결과(JSON)로 DB에 반영.

에이전트가 낸 결과 형식 (회차별 *_done.json):
    {"round": "2012-1",
     "questions": [
        {"ref": "2012-1-5", "kind": "text", "box": "지문 원문..."},
        {"ref": "2012-1-9", "kind": "image"}
     ]}

  kind="text"  → 발문 뒤에 [box]...[/box] 를 덧붙인다 (이미지는 지우지 않는다)
  kind="image" → 그림이므로 건드리지 않는다

원칙
  - 발문(DB text)은 유지하고 그 뒤에 박스만 붙인다
  - 이미 [box] 가 있으면 건너뛴다 (재실행 안전)
  - text_image 는 삭제하지 않는다 (원본 대조용)

사용법:
    python load_eco_boximg.py --src _eco_boximg          # 검증만
    python load_eco_boximg.py --src _eco_boximg --apply  # DB 반영
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT)

    files = sorted(glob.glob(os.path.join(args.src, "*_done.json")))
    if not files:
        print("판독 결과 파일(*_done.json)이 없다:", args.src)
        return

    n_text = n_img = n_skip = n_miss = 0
    applied = 0
    short = []

    for fp in files:
        d = json.load(open(fp, encoding="utf-8"))
        for q in d.get("questions", []):
            ref = q.get("ref", "")
            kind = (q.get("kind") or "").strip()
            try:
                y, r, num = (int(x) for x in ref.split("-"))
            except ValueError:
                print("  [ref 이상] %s (%s)" % (ref, os.path.basename(fp)))
                continue

            dq = GisaQuestion.objects.filter(
                exam__certification=cert, exam__year=y,
                exam__round=r, number=num).first()
            if dq is None:
                n_miss += 1
                print("  [DB 없음] %s" % ref)
                continue

            if kind == "image":
                n_img += 1
                continue

            box = (q.get("box") or "").strip()
            if not box:
                print("  [box 비었음] %s" % ref)
                continue

            if "[box]" in (dq.text or ""):
                n_skip += 1
                continue

            if len(box) < 10:
                short.append((ref, box))

            n_text += 1
            if args.apply:
                dq.text = "%s\n[box]%s[/box]" % (dq.text.strip(), box)
                dq.save(update_fields=["text"])
                applied += 1

    print()
    print("판독 결과 %d회차" % len(files))
    print("  텍스트 지문   %d" % n_text)
    print("  그림(유지)    %d" % n_img)
    print("  이미 [box]    %d" % n_skip)
    print("  DB 없음       %d" % n_miss)
    if short:
        print("  ※ 10자 미만 의심 %d건: %s" % (len(short), short[:5]))
    print()
    if args.apply:
        print("DB 반영 완료: %d문항" % applied)
    else:
        print("반영 대상 %d문항 (--apply 로 저장)" % n_text)


if __name__ == "__main__":
    main()
