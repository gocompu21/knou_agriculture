"""직접 읽고 묶은 주제 그룹을 topic_key / freq_rounds / freq_note 에 반영한다.

자동 군집화(analyze_essay_freq.py)는 [box] 지문을 버리고 발문 상투어만 남겨
"편향천이 / LID / 자기설계적 복원"을 한 그룹으로 묶는 오류를 냈다. 99개 그룹 중
71개가 오분류였다. 그래서 사람이(에이전트가) 문항을 직접 읽어 묶는다.
"""
import argparse, glob, hashlib, json, os, sys, collections, django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction
from gisa.models import GisaEssayQuestion as Q


def load_groups(src):
    """[{group: '주제명', pks: [...]}, ...] 를 모은다."""
    out = []
    for p in sorted(glob.glob(os.path.join(src, '*_done.json'))):
        for g in json.load(open(p, encoding='utf-8')):
            pks = [int(x) for x in g.get('pks', [])]
            if pks:
                out.append({'name': g.get('group', ''), 'pks': pks})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='_essay_group')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    groups = load_groups(args.src)
    if not groups:
        print('결과 파일(*_done.json)이 없습니다.'); return

    qs = {q.pk: q for q in Q.objects.filter(source='기출')}
    seen, dup = set(), []
    for g in groups:
        for pk in g['pks']:
            if pk in seen:
                dup.append(pk)
            seen.add(pk)

    missing = sorted(set(qs) - seen)
    unknown = sorted(seen - set(qs))

    print(f'문항 {len(qs)} / 묶인 문항 {len(seen)} / 그룹 {len(groups)}')
    if dup:
        print(f'  ⚠ 두 그룹에 든 문항 {len(dup)}개: {dup[:10]}')
    if unknown:
        print(f'  ⚠ 없는 pk {len(unknown)}개: {unknown[:10]}')
    if missing:
        print(f'  ⚠ 어느 그룹에도 없는 문항 {len(missing)}개: {missing[:10]}')
    if dup or unknown or missing:
        print('\n위 문제를 고친 뒤 다시 실행하세요.'); return

    sizes = collections.Counter(len(g['pks']) for g in groups)
    print('\n그룹 크기 분포')
    for n in sorted(sizes, reverse=True)[:8]:
        print(f'  {n}문항짜리 그룹 {sizes[n]}개')

    multi = [g for g in groups if len(g['pks']) > 1]
    print(f'\n되풀이 출제 그룹 {len(multi)}개 (문항 {sum(len(g["pks"]) for g in multi)}개)')
    for g in sorted(multi, key=lambda x: -len(x['pks']))[:10]:
        rounds = sorted({(qs[p].year, qs[p].round) for p in g['pks']}, reverse=True)
        print(f'  {len(rounds):>2}회  {g["name"][:34]:<34} '
              f'{" ".join(f"{y}-{r}" for y, r in rounds[:6])}')

    if not args.apply:
        print('\n(--apply 를 붙이면 반영합니다)'); return

    with transaction.atomic():
        for g in groups:
            items = [qs[p] for p in g['pks']]
            # 같은 그룹이 늘 같은 키를 갖도록 pk 목록에서 만든다
            key = hashlib.md5(
                ','.join(str(p) for p in sorted(g['pks'])).encode()).hexdigest()[:16]
            rounds = sorted({(q.year, q.round) for q in items}, reverse=True)
            note = ' '.join(f'{y}-{r}' for y, r in rounds)
            for q in items:
                q.topic_key = key
                q.freq_rounds = len(rounds)
                q.freq_note = note
                q.save(update_fields=['topic_key', 'freq_rounds', 'freq_note'])
    print(f'\n반영 {len(seen)}문항 / {len(groups)}그룹')


if __name__ == '__main__':
    main()
