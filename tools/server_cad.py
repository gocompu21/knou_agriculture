# -*- coding: utf-8 -*-
"""운영 서버의 CAD 도면을 안전하게 고친다 — 백업 → 판 확인 → 고치기 → 저장(2026-10, 대표님과 하네스 이야기 5번).

대표님이 "이 도면에서 ○○ 를 지워 줘" 하실 때마다 셸 스크립트를 새로 짜던 일을 한 길로 묶었다.

    python tools/server_cad.py list                       # 서버 도면 목록(번호·이름·작도 수·고친 때)
    python tools/server_cad.py pull 10                    # 받아 오기 → tools/server_cad/cad10.json (판 stamp 포함)
    python tools/server_cad.py push 10                    # 받아 온 파일(고친 것)을 올린다 — 판이 그대로일 때만
    python tools/server_cad.py edit 10 고침.py            # pull → 고침.py 의 apply(doc) → 바뀐 것 요약 → push
    python tools/server_cad.py edit 10 고침.py --dry      # 올리지 않고 무엇이 바뀌는지만
    python tools/server_cad.py backups 10                 # 서버에 남은 백업
    python tools/server_cad.py restore 10 <백업 파일 이름> # 백업으로 되돌리기(이것도 지금 판을 먼저 백업)

지키는 것
- **올리기 직전 서버에 지금 판을 백업**한다(~/cad_backups/cad<번호>_<시각>.json). 되돌리기는 restore 로
- **판(stamp = updated_at)이 받아 올 때와 다르면 올리지 않는다** — 그사이 대표님이 화면에서 저장했으면 그것을 덮지 않는다.
  다시 pull 해서 고친다
- 올린 뒤에는 대표님께 **"그 도면을 열어 두셨다면 저장하지 말고 새로 고침"** 을 꼭 말씀드린다
  (열린 화면의 판은 옛 판이라, 저장하면 덮어쓸까 묻는 창이 뜬다)
- apply(doc) 는 doc(dict: pts·ops·syms …)를 그 자리에서 고치고, 돌려줄 것은 없다(문자열을 돌려주면 요약에 붙인다)
"""
import argparse, json, os, subprocess, sys, importlib.util
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'server_cad')           # 받아 온 파일(git 밖 — .gitignore)
SSH = ['ssh', '-o', 'ServerAliveInterval=60', '-i', r'C:\AWS\knou_key2.pem', 'ubuntu@hanulstudy.kr']


