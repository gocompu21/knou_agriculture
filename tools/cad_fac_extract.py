import os, sys, re, json, django
sys.path.insert(0, os.getcwd()); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup()
sys.stdout.reconfigure(encoding='utf-8')
from gisa.models import GisaDrawingRef as R
SP = os.path.dirname(os.path.abspath(__file__))
rows = []
for r in R.objects.filter(certification_id=5).order_by('code', 'order'):
    c = r.content or ''
    for m in re.finditer(r'<svg[^>]*aria-label="시설물 수량표"[^>]*>(.*?)</svg>', c, re.S):
        t = m.group(1)
        for g in re.finditer(r'<g transform="translate\(([\d.]+) ([\d.]+)\) scale\(([\d.]+)\)">(.*?)</g><text x="[\d.]+" y="[\d.]+">([^<]+)</text><text[^>]*>([^<]*)</text><text[^>]*>([^<]*)</text>', t, re.S):
            rows.append({'code': r.code, 'src': r.source, 'scale': float(g.group(3)), 'svg': g.group(4), 'name': g.group(5).strip(), 'spec': g.group(6).strip(), 'unit': g.group(7).strip()})
print(len(rows))
seen = {}
for x in rows:
    k = x['name']
    if k not in seen or ('×' in x['spec'] and '×' not in seen[k]['spec']): seen[k] = x
print(len(seen))
for k, x in seen.items(): print(k, '|', x['spec'], '|', x['unit'], '|', x['code'], len(x['svg']))
json.dump(list(seen.values()), open(os.path.join(SP, 'fac_rows.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
