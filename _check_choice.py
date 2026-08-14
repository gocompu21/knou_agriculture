# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User

url = sys.argv[1] if len(sys.argv) > 1 else "/gisa/3/study/165/21/"
u = User.objects.filter(is_staff=True).first()
c = Client(); c.force_login(u)
r = c.get(url)
h = r.content.decode("utf-8")
print("URL", url, "status", r.status_code)
print("  choice-item 에 onclick :", h.count('class="choice-item" onclick'), "(0 이어야 함)")
print("  choice-num  에 onclick :", h.count('data-choice="1" onclick') * 4 // 1 if False else h.count('onclick="selectChoice'))
print("  .choice-item:hover 제거:", ".choice-item:hover" not in h)
print("  히트영역 확장 ::before :", ".choice-num::before" in h)
print("  selectChoice 정규화    :", "closest('.choice-item')" in h)
