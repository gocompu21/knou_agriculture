# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

cert = Certification.objects.get(name="자연생태복원기사")
CASES = [
    (2022, 2, 64, "choice_4", "단절되 거나"),
    (2022, 2, 63, "choice_3", "휴 양"),
    (2022, 2, 61, "choice_2", "저 항"),
]
for y, r, n, f, bad in CASES:
    q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=y,
                                    exam__round=r, number=n).first()
    v = getattr(q, f) or ""
    print("%d-%d-%d [%s]  '%s' 잔존: %s" % (y, r, n, f, bad, bad in v))
print()
q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=2022,
                                exam__round=2, number=64).first()
print("[2022-2-64 보기4]")
print("  ", q.choice_4)
