# -*- coding: utf-8 -*-
"""필답 기출을 주제별로 묶어 출제 빈도를 센다.

같은 주제가 표현만 바뀌어 되풀이 출제되므로, 문항을 그대로 세면
빈출을 알 수 없다. 문제문·답의 낱말 겹침으로 군집을 만들어 센다.

사용:
  python analyze_essay_freq.py               # 상위 주제
  python analyze_essay_freq.py --top 60
  python analyze_essay_freq.py --min 3       # N회 이상만
"""
import argparse
import os
import re
import sys
from collections import defaultdict

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gisa.models import Certification, GisaEssayQuestion as Q   # noqa: E402

CERT = '자연생태복원기사'

STOP = re.compile(
    r'(에\s*대하여|에\s*대해|다음|설명하시오|쓰시오|서술하시오|기술하시오|구하시오|'
    r'채우시오|고르시오|무엇인가|무엇이라|하는가|것은|것을|하시오|알맞은|각각|모두|'
    r'대하여|관하여|경우|이하|이상|가지|보기|안에|들어갈|해당하는|나열한|따른|의한|'
    r'있는|하는|되는|위한|위하여)')

# 흔해서 주제 구분에 도움이 안 되는 낱말
NOISE = {'생태', '환경', '자연', '지역', '조성', '방법', '기능', '특징', '개념', '정의',
         '설명', '내용', '사항', '경우', '이용', '관리', '계획', '사업', '대상', '구분',
         '종류', '이유', '변화', '영향', '이란', '무엇', '어떤', '이때', '이를', '그에',
         '따라', '통해', '위해', '또는', '그리고', '한다', '있다', '된다', '하여', '되어'}


def keywords(q):
    """주제를 대표할 만한 낱말 집합."""
    s = (q.text or '') + ' ' + ' '.join((q.answer_items or [])[:3])
    s = re.sub(r'\[box\].*?\[/box\]', ' ', s, flags=re.S)
    s = re.sub(r'[①-⑮㉠-㉦]', ' ', s)
    s = STOP.sub(' ', s)
    ko = {w for w in re.findall(r'[가-힣]{2,}', s) if w not in NOISE}
    en = {w.upper() for w in re.findall(r'[A-Za-z]{2,}', s)}
    return ko | en


def sim(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cert', default=CERT)
    ap.add_argument('--top', type=int, default=45)
    ap.add_argument('--min', type=int, default=2)
    ap.add_argument('--th', type=float, default=0.40)
    args = ap.parse_args()

    cert = Certification.objects.filter(name=args.cert).first()
    qs = list(Q.objects.filter(certification=cert, source='기출')
              .order_by('-year', '-round', 'number'))
    print(f'기출 {len(qs)}문항 / '
          f'{len(set((q.year, q.round) for q in qs))}개 회차\n')

    items = [(q, keywords(q)) for q in qs]

    # 탐욕적 군집 — 가장 최근 문항을 대표로 삼는다
    clusters = []          # [{'rep': q, 'kw': set, 'members': [q...]}]
    for q, kw in items:
        best, bs = None, 0.0
        for c in clusters:
            s = sim(kw, c['kw'])
            if s > bs:
                best, bs = c, s
        if best and bs >= args.th:
            best['members'].append(q)
            best['kw'] |= kw           # 주제 어휘를 넓힌다
        else:
            clusters.append({'rep': q, 'kw': set(kw), 'members': [q]})

    # 회차 수 기준으로 정렬 (같은 회차 중복은 1회로)
    def rounds_of(c):
        return {(m.year, m.round) for m in c['members']}

    clusters.sort(key=lambda c: (-len(rounds_of(c)), -len(c['members'])))

    shown = 0
    print(f'{"순":>3s} {"회차":>4s} {"문항":>4s}  주제 / 출제 회차')
    print('─' * 92)
    for c in clusters:
        rs = rounds_of(c)
        if len(rs) < args.min:
            continue
        shown += 1
        if shown > args.top:
            break
        years = ' '.join(f'{y}-{r}' for y, r in sorted(rs, reverse=True)[:12])
        more = f' 외 {len(rs)-12}' if len(rs) > 12 else ''
        title = re.sub(r'\s+', ' ', c['rep'].text)[:56]
        print(f'{shown:3d} {len(rs):4d} {len(c["members"]):4d}  {title}')
        print(f'{"":13s}{years}{more}')

    # 요약
    multi = [c for c in clusters if len(rounds_of(c)) >= 2]
    once = [c for c in clusters if len(rounds_of(c)) == 1]
    print(f'\n주제 {len(clusters)}개 | 2회 이상 출제 {len(multi)}개 | 1회만 {len(once)}개')
    tot = sum(len(c['members']) for c in multi)
    print(f'되풀이 주제가 차지하는 문항 {tot} / {len(qs)} '
          f'({tot / len(qs) * 100:.0f}%)')


if __name__ == '__main__':
    main()
