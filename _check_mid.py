# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

cert = Certification.objects.get(name="자연생태복원기사")
q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=2022,
                                exam__round=2, number=63).first()
print("[2022-2-63 보기3]")
print("  ", q.choice_3)
print("   '휴 양' 잔존:", "휴 양" in q.choice_3)

q2 = GisaQuestion.objects.filter(exam__certification=cert, exam__year=2022,
                                 exam__round=2, number=61).first()
print()
print("[2022-2-61 보기2]  '저 항' 잔존:", "저 항" in q2.choice_2)

q3 = GisaQuestion.objects.filter(pk=1847).first()
print()
print("[식물보호기사 2012-2 #47 해설]")
print("  ", (q3.explanation or "")[:76])
