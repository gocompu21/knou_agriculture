# -*- coding: utf-8 -*-
"""통합 작업용: 자연생태복원기사 노트 9개를 파일로 추출."""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from gisa.models import Certification, GisaTextbook

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

MAP = {
    "생태환경조사분석": "new_survey",
    "환경생태학개론": "old_env",
    "경관생태학": "old_land",
    "생태복원계획": "new_plan",
    "환경계획학": "old_plan",
    "생태복원설계·시공": "new_design",
    "생태복원공학": "old_eng",
    "생태복원 사후관리·평가": "new_mgmt",
    "자연환경관계법규": "old_law",
}

cert = Certification.objects.get(name="자연생태복원기사")
for name, pre in MAP.items():
    tb = GisaTextbook.objects.get(certification=cert, subject__name=name)
    fp = os.path.join(OUT, pre + ".md")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(tb.content)
    print("%-22s → %s.md (%s자)" % (name, pre, format(len(tb.content), ",")))
