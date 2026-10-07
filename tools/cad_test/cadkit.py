# -*- coding: utf-8 -*-
"""CAD 탭 확인 도구 — 안부장이 세션마다 새로 짜던 Playwright 시험 코드를 한 곳에 모았다(2026-10).

쓰는 법(저장소 맨 위에서, venv 파이썬으로):

    from tools.cad_test.cadkit import Cad
    with Cad(doc) as c:              # doc = 도면 JSON(dict). None 이면 빈 A2 1:400
        c.zoom(50, 50, 4)            # 그 자리로 휠 확대 4번
        c.key('l')                   # 도구 단축키
        c.click(40, 60)              # 도면 좌표(m)로 누르기
        d = c.doc()                  # 지금 초안(localStorage) 도면
        c.shot('out.png', 50, 50, 400, 300)   # 도면 좌표 둘레를 찍는다
        print(c.errors)              # 페이지 오류(있으면 JS 가 죽은 것)

전제:
- 개발 서버가 떠 있어야 한다(기본 8099). `--noreload` 로 띄웠으면 템플릿을 고친 뒤 다시 띄울 것
  (CLAUDE.md '개발 서버' 절). 다른 일과 겹치면 port 를 바꾼다
- 로그인은 쿠키를 박아 두지 않고 로컬 DB 의 스태프 계정으로 세션을 만들어 쓴다(staff_cookie)
- 서버(운영) 도면은 server_drawing(pk) 로 **읽기만** 해 온다
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BLANK = {'v': 1, 'sheet': 'a2-400', 'pts': [], 'ops': [], 'syms': {}, 'seq': 10}
CERT = 5                                   # 로컬 조경기사 — CAD 탭이 붙은 실기 작업형 화면
SSH = ['ssh', '-o', 'ServerAliveInterval=60', '-i', r'C:\AWS\knou_key2.pem', 'ubuntu@hanulstudy.kr']


def staff_cookie():
    """로컬 DB 의 스태프 계정으로 세션을 만들어 sessionid 값을 돌려준다."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from django.contrib.auth.models import User
    from django.test import Client
    c = Client()
    c.force_login(User.objects.filter(is_staff=True, is_active=True).order_by('pk').first())
    return c.cookies['sessionid'].value


