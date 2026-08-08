# -*- coding: utf-8 -*-
"""서버 적재: 이미지로만 있던 지문을 텍스트로 복원한 230문항 반영.

`_deploy_eco_boxtext.json` 은 {ref, text} 목록이다.
text 에는 이미 `[box]...[/box]` 가 붙어 있으므로 그대로 덮어쓴다.
(text_image 는 건드리지 않는다 — 원본 대조용)

사용법 (서버):
    python load_eco_boxtext_deploy.py
"""
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
JSON_PATH = "_deploy_eco_boxtext.json"


def main():
    if not os.path.exists(JSON_PATH):
        print("JSON 없음:", JSON_PATH)
        return

    cert = Certification.objects.get(name=CERT)
    rows = json.load(open(JSON_PATH, encoding="utf-8"))

    n_upd = n_same = n_miss = 0
    for r in rows:
        try:
            y, rd, num = (int(x) for x in r["ref"].split("-"))
        except ValueError:
            continue
        q = GisaQuestion.objects.filter(
            exam__certification=cert, exam__year=y,
            exam__round=rd, number=num).first()
        if q is None:
            n_miss += 1
            print("  [DB 없음] %s" % r["ref"])
            continue
        if q.text == r["text"]:
            n_same += 1
            continue
        q.text = r["text"]
        q.save(update_fields=["text"])
        n_upd += 1

    print("반영 %d · 이미 동일 %d · 없음 %d (총 %d)"
          % (n_upd, n_same, n_miss, len(rows)))

    box = GisaQuestion.objects.filter(
        exam__certification=cert, text__contains="[box]").count()
    only_img = (GisaQuestion.objects
                .filter(exam__certification=cert)
                .exclude(text_image="")
                .exclude(text__contains="[box]").count())
    print("확인: [box] 보유 %d문항 · 이미지만 남은 문항 %d" % (box, only_img))


if __name__ == "__main__":
    main()
