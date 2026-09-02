"""재서술한 문제문을 검증하고 DB에 반영한다.

용어·수치를 그대로 두는 것이 이 작업의 전제라, 반영 전에 원문과 대조해
숫자와 법령명이 사라지지 않았는지 확인한다. 위반이 있으면 그 건만 건너뛴다.
"""
import argparse, glob, json, os, re, sys, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from gisa.models import GisaEssayQuestion as Q

NUM = re.compile(r'\d+(?:[,.]\d+)*')
LAW = re.compile(r'「[^」]+」')
# 답 개수를 지시하는 표현은 정답 수와 직결되므로 반드시 살아 있어야 한다
CNT = re.compile(r'(\d+)\s*가지')


def numbers(s):
    """수치 비교용. 자릿점과 단위 표기 차이는 무시한다."""
    return sorted(n.replace(',', '') for n in NUM.findall(s or ''))


def check(old, new):
    """반영해도 되는지 판정. 반환값은 경고 목록(비어 있으면 통과)."""
    warns = []
    if not new or not new.strip():
        return ['빈 문자열']
    if new.strip() == (old or '').strip():
        return ['변경 없음']

    # 숫자가 통째로 사라지면 조건이 날아간 것이다
    o_n, n_n = numbers(old), numbers(new)
    lost = [x for x in o_n if x not in n_n]
    if lost:
        warns.append(f'수치 누락 {lost}')

    # 답 개수 지시는 정답 채점과 직결된다
    o_c, n_c = CNT.findall(old or ''), CNT.findall(new)
    if o_c != n_c:
        warns.append(f'개수 지시 변경 {o_c}→{n_c}')

    # 법령명은 정확히 유지돼야 조문을 찾을 수 있다
    o_l, n_l = set(LAW.findall(old or '')), set(LAW.findall(new))
    if o_l - n_l:
        warns.append(f'법령명 누락 {sorted(o_l - n_l)}')

    # 지문 상자와 표는 구조가 유지돼야 화면이 깨지지 않는다
    for tag in ('[box]', '[/box]'):
        if (old or '').count(tag) != new.count(tag):
            warns.append(f'{tag} 개수 불일치')
    if (old or '').count('|') and not new.count('|'):
        warns.append('표 소실')
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_essay_textrw')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='경고가 있어도 반영 (개별 검토를 마친 경우에만)')
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, '*_done.json')))
    if not files:
        print('결과 파일(*_done.json)이 없습니다.'); return

    rows = []
    for p in files:
        with open(p, encoding='utf-8') as f:
            rows.extend(json.load(f))
    print(f'{len(files)}개 파일 / {len(rows)}건')

    ok, skipped, missing = [], [], 0
    seen = set()
    for r in rows:
        pk = r.get('pk')
        new = (r.get('new_text') or '').strip()
        if pk in seen:
            continue
        seen.add(pk)
        q = Q.objects.filter(pk=pk).first()
        if not q:
            missing += 1; continue
        w = check(q.text, new)
        if w and not args.force:
            skipped.append((q, new, w))
        else:
            ok.append((q, new))

    print(f'통과 {len(ok)} / 보류 {len(skipped)} / 없는 pk {missing}')
    if skipped:
        print('\n── 보류 ──')
        for q, new, w in skipped[:40]:
            print(f'[{q.pk}] {q.label} {q.number}번 — {", ".join(w)}')
            if '변경 없음' not in w:
                print(f'   old: {(q.text or "")[:90]}')
                print(f'   new: {new[:90]}')

    if not args.apply:
        print('\n(--apply 를 붙이면 DB에 반영합니다)'); return

    # 되돌릴 수 있도록 원문을 남긴다
    bak = '_essay_text_backup.json'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8') as f:
            json.dump({str(q.pk): q.text for q in Q.objects.all()},
                      f, ensure_ascii=False, indent=1)
        print(f'원문 백업 → {bak}')

    for q, new in ok:
        q.text = new
        q.save(update_fields=['text'])
    print(f'반영 {len(ok)}건')


if __name__ == '__main__':
    main()
