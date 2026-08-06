# -*- coding: utf-8 -*-
"""2020-3 / 2021-2 / 2022-1 을 선지별 해설 재작성용 배치로 분할 추출.

이 세 회차는 출판사 해설로 explanation 을 교체했으나,
UI(학습모드·채점결과·오답노트)는 choice_1~4_exp 만 표시하므로
선지 해설도 새 해설을 근거로 다시 써야 한다.

사용법:
    python dump_eco2022_for_exp.py --out-dir <배치디렉토리>
"""
import argparse
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
TARGETS = [(2020, 3), (2021, 2), (2022, 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    cert = Certification.objects.get(name=CERT)

    n_files = n_q = 0
    for year, rnd in TARGETS:
        qs = (GisaQuestion.objects
              .filter(exam__certification=cert, exam__year=year, exam__round=rnd)
              .select_related("exam", "subject")
              .order_by("number"))

        batches = {}
        for q in qs:
            batches.setdefault(q.subject.name, []).append({
                "id": q.pk,
                "ref": "%d-%d-%d" % (year, rnd, q.number),
                "number": q.number,
                "text": q.text,
                "choices": [q.choice_1, q.choice_2, q.choice_3, q.choice_4],
                "answer": q.answer,
                "explanation": q.explanation or "",
            })

        for subj, items in batches.items():
            safe = subj.replace("·", "_").replace(" ", "_")
            fp = os.path.join(args.out_dir, "%d-%d_%s.json" % (year, rnd, safe))
            with open(fp, "w", encoding="utf-8") as f:
                json.dump({"year": year, "round": rnd, "subject": subj,
                           "questions": items}, f, ensure_ascii=False, indent=1)
            n_files += 1
            n_q += len(items)
            avg = sum(len(i["explanation"]) for i in items) // max(len(items), 1)
            print("%d-%d %-20s %2d문항  해설평균 %4d자" % (year, rnd, subj, len(items), avg))

    print("\n배치 %d개 · 총 %d문항" % (n_files, n_q))
    print("출력:", os.path.abspath(args.out_dir))


if __name__ == "__main__":
    main()
