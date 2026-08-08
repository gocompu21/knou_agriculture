# -*- coding: utf-8 -*-
"""서버 적재: 재생성한 문항 이미지를 media 에 덮어쓴다.

_deploy_q16_images.json 형식: [{"path": "gisa/questions/...", "b64": "..."}]
원본은 .orig 로 백업한다(이미 있으면 유지).
"""
import base64
import io
import json
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.conf import settings

JSON_PATH = sys.argv[1] if len(sys.argv) > 1 else "_deploy_q16_images.json"

rows = json.load(open(JSON_PATH))
n = 0
for r in rows:
    dst = os.path.join(settings.MEDIA_ROOT, r["path"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    bak = dst + ".orig"
    if os.path.exists(dst) and not os.path.exists(bak):
        shutil.copy(dst, bak)
    data = base64.b64decode(r["b64"])
    open(dst, "wb").write(data)
    n += 1
    print("  %s (%s bytes)" % (r["path"], format(len(data), ",")))
print("반영 %d개 (원본은 .orig 백업)" % n)