def remote(code, stdin=None):
    """서버에서 Django 코드를 돌린다. 마지막 줄에 JSON 한 줄을 찍게 하고 그것을 돌려준다."""
    import base64                                 # 코드를 base64 로 넘긴다 — ssh 너머 셸이 따옴표·줄바꿈·$ 를 건드리지 않게
    b = base64.b64encode(code.encode('utf-8')).decode()
    cmd = ('cd ~/knou_agriculture && venv/bin/python manage.py shell -c '
           '"import base64;exec(base64.b64decode(\'' + b + '\').decode())"')
    r = subprocess.run(SSH + [cmd], input=stdin, capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        raise SystemExit('서버 오류:\n' + (r.stderr or r.stdout)[-2000:])
    line = [l for l in r.stdout.splitlines() if l.startswith('{') or l.startswith('[')][-1]
    return json.loads(line)


HEAD = ("import json,sys,os,datetime;from gisa.models import CadDrawing as D\n"
        "B=os.path.expanduser('~/cad_backups');os.makedirs(B,exist_ok=True)\n"
        "def bk(d,why):\n"
        "    f=os.path.join(B,'cad%d_%s_%s.json'%(d.pk,datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),why))\n"
        "    json.dump({'title':d.title,'sheet':d.sheet,'data':d.data,'stamp':d.updated_at.isoformat()},open(f,'w',encoding='utf-8'),ensure_ascii=False);return os.path.basename(f)\n")


def cmd_list(a):
    rows = remote(HEAD + "print(json.dumps([[d.pk,d.title,d.sheet,len((d.data or {}).get('ops',[])),d.updated_at.strftime('%m-%d %H:%M')] for d in D.objects.order_by('pk')],ensure_ascii=False))")
    for r in rows:
        print(f'{r[0]:>3}  {r[1]}  ({r[2]}, 작도 {r[3]}줄, {r[4]})')


def path(pk):
    os.makedirs(WORK, exist_ok=True)
    return os.path.join(WORK, f'cad{pk}.json')


def cmd_pull(a):
    j = remote(HEAD + "d=D.objects.get(pk=%d);print(json.dumps({'pk':d.pk,'title':d.title,'sheet':d.sheet,'data':d.data,'stamp':d.updated_at.isoformat()},ensure_ascii=False))" % a.pk)
    json.dump(j, open(path(a.pk), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"받음 — {a.pk} '{j['title']}' 작도 {len(j['data'].get('ops', []))}줄 · 점 {len(j['data'].get('pts', []))}개 · 판 {j['stamp']}")
    print('  →', path(a.pk))
    return j


def push(pk, j, why='push'):
    res = remote(HEAD + (
        "j=json.load(sys.stdin);d=D.objects.get(pk=j['pk'])\n"
        "if d.updated_at.isoformat()!=j['stamp']:\n"
        "    print(json.dumps({'ok':False,'why':'판이 다릅니다 — 받아 온 뒤 화면에서 저장했습니다. 다시 pull 하세요','now':d.updated_at.isoformat()}))\n"
        "else:\n"
        "    f=bk(d,%s);d.data=j['data'];d.save();print(json.dumps({'ok':True,'backup':f,'stamp':d.updated_at.isoformat()}))\n") % json.dumps(why),
        stdin=json.dumps(j, ensure_ascii=False))
    if not res.get('ok'):
        raise SystemExit('✕ 올리지 않았습니다 — ' + res.get('why', '') + f" (서버 판 {res.get('now')})")
    j['stamp'] = res['stamp']
    json.dump(j, open(path(pk), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"✓ 올림 — 백업 ~/cad_backups/{res['backup']} · 새 판 {res['stamp']}")
    print('  ※ 대표님께: 그 도면을 열어 두셨다면 저장하지 말고 새로 고침해 주세요')


def cmd_push(a):
    push(a.pk, json.load(open(path(a.pk), encoding='utf-8')))


def summary(before, after):
    cb = Counter(o.get('t') for o in before['ops']); ca = Counter(o.get('t') for o in after['ops'])
    ids_b = {o['id'] for o in before['ops']}; ids_a = {o['id'] for o in after['ops']}
    print(f"  작도 {len(before['ops'])} → {len(after['ops'])}줄 (지움 {len(ids_b - ids_a)} · 새로 {len(ids_a - ids_b)}) · 점 {len(before['pts'])} → {len(after['pts'])}")
    for t in sorted(set(cb) | set(ca)):
        if cb[t] != ca[t]:
            print(f'    {t}: {cb[t]} → {ca[t]}')


def cmd_edit(a):
    j = cmd_pull(a)
    spec = importlib.util.spec_from_file_location('fix', a.script); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    before = json.loads(json.dumps(j['data']))
    note = m.apply(j['data'])
    print('고친 것:' + (f' {note}' if note else ''))
    summary(before, j['data'])
    if a.dry:
        print('(--dry — 올리지 않았습니다)'); return
    push(a.pk, j, 'edit')


def cmd_backups(a):
    rows = remote(HEAD + "print(json.dumps(sorted([f for f in os.listdir(B) if f.startswith('cad%d_')])))" % a.pk)
    print('\n'.join(rows) or '백업 없음')


def cmd_restore(a):
    res = remote(HEAD + (
        "d=D.objects.get(pk=%d);s=json.load(open(os.path.join(B,%s),encoding='utf-8'))\n"
        "f=bk(d,'before-restore');d.data=s['data'];d.save();print(json.dumps({'backup':f,'stamp':d.updated_at.isoformat()}))") % (a.pk, json.dumps(a.name)))
    print(f"✓ 되돌림 — 되돌리기 전 판도 백업 ~/cad_backups/{res['backup']} · 새 판 {res['stamp']}")
    print('  ※ 대표님께: 그 도면을 열어 두셨다면 저장하지 말고 새로 고침해 주세요')


ap = argparse.ArgumentParser(description='운영 서버 CAD 도면 안전하게 고치기')
sp = ap.add_subparsers(dest='cmd', required=True)
sp.add_parser('list')
for c in ('pull', 'push', 'backups'):
    sp.add_parser(c).add_argument('pk', type=int)
e = sp.add_parser('edit'); e.add_argument('pk', type=int); e.add_argument('script'); e.add_argument('--dry', action='store_true')
r = sp.add_parser('restore'); r.add_argument('pk', type=int); r.add_argument('name')
a = ap.parse_args()
{'list': cmd_list, 'pull': cmd_pull, 'push': cmd_push, 'edit': cmd_edit, 'backups': cmd_backups, 'restore': cmd_restore}[a.cmd](a)
