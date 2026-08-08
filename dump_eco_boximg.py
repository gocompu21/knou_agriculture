# -*- coding: utf-8 -*-
"""자연생태복원기사: 지문이 이미지로만 있는 문항을 판독 배치로 추출.

`text_image` 는 있는데 본문에 `[box]` 텍스트가 없는 문항이 대상이다.
이미지가 순수 텍스트 박스면 텍스트로 옮기고(그림이면 그대로 둔다),
에이전트가 이미지를 직접 읽어 판단한다.

사용법:
    python dump_eco_boximg.py --out-dir _eco_boximg
"""
import argparse
import io
import json
import os
import shutil
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.conf import settings

from gisa.models import Certification, GisaQuestion

CERT = "자연생태복원기사"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT)
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert)
          .exclude(text_image="")
          .exclude(text__contains="[box]")
          .select_related("exam", "subject")
          .order_by("exam__year", "exam__round", "number"))

    os.makedirs(args.out_dir, exist_ok=True)
    by_round = defaultdict(list)
    n_img = n_miss = 0

    for q in qs:
        key = "%d-%d" % (q.exam.year, q.exam.round)
        src = os.path.join(settings.MEDIA_ROOT, q.text_image.name)
        img_dir = os.path.join(args.out_dir, key)
        os.makedirs(img_dir, exist_ok=True)
        fname = "%d.png" % q.number
        dst = os.path.join(img_dir, fname)

        if os.path.exists(src):
            shutil.copy(src, dst)
            n_img += 1
        else:
            fname = ""
            n_miss += 1

        by_round[key].append({
            "id": q.pk,
            "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
            "number": q.number,
            "subject": q.subject.name,
            "image": fname,
            "text": q.text,
            "choices": [q.choice_1, q.choice_2, q.choice_3, q.choice_4],
            "answer": q.answer,
        })

    for key, items in sorted(by_round.items()):
        fp = os.path.join(args.out_dir, "%s.json" % key)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"round": key, "questions": items}, f,
                      ensure_ascii=False, indent=1)

    print("대상 %d문항 · 이미지 복사 %d · 파일없음 %d"
          % (qs.count(), n_img, n_miss))
    print("회차 %d개 → %s" % (len(by_round), os.path.abspath(args.out_dir)))
    for key, items in sorted(by_round.items(),
                             key=lambda kv: tuple(int(x) for x in kv[0].split("-"))):
        print("   %-8s %3d문항" % (key, len(items)))


if __name__ == "__main__":
    main()
