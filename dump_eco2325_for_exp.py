# -*- coding: utf-8 -*-
"""2023~2025 신규 문항을 '선지별 해설 보강' 에이전트용 배치 파일로 분할 추출.

파싱 단계에서 PDF 원본 해설은 `explanation` 에 들어갔지만,
학습모드·채점결과·오답노트 UI 는 `choice_1~4_exp` 만 표시한다.
따라서 통합 해설을 근거로 선지별 해설을 채워야 사용자에게 보인다.

배치 파일에는 문항·보기·정답과 **PDF 원본 해설**이 함께 들어가므로,
에이전트는 원본 해설을 근거로 삼고 자기 지식으로 각 선지의 맞고 틀림의
이유를 서술하면 된다.

사용법:
    python dump_eco2325_for_exp.py                 # 회차×과목 단위 배치 생성
    python dump_eco2325_for_exp.py --year 2023
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

CERT_NAME = "자연생태복원기사"
NEW_YEARS = (2023, 2024, 2025)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--out-dir", required=True, help="배치 JSON 출력 디렉토리")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    cert = Certification.objects.get(name=CERT_NAME)

    years = [args.year] if args.year else list(NEW_YEARS)
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert, exam__year__in=years)
          .select_related("exam", "subject")
          .order_by("exam__year", "exam__round", "number"))

    batches = {}
    for q in qs:
        key = (q.exam.year, q.exam.round, q.subject.name)
        batches.setdefault(key, []).append({
            "id": q.pk,
            "ref": "%d-%d-%d" % (q.exam.year, q.exam.round, q.number),
            "number": q.number,
            "text": q.text,
            "choices": [q.choice_1, q.choice_2, q.choice_3, q.choice_4],
            "answer": q.answer,
            "explanation": q.explanation or "",
        })

    n_files = 0
    for (year, rnd, subj), items in sorted(batches.items()):
        safe = subj.replace("·", "_").replace(" ", "_")
        fp = os.path.join(args.out_dir, "%d-%d_%s.json" % (year, rnd, safe))
        with open(fp, "w", encoding="utf-8") as f:
            json.dump({"year": year, "round": rnd, "subject": subj,
                       "questions": items}, f, ensure_ascii=False, indent=1)
        n_files += 1
        print("%d-%d %-20s %2d문항" % (year, rnd, subj, len(items)))

    print("\n배치 %d개 · 총 %d문항" % (n_files, qs.count()))
    print("출력:", os.path.abspath(args.out_dir))


if __name__ == "__main__":
    main()
