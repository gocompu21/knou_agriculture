# -*- coding: utf-8 -*-
"""통합 노트 검증: 신·구 체계 문항 커버리지를 함께 확인.

사용법:
    python _check_merged.py <통합md경로> <신과목> [구과목...]
예:
    python _check_merged.py final/survey.md 생태환경조사분석 환경생태학개론 경관생태학
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaQuestion

path = sys.argv[1]
subjects = sys.argv[2:]

content = open(path, encoding="utf-8").read()
refs = set(re.findall(r"\((\d{4}-\d-\d{1,3})\)", content))

print("[구조] 장 %d · 절 %d · 항 %d · 키워드표 %d" % (
    len(re.findall(r"^## (?:제\d+장|부록)", content, re.M)),
    len(re.findall(r"^### ", content, re.M)),
    len(re.findall(r"^#### ", content, re.M)),
    len(re.findall(r"^### 핵심 키워드 요약", content, re.M)),
))
print("[분량] %s자 · %s줄" % (format(len(content), ","),
                              format(content.count("\n") + 1, ",")))
print("[ref] 고유 %d개" % len(refs))
print()

cert = Certification.objects.get(name="자연생태복원기사")
all_actual = set()
for sname in subjects:
    qs = (GisaQuestion.objects
          .filter(exam__certification=cert, subject__name=sname)
          .select_related("exam"))
    actual = {"%d-%d-%d" % (q.exam.year, q.exam.round, q.number) for q in qs}
    all_actual |= actual
    hit = refs & actual
    miss = sorted(actual - refs)
    print("%-22s %3d/%3d (%.1f%%)" % (sname, len(hit), len(actual),
                                      len(hit) / len(actual) * 100))
    if miss:
        print("   미연결 %d개: %s%s" % (
            len(miss), ", ".join(miss[:12]),
            " ..." if len(miss) > 12 else ""))

bogus = sorted(refs - all_actual)
print()
print("합계 %d/%d (%.1f%%)" % (len(refs & all_actual), len(all_actual),
                               len(refs & all_actual) / len(all_actual) * 100))
if bogus:
    print("⚠ 존재하지 않는 ref %d개: %s%s" % (
        len(bogus), ", ".join(bogus[:12]), " ..." if len(bogus) > 12 else ""))
else:
    print("무효 ref 0건")
