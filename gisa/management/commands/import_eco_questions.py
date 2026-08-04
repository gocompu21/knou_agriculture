# -*- coding: utf-8 -*-
"""자연생태복원기사 기출문제 import

parse_eco.py 가 만든 _eco_parsed.json 과 _eco_images/ 를 읽어 DB에 저장한다.

사용법:
    python manage.py import_eco_questions                 # 전체
    python manage.py import_eco_questions --year 2012     # 특정 연도
    python manage.py import_eco_questions --dry-run       # 미리보기
"""
import os
import json

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.models import Certification, GisaSubject, GisaExam, GisaQuestion

CERT_NAME = "자연생태복원기사"
CERT_CATEGORY = "기사"

# 과목 순서.
# 2022년 출제 체계 개편으로 과목명이 전면 교체되었다(단순 축소가 아님).
#   ~2021: 5과목 100문항 / 2022~: 4과목 80문항
# 두 체계의 과목을 모두 등록하고, 문항은 파싱 결과의 subject 이름으로 연결한다.
SUBJECT_ORDER = [
    # 2012~2021 (구 체계)
    "환경생태학개론",
    "환경계획학",
    "생태복원공학",
    "경관생태학",
    "자연환경관계법규",
    # 2022~ (신 체계)
    "생태환경조사분석",
    "생태복원계획",
    "생태복원설계·시공",
    "생태복원 사후관리·평가",
]


class Command(BaseCommand):
    help = "자연생태복원기사 기출문제 import (_eco_parsed.json 기반)"

    def add_arguments(self, parser):
        parser.add_argument("--json", default="_eco_parsed.json", help="파싱 결과 JSON 경로")
        parser.add_argument("--images", default="_eco_images", help="이미지 디렉토리")
        parser.add_argument("--year", type=int, help="특정 연도만")
        parser.add_argument("--round", type=int, help="특정 회차만")
        parser.add_argument("--dry-run", action="store_true", help="저장하지 않고 미리보기")

    def handle(self, *args, **opt):
        base = os.getcwd()
        json_path = opt["json"]
        if not os.path.isabs(json_path):
            json_path = os.path.join(base, json_path)
        img_dir = opt["images"]
        if not os.path.isabs(img_dir):
            img_dir = os.path.join(base, img_dir)

        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR("JSON 없음: %s" % json_path))
            self.stderr.write("먼저 `python parse_eco.py` 를 실행하세요.")
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        if opt.get("year"):
            data = [d for d in data if d["year"] == opt["year"]]
        if opt.get("round"):
            data = [d for d in data if d["round"] == opt["round"]]

        if not data:
            self.stderr.write("대상 회차 없음")
            return

        dry = opt["dry_run"]

        # 자격증
        if dry:
            cert = Certification.objects.filter(name=CERT_NAME).first()
            self.stdout.write("[dry-run] 자격증: %s" % (cert or "신규 생성 예정"))
        else:
            cert, created = Certification.objects.get_or_create(
                name=CERT_NAME, defaults={"category": CERT_CATEGORY}
            )
            self.stdout.write(
                self.style.SUCCESS("자격증 %s: %s (pk=%d)"
                                   % ("생성" if created else "확인", cert.name, cert.pk))
            )

        # 과목
        subj_map = {}
        if not dry:
            for i, name in enumerate(SUBJECT_ORDER, start=1):
                s, c = GisaSubject.objects.get_or_create(
                    certification=cert, name=name, defaults={"order": i}
                )
                if s.order != i:
                    s.order = i
                    s.save(update_fields=["order"])
                subj_map[name] = s
                if c:
                    self.stdout.write("  과목 생성: %d. %s (pk=%d)" % (i, name, s.pk))

        total_q = 0
        total_img = 0
        for d in data:
            year, rnd = d["year"], d["round"]
            qs = d["questions"]

            if dry:
                self.stdout.write("[dry-run] %d년 %d회 → %d문항" % (year, rnd, len(qs)))
                total_q += len(qs)
                continue

            with transaction.atomic():
                exam, _ = GisaExam.objects.get_or_create(
                    certification=cert, year=year, round=rnd, exam_type="필기"
                )

                n_img = 0
                for q in qs:
                    subj = subj_map.get(q["subject"])
                    if subj is None:
                        continue

                    defaults = {
                        "subject": subj,
                        "text": q["text"],
                        "choice_1": q["choices"][0],
                        "choice_2": q["choices"][1],
                        "choice_3": q["choices"][2],
                        "choice_4": q["choices"][3],
                        "answer": q["answer"],
                    }
                    # 해설이 파싱 결과에 있으면 함께 저장한다.
                    # (없으면 키 자체를 넣지 않아 기존 해설을 보존한다)
                    for key in ("explanation", "choice_1_exp", "choice_2_exp",
                                "choice_3_exp", "choice_4_exp"):
                        if q.get(key):
                            defaults[key] = q[key]

                    obj, _created = GisaQuestion.objects.update_or_create(
                        exam=exam,
                        number=q["number"],
                        defaults=defaults,
                    )

                    # 이미지 저장
                    fields = [
                        ("text_image", q.get("text_image", "")),
                        ("choice_1_image", (q.get("choice_images") or ["", "", "", ""])[0]),
                        ("choice_2_image", (q.get("choice_images") or ["", "", "", ""])[1]),
                        ("choice_3_image", (q.get("choice_images") or ["", "", "", ""])[2]),
                        ("choice_4_image", (q.get("choice_images") or ["", "", "", ""])[3]),
                    ]
                    changed = False
                    for field, fname in fields:
                        if not fname:
                            continue
                        src = os.path.join(img_dir, fname)
                        if not os.path.exists(src):
                            self.stderr.write("  이미지 없음: %s" % src)
                            continue
                        cur = getattr(obj, field)
                        if cur and os.path.basename(cur.name) == fname:
                            continue  # 이미 저장됨
                        with open(src, "rb") as fh:
                            getattr(obj, field).save(fname, File(fh), save=False)
                        changed = True
                        n_img += 1
                    if changed:
                        obj.save()

                total_q += len(qs)
                total_img += n_img
                self.stdout.write("  %d년 %d회: %d문항 (이미지 %d)" % (year, rnd, len(qs), n_img))

        self.stdout.write(
            self.style.SUCCESS("\n완료: %d회차 · %d문항 · 이미지 %d개"
                               % (len(data), total_q, total_img))
        )
