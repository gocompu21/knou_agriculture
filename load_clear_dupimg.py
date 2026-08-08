# -*- coding: utf-8 -*-
"""서버 적재: 중복 지문 이미지 필드 비우기 (파일은 남긴다)."""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from gisa.models import Certification, GisaQuestion

cert = Certification.objects.get(name="자연생태복원기사")
refs = json.load(open("_deploy_clear_dupimg.json", encoding="utf-8"))
bak, n, skip = [], 0, 0
for ref in refs:
    y, r, num = (int(x) for x in ref.split("-"))
    q = GisaQuestion.objects.filter(exam__certification=cert, exam__year=y,
                                    exam__round=r, number=num).first()
    if q is None or not q.text_image:
        skip += 1
        continue
    if "[box]" not in (q.text or ""):
        print("  [건너뜀 - box 없음] %s" % ref)
        skip += 1
        continue
    bak.append({"ref": ref, "text_image": q.text_image.name})
    q.text_image = ""
    q.save(update_fields=["text_image"])
    n += 1
json.dump(bak, open("_dup_image_backup.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("제거 %d · 건너뜀 %d" % (n, skip))
left = GisaQuestion.objects.filter(exam__certification=cert,
                                   text__contains="[box]").exclude(text_image="").count()
print("남은 중복: %d" % left)
