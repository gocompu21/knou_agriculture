# -*- coding: utf-8 -*-
"""통합 노트를 DB에 저장하고 파싱 검증.

사용법:
    python _save_merged.py <md경로> <과목명> [--dry]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaSubject, GisaTextbook
from gisa.views import parse_study_guide

path, subject = sys.argv[1], sys.argv[2]
dry = "--dry" in sys.argv

content = open(path, encoding="utf-8").read()

ch = parse_study_guide(content)
nsec = sum(len(x["sections"]) for x in ch)
empty = [(x["title"], s["title"]) for x in ch for s in x["sections"]
         if not s.get("content_html") and not s.get("subsections")]

print("[파싱] 장 %d · 절 %d · 빈절 %d" % (len(ch), nsec, len(empty)))
for t in ch:
    print("   %-46s (절 %d)" % (t["title"][:46], len(t["sections"])))
if empty:
    print("\n빈 절:")
    for c, s in empty[:10]:
        print("   %s > %s" % (c, s))

if dry:
    print("\n(--dry: 저장 안 함)")
    sys.exit()

cert = Certification.objects.get(name="자연생태복원기사")
subj = GisaSubject.objects.get(certification=cert, name=subject)
tb, created = GisaTextbook.objects.update_or_create(
    certification=cert, subject=subj, defaults={"content": content})
print("\n저장 완료: %s %s (%s자)"
      % (subject, "생성" if created else "갱신", format(len(content), ",")))
