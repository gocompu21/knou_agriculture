# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

cert = Certification.objects.get(name="자연생태복원기사")
q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=2022,
                                exam__round=2, number=71).first()
print("[2022-2-71]")
print(" 3)", q.choice_3)
print(" 4)", q.choice_4)
print()
for bad in ["목 표", "서 식", "모니 터링"]:
    print("  '%s' 잔존: %s" % (bad, bad in (q.choice_3 + q.choice_4)))

print()
print("[정상 표기 보존 확인]")
FIELDS = ["text", "choice_1", "choice_2", "choice_3", "choice_4",
          "explanation", "choice_1_exp", "choice_2_exp",
          "choice_3_exp", "choice_4_exp"]
for good in ["수목 표면", "순환 경로", "볼 수", "이 중"]:
    n = 0
    for qq in GisaQuestion.objects.all().only(*FIELDS).iterator(chunk_size=500):
        for f in FIELDS:
            if good in (getattr(qq, f) or ""):
                n += 1
    print("  %-10s %d곳" % (good, n))
