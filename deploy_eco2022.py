# -*- coding: utf-8 -*-
"""자연생태복원기사 2023~2025 신규 720문항을 EC2로 배포.

기존 3,160문항은 이미 서버에 있으므로 신규분만 다룬다.
이 회차들은 이미지가 없어(전부 텍스트로 판독) 이미지 zip이 필요 없다.

로컬(추출):
    python deploy_eco2325.py export     → _deploy_eco2022.json

서버(적재):
    python deploy_eco2325.py load
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.db import transaction

from gisa.models import Certification, GisaSubject, GisaExam, GisaQuestion

CERT_NAME = "자연생태복원기사"
CERT_CATEGORY = "기사"
YEARS = (2020, 2021, 2022)
JSON_PATH = "_deploy_eco2022.json"

# 2022년 개편 이후 신 체계 4과목 (order 는 기존 배포와 일치시킨다)
# 2020~2021 은 구 체계 5과목, 2022 부터 신 체계 4과목이므로 둘 다 등록한다.
NEW_SUBJECTS = [
    ("환경생태학개론", 1),
    ("환경계획학", 2),
    ("생태복원공학", 3),
    ("경관생태학", 4),
    ("자연환경관계법규", 5),
    ("생태환경조사분석", 6),
    ("생태복원계획", 7),
    ("생태복원설계·시공", 8),
    ("생태복원 사후관리·평가", 9),
]

FIELDS = ("text", "choice_1", "choice_2", "choice_3", "choice_4", "answer",
          "explanation", "choice_1_exp", "choice_2_exp", "choice_3_exp",
          "choice_4_exp")


def export():
    cert = Certification.objects.get(name=CERT_NAME)
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert, exam__year__in=YEARS)
          .select_related("exam", "subject")
          .order_by("exam__year", "exam__round", "number"))

    rows = []
    for q in qs:
        d = {
            "year": q.exam.year,
            "round": q.exam.round,
            "exam_type": q.exam.exam_type,
            "number": q.number,
            "subject": q.subject.name,
        }
        for f in FIELDS:
            d[f] = getattr(q, f) or ""
        rows.append(d)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)

    size = os.path.getsize(JSON_PATH)
    print("추출: %d문항 → %s (%s bytes)"
          % (len(rows), JSON_PATH, format(size, ",")))

    n_exp = sum(1 for r in rows if r["explanation"])
    n_cexp = sum(1 for r in rows if r["choice_1_exp"])
    print("  통합해설 %d · 선지해설 %d" % (n_exp, n_cexp))


def load():
    if not os.path.exists(JSON_PATH):
        print("JSON 없음:", JSON_PATH)
        return

    with open(JSON_PATH, encoding="utf-8") as f:
        rows = json.load(f)

    cert, _ = Certification.objects.get_or_create(
        name=CERT_NAME, defaults={"category": CERT_CATEGORY})
    print("자격증: %s (pk=%d)" % (cert.name, cert.pk))

    # 신 체계 과목 확보
    subj_map = {}
    for name, order in NEW_SUBJECTS:
        s, created = GisaSubject.objects.get_or_create(
            certification=cert, name=name, defaults={"order": order})
        subj_map[name] = s
        if created:
            print("  과목 생성: %s (pk=%d)" % (name, s.pk))

    # 회차별로 묶어 처리
    by_exam = {}
    for r in rows:
        by_exam.setdefault((r["year"], r["round"], r["exam_type"]), []).append(r)

    n_new = n_upd = 0
    for (year, rnd, etype), items in sorted(by_exam.items()):
        with transaction.atomic():
            exam, _ = GisaExam.objects.get_or_create(
                certification=cert, year=year, round=rnd, exam_type=etype)
            a = b = 0
            for r in items:
                subj = subj_map.get(r["subject"])
                if subj is None:
                    print("  [과목 미상] %d-%d #%d %s"
                          % (year, rnd, r["number"], r["subject"]))
                    continue
                defaults = {"subject": subj}
                for f in FIELDS:
                    defaults[f] = r.get(f, "")
                _, created = GisaQuestion.objects.update_or_create(
                    exam=exam, number=r["number"], defaults=defaults)
                if created:
                    a += 1
                else:
                    b += 1
            n_new += a
            n_upd += b
            print("  %d-%d: 신규 %d · 갱신 %d" % (year, rnd, a, b))

    print("\n완료: 신규 %d · 갱신 %d (총 %d문항)" % (n_new, n_upd, n_new + n_upd))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        export()
    elif cmd == "load":
        load()
    else:
        print("사용법: python deploy_eco2325.py [export|load]")
