# -*- coding: utf-8 -*-
"""자연생태복원기사 쪽집게 노트를 서버 DB에 적재.

사용법 (서버):
    python load_eco_textbook_deploy.py
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaSubject, GisaTextbook

JSON_PATH = "_deploy_eco_textbook.json"


def main():
    if not os.path.exists(JSON_PATH):
        print("JSON 없음:", JSON_PATH)
        return

    with open(JSON_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    for r in rows:
        cert = Certification.objects.get(name=r["cert"])
        subj = GisaSubject.objects.get(certification=cert, name=r["subject"])
        tb, created = GisaTextbook.objects.update_or_create(
            certification=cert, subject=subj,
            defaults={"content": r["content"]},
        )
        print("%s %s: %s (%s자)"
              % (r["cert"], r["subject"],
                 "생성" if created else "갱신", format(len(r["content"]), ",")))

    print("\n완료: %d개 과목" % len(rows))


if __name__ == "__main__":
    main()
