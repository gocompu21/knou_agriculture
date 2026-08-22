# -*- coding: utf-8 -*-
"""문제+보기를 회차별 배치로 추출한다 (교정 전수조사용).

에이전트가 직접 읽고 조판 흔적·오탈자를 찾는다.
해설은 분량이 커서(239만자) 별도 단계로 미룬다.
"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

CERT = "자연생태복원기사"
OUT = "_proof"

cert = Certification.objects.get(name=CERT)
os.makedirs(OUT, exist_ok=True)

by = {}
for q in (GisaQuestion.objects.filter(exam__certification=cert)
          .select_related("exam", "subject").order_by("exam__year", "exam__round", "number")):
    key = "%d-%d" % (q.exam.year, q.exam.round)
    by.setdefault(key, []).append({
        "pk": q.pk,
        "ref": "%s-%d" % (key, q.number),
        "subject": q.subject.name,
        "text": q.text,
        "choices": [q.choice_1, q.choice_2, q.choice_3, q.choice_4],
        "answer": q.answer,
    })

tot = 0
for key, items in sorted(by.items(), key=lambda kv: tuple(int(x) for x in kv[0].split("-"))):
    fp = os.path.join(OUT, "%s.json" % key)
    json.dump({"round": key, "questions": items},
              open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(len(i["text"]) + sum(len(c or "") for c in i["choices"]) for i in items)
    tot += n
    print("%-8s %3d문항 %7s자" % (key, len(items), format(n, ",")))
print()
print("회차 %d개 · 합계 %s자" % (len(by), format(tot, ",")))
