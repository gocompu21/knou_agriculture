# -*- coding: utf-8 -*-
"""자연생태복원기사 과목별 문항을 노트 작성용 텍스트로 추출.

쪽집게 노트 작성 에이전트에게 넘길 재료를 만든다.
문항·정답뿐 아니라 **해설까지 함께** 뽑아, 에이전트가 자기 지식과 종합해
서술할 수 있게 한다.

사용법:
    python dump_eco_questions.py 생태환경조사분석 eco_survey
    python dump_eco_questions.py 생태환경조사분석 eco_survey --no-exp   # 해설 제외
"""
import argparse
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaQuestion

CERT_NAME = "자연생태복원기사"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subject", help="과목명 (예: 생태환경조사분석)")
    ap.add_argument("prefix", help="출력 파일 prefix (예: eco_survey)")
    ap.add_argument("--out-dir", default=".", help="출력 디렉토리")
    ap.add_argument("--no-exp", action="store_true", help="해설 제외")
    args = ap.parse_args()

    cert = Certification.objects.get(name=CERT_NAME)
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert, subject__name=args.subject)
          .select_related("exam")
          .order_by("exam__year", "exam__round", "number"))

    if not qs.exists():
        print("문항 없음:", args.subject)
        return

    lines = []
    n_exp = 0
    for q in qs:
        ref = "%d-%d-%d" % (q.exam.year, q.exam.round, q.number)
        lines.append("[%s] %s" % (ref, q.text))
        choices = [q.choice_1, q.choice_2, q.choice_3, q.choice_4]
        ans = set((q.answer or "").split(","))
        for i, c in enumerate(choices, start=1):
            mark = "*" if str(i) in ans else " "
            lines.append("  %s%d) %s" % (mark, i, c))
        if not args.no_exp and q.explanation:
            n_exp += 1
            lines.append("  [해설] %s" % q.explanation.replace("\n", "\n         "))
        lines.append("")

    fp = os.path.join(args.out_dir, "_%s_full.txt" % args.prefix)
    with open(fp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    years = sorted({q.exam.year for q in qs})
    print("과목: %s" % args.subject)
    print("문항: %d개 (%d~%d년)" % (qs.count(), years[0], years[-1]))
    print("해설 포함: %d개 (%.0f%%)" % (n_exp, n_exp / qs.count() * 100))
    print("저장: %s (%s자)" % (os.path.abspath(fp),
                              format(sum(len(x) for x in lines), ",")))


if __name__ == "__main__":
    main()