def server_drawing(pk, cache_dir=None):
    """운영 서버의 CadDrawing 을 읽기만 해 온다 → {'sheet','data','title'}. cache_dir 가 있으면 거기 둔다."""
    if cache_dir:
        f = os.path.join(cache_dir, f'cad{pk}.json')
        if os.path.exists(f):
            return json.load(open(f, encoding='utf-8'))
    code = ("import json,sys;from gisa.models import CadDrawing as D;d=D.objects.get(pk=%d);"
            "x=d.data if isinstance(d.data,dict) else json.loads(d.data);"
            "sys.stdout.write(json.dumps({'title':d.title,'sheet':x.get('sheet'),'data':x},ensure_ascii=False))") % int(pk)
    out = subprocess.run(SSH + [f"cd ~/knou_agriculture && venv/bin/python manage.py shell -c \"{code}\""],
                         capture_output=True, text=True, encoding='utf-8')
    j = json.loads(out.stdout[out.stdout.index('{'):])
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        json.dump(j, open(os.path.join(cache_dir, f'cad{pk}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    return j


class Cad:
    """도면 하나를 초안으로 넣고 CAD 탭을 연 브라우저. with 로 쓰면 끝날 때 초안을 지우고 닫는다."""

    def __init__(self, doc=None, port=8099, size=(1440, 900), ls=None, headless=True, wait=2500, video=None):
        self.video = video                         # 폴더를 주면 그 안에 녹화(webm)
        self.doc0 = doc or dict(BLANK)
        self.port, self.size, self.ls, self.headless, self.wait = port, size, ls or {}, headless, wait
        self.errors = []

    # ── 열고 닫기 ──
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        sid = staff_cookie()                      # Playwright 가 이벤트 루프를 열기 전에 — 그 안에서는 Django ORM 이 막힌다
        self._p = sync_playwright().start()
        self.b = self._p.chromium.launch(headless=self.headless)
        vo = {'record_video_dir': self.video, 'record_video_size': {'width': self.size[0], 'height': self.size[1]}} if self.video else {}
        self.ctx = self.b.new_context(viewport={'width': self.size[0], 'height': self.size[1]}, **vo)
        self.ctx.add_cookies([{'name': 'sessionid', 'value': sid, 'domain': 'localhost', 'path': '/'}])
        self.pg = self.ctx.new_page()
        self.pg.on('pageerror', lambda e: self.errors.append(str(e)))
        self.pg.on('dialog', lambda d: d.accept())
        base = f'http://localhost:{self.port}/gisa/{CERT}/essay/work/'
        self.pg.goto(base)
        # 자·초안 — 기본은 I자·삼각자·템플릿을 치운다(시험마다 ls 로 덮어쓴다)
        ls = {'cadBar': {'on': False, 'y': 200}, 'cadTri': None, 'cadTpl': None, **self.ls}
        self.pg.evaluate("""([d, ls]) => {
            localStorage.setItem('cadDraft:%d', JSON.stringify({id: null, doc: d, dirty: false}));
            for (const [k, v] of Object.entries(ls)) v == null ? localStorage.removeItem(k) : localStorage.setItem(k, typeof v === 'string' ? v : JSON.stringify(v));
        }""" % CERT, [self.doc0, ls])
        self.pg.goto(base + '?tab=cad')
        self.pg.wait_for_timeout(self.wait)
        return self

    def __exit__(self, *a):
        try:
            self.pg.evaluate("localStorage.removeItem('cadDraft:%d')" % CERT)
        finally:
            self.ctx.close(); self.b.close(); self._p.stop()

    # ── 좌표 ──
    def S(self, x, y):
        """도면 좌표(m) → 화면 좌표(px)."""
        return self.pg.evaluate("([x,y]) => { const p = new DOMPoint(x,y).matrixTransform(document.getElementById('cadSvg').getScreenCTM()); return [p.x, p.y]; }", [x, y])

    # ── 손놀림 ──
    def zoom(self, x, y, n=3):
        self.pg.mouse.move(*self.S(x, y))
        for _ in range(n):
            self.pg.mouse.wheel(0, -300); self.pg.wait_for_timeout(80)
        self.pg.wait_for_timeout(200)

    def key(self, k, wait=200):
        self.pg.keyboard.press(k); self.pg.wait_for_timeout(wait)

    def click(self, x, y, wait=250, **kw):
        self.pg.mouse.click(*self.S(x, y), **kw); self.pg.wait_for_timeout(wait)

    def drag(self, pts, button='left', wait=250):
        """도면 좌표 점들을 따라 끈다(프리드로잉·수목 군식·샤프 긋기)."""
        m = self.pg.mouse
        m.move(*self.S(*pts[0])); m.down(button=button)
        for q in pts[1:]:
            m.move(*self.S(*q))
        m.up(button=button); self.pg.wait_for_timeout(wait)

    # ── 읽기 ──
    def doc(self):
        """지금 초안 도면(dict)."""
        return self.pg.evaluate("JSON.parse(localStorage.getItem('cadDraft:%d')).doc" % CERT)

    def texts(self):
        return [(o['s'], o.get('x'), o.get('y')) for o in self.doc()['ops'] if o['t'] == 'text']

    def hint(self):
        return self.pg.locator('#cadHint').text_content()

    def shot(self, path, x=None, y=None, w=600, h=400, el=None):
        """도면 좌표 (x,y) 둘레 w×h px, 또는 요소(el 선택자)를 찍는다. 둘 다 없으면 화면 전체."""
        if el:
            return self.pg.screenshot(path=path, clip=self.pg.locator(el).bounding_box())
        if x is None:
            return self.pg.screenshot(path=path)
        cx, cy = self.S(x, y)
        return self.pg.screenshot(path=path, clip={'x': cx - w / 2, 'y': cy - h / 2, 'width': w, 'height': h})


def jscheck(path=os.path.join(ROOT, 'templates', 'gisa', '_cad.html')):
    """템플릿의 <script> 를 뽑아 node --check — 서버 렌더 없이 바로(렌더된 화면은 _jscheck.py)."""
    import re, tempfile
    s = open(path, encoding='utf-8').read()
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', s, re.S))
    js = re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '0', js)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js); tmp = f.name
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True, encoding='utf-8')
    os.unlink(tmp)
    print('✓ JS 문법 이상 없음' if not r.returncode else '✕ JS 문법 오류\n' + r.stderr)
    return r.returncode == 0


if __name__ == '__main__':
    sys.exit(0 if jscheck() else 1)
