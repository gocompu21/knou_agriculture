# -*- coding: utf-8 -*-
"""서버 적재: 단일 과목 쪽집게 노트 갱신."""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaTextbook

path = sys.argv[1] if len(sys.argv) > 1 else "_deploy_note_streamorder.json"
for r in json.load(open(path, encoding="utf-8")):
    cert = Certification.objects.get(name=r["cert"])
    tb = GisaTextbook.objects.get(certification=cert, subject__name=r["subject"])
    before = len(tb.content)
    tb.content = r["content"]
    tb.save(update_fields=["content"])
    print("%s / %s : %s자 → %s자" % (r["cert"], r["subject"],
          format(before, ","), format(len(r["content"]), ",")))
