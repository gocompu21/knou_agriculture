# -*- coding: utf-8 -*-
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp",
          "choice_3_exp", "choice_4_exp"]
PAT = re.compile(r"[가-힣] (다\.|다\)|은\?|는\?|을\?|은 것|는 것|을 것)")

left = 0
for q in GisaQuestion.objects.all().only(*FIELDS).iterator(chunk_size=500):
    for f in FIELDS:
        if PAT.search(getattr(q, f) or ""):
            left += 1
print("남은 어미 분리: %d건 (0 이어야 함)" % left)

cert = Certification.objects.get(name="자연생태복원기사")
q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=2022,
                                exam__round=2, number=61).first()
print()
print("[2022-2-61 보기2]")
print("  ", q.choice_2)
print()
print("  '저 항' 잔존:", "저 항" in q.choice_2)
