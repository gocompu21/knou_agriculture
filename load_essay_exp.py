"""작성한 필답 해설을 검증하고 reference 필드에 넣는다.

해설은 화면에서 `qtext` 필터를 거치므로, 넣기 전에 실제로 렌더링해 보고
SVG가 필터에 걸려 사라지지는 않는지, 표가 표로 바뀌는지 확인한다.
"""
import argparse, glob, json, os, re, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q
from gisa.templatetags.gisa_filters import qtext


# 객관식에서만 성립하는 표현. 실기 필답 해설에 있으면 수험생이 필기 문제로 오해한다
_OBJECTIVE = re.compile(
    r'고르게|고르는|고르면|선지|보기 중|틀린 것|옳은 것|아닌 것은|오답 패턴|객관식'
)


def body_len(text):
    """표와 SVG 마크업을 뺀 본문 길이. 분량 판단은 이 값으로 한다."""
    t = re.sub(r'\[svg\].*?\[/svg\]', '', text or '', flags=re.DOTALL)
    t = re.sub(r'^\s*\|.*$', '', t, flags=re.MULTILINE)
    return len(t.strip())


def check(text):
    """넣어도 되는지 판정. 반환값은 경고 목록(비어 있으면 통과)."""
    warns = []
    if not (text or '').strip():
        return ['빈 해설']
    html = str(qtext(text))

    m = _OBJECTIVE.search(text)
    if m:
        warns.append(f'객관식 표현 "{m.group()}"')

    # LaTeX 천단위 표기는 필터가 중괄호를 처리하지 않아 그대로 노출된다
    if '{,}' in text:
        warns.append('{,} 표기 (중괄호가 화면에 노출됨)')

    # SVG가 필터에 걸려 통째로 사라지면 그림 없는 해설이 된다
    want = text.count('[svg]')
    got = html.count('<svg')
    if want != got:
        warns.append(f'SVG {want}개 중 {got}개만 렌더링 — 금지 요소 확인')

    # 마크다운 표가 표로 안 바뀌면 파이프 문자가 그대로 보인다
    if '|---' in text or '| ---' in text:
        if '<table' not in html:
            warns.append('표가 변환되지 않음')

    # 태그를 직접 쓴 흔적 (escape 되어 글자로 보인다)
    for tag in ('&lt;div', '&lt;p&gt;', '&lt;br'):
        if tag in html:
            warns.append(f'HTML 태그가 글자로 노출됨 ({tag})')
            break
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_eco2022_exp')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    rows = []
    for p in sorted(glob.glob(os.path.join(args.src, 'exp_*.json'))):
        rows.extend(json.load(open(p, encoding='utf-8')))
    if not rows:
        print('결과 파일(exp_*.json)이 없습니다.'); return

    ok, bad = [], []
    for r in sorted(rows, key=lambda x: x.get('number', 0)):
        q = Q.objects.filter(pk=r['pk']).first()
        if not q:
            bad.append((r, ['없는 pk'])); continue
        w = check(r.get('reference'))
        (bad if w else ok).append((r, w) if w else (r, q))

    print(f'{len(rows)}건 — 통과 {len(ok)} / 문제 {len(bad)}')
    for r, w in bad:
        print(f'  [{r.get("number")}] {", ".join(w)}')

    print('\n번호  본문   전체   표  그림')
    for r, q in ok:
        t = r['reference']
        print(f'  {r["number"]:>2}  {body_len(t):>4}  {len(t):>5}   '
              f'{"O" if "|---" in t or "| ---" in t else "-"}   '
              f'{t.count("[svg]") or "-"}')

    if not args.apply:
        print('\n(--apply 를 붙이면 DB에 반영합니다)'); return

    for r, q in ok:
        q.reference = r['reference']
        q.save(update_fields=['reference'])
    print(f'\n반영 {len(ok)}건')


if __name__ == '__main__':
    main()
