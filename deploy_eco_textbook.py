# -*- coding: utf-8 -*-
"""자연생태복원기사 쪽집게 노트를 과목 단위로 export/load.

기존 load_eco_textbook_deploy.py 는 전체 과목을 한 번에 다뤘으나,
과목이 완성되는 대로 하나씩 배포할 수 있게 분리했다.

로컬(추출):
    python deploy_eco_textbook.py export 생태환경조사분석
    python deploy_eco_textbook.py export            # 전체

서버(적재):
    python deploy_eco_textbook.py load
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

CERT_NAME = "자연생태복원기사"
JSON_PATH = "_deploy_eco_textbook_new.json"

# 신 체계 4과목 order (기존 배포와 일치)
SUBJECT_ORDER = {
    "생태환경조사분석": 6,
    "생태복원계획": 7,
    "생태복원설계·시공": 8,
    "생태복원 사후관리·평가": 9,
}


def export(subjects=None):
    cert = Certification.objects.get(name=CERT_NAME)
    qs = GisaTextbook.objects.filter(certification=cert).select_related("subject")
    if subjects:
        qs = qs.filter(subject__name__in=subjects)

    rows = []
    for tb in qs.order_by("subject__order"):
        rows.append({
            "cert": CERT_NAME,
            "subject": tb.subject.name,
            "order": tb.subject.order,
            "content": tb.content,
        })
        print("%-22s %s자" % (tb.subject.name, format(len(tb.content), ",")))

    if not rows:
        print("대상 없음")
        return

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    print("\n저장: %s (%s bytes)"
          % (JSON_PATH, format(os.path.getsize(JSON_PATH), ",")))


def load():
    if not os.path.exists(JSON_PATH):
        print("JSON 없음:", JSON_PATH)
        return

    with open(JSON_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    cert = Certification.objects.get(name=CERT_NAME)
    print("자격증: %s (pk=%d)" % (cert.name, cert.pk))

    for r in rows:
        subj, created = GisaSubject.objects.get_or_create(
            certification=cert, name=r["subject"],
            defaults={"order": r.get("order") or SUBJECT_ORDER.get(r["subject"], 99)},
        )
        if created:
            print("  과목 생성: %s (pk=%d)" % (subj.name, subj.pk))

        tb, made = GisaTextbook.objects.update_or_create(
            certification=cert, subject=subj,
            defaults={"content": r["content"]},
        )
        print("  %-22s %s (%s자)"
              % (r["subject"], "생성" if made else "갱신",
                 format(len(r["content"]), ",")))

    print("\n완료: %d개 과목" % len(rows))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        export(sys.argv[2:] or None)
    elif cmd == "load":
        load()
    else:
        print("사용법: python deploy_eco_textbook.py [export [과목명...] | load]")
