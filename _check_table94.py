# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.templatetags.gisa_filters import qtext
from gisa.models import Certification, GisaQuestion

cert = Certification.objects.get(name="자연생태복원기사")
for y, r, n in [(2021, 3, 94), (2017, 3, 45), (2013, 3, 43)]:
    q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=y,
                                    exam__round=r, number=n).first()
    if not q:
        print("%d-%d-%d 없음" % (y, r, n)); continue
    h = str(qtext(q.text))
    print("%d-%d-%d  표:%s  행:%d  잔존파이프:%d  각주div:%s"
          % (y, r, n, "O" if "<table" in h else "X", h.count("<tr>"),
             h.count("|"), "O" if "margin-top:6px" in h else "-"))

bad = 0; tq = 0
for q in GisaQuestion.objects.all().only("id", "text").iterator(chunk_size=500):
    v = q.text or ""
    if not v: continue
    h = str(qtext(v))
    if ("|---" in v and "<table" not in h) or h.count("<table") != h.count("</table>"):
        bad += 1
    if "<table" in h: tq += 1
print()
print("[전수] 문제 지문 표 렌더 %d건 · 이상 %d건" % (tq, bad))
