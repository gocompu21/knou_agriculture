# -*- coding: utf-8 -*-
"""렌더된 화면의 <script> 를 실제로 파싱해 본다.

템플릿의 JS 는 서버 테스트로는 절대 안 잡힌다 — 문자열 하나가 끊겨도 HTML 은
멀쩡히 200 을 주고, 브라우저에서만 그 블록 전체가 죽는다(실제로 `\n` 이 진짜
줄바꿈으로 들어가 vdFold 부터 전부 undefined 가 됐다).
"""
import os, re, sys, subprocess, tempfile
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')
from django.test import Client
from django.contrib.auth.models import User

PAGES = sys.argv[1:] or ['/gisa/5/essay/work/?tab=video']
c = Client(); c.force_login(User.objects.filter(is_staff=True, is_active=True).first())
bad = 0
for url in PAGES:
    html = c.get(url).content.decode('utf-8', 'replace')
    for i, m in enumerate(re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)):
        body = m.group(1)
        if not body.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                         encoding='utf-8') as f:
            f.write(body); path = f.name
        r = subprocess.run(['node', '--check', path], capture_output=True, text=True,
                           encoding='utf-8')
        os.unlink(path)
        if r.returncode:
            bad += 1
            print(f'✕ {url} script#{i}')
            print('  ' + '\n  '.join((r.stderr or '').splitlines()[:6]))
        else:
            print(f'✓ {url} script#{i} ({len(body):,}자)')
print('\n실패', bad)
sys.exit(1 if bad else 0)
