# -*- coding: utf-8 -*-
"""필답 기출을 주제별로 묶어 출제 빈도를 문항에 기록한다.

같은 주제가 표현만 바꿔 되풀이 출제되므로 문항을 그대로 세면 빈출을
알 수 없다. 문제문·답의 낱말 겹침으로 군집을 만들고, 그 주제가 몇 개
회차에 나왔는지를 각 문항의 freq_rounds 에 쓴다.

예상문제는 회차 개념이 없으므로, 기출 주제와 묶이면 그 빈도를 물려받는다.
빈출 주제를 예상문제로 먼저 익히는 흐름을 만들기 위해서다.

사용:
  python manage.py tag_essay_frequency --dry-run
  python manage.py tag_essay_frequency
"""
import hashlib
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.models import Certification, GisaEssayQuestion

STOP = re.compile(
    r'(에\s*대하여|에\s*대해|다음|설명하시오|쓰시오|서술하시오|기술하시오|구하시오|'
    r'채우시오|고르시오|무엇인가|무엇이라|하는가|것은|것을|하시오|알맞은|각각|모두|'
    r'대하여|관하여|경우|이하|이상|가지|보기|안에|들어갈|해당하는|나열한|따른|의한|'
    r'있는|하는|되는|위한|위하여)')

NOISE = {'생태', '환경', '자연', '지역', '조성', '방법', '기능', '특징', '개념', '정의',
         '설명', '내용', '사항', '경우', '이용', '관리', '계획', '사업', '대상', '구분',
         '종류', '이유', '변화', '영향', '이란', '무엇', '어떤', '이때', '이를', '그에',
         '따라', '통해', '위해', '또는', '그리고', '한다', '있다', '된다', '하여', '되어'}

THRESHOLD = 0.40


def keywords(q):
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


class Command(BaseCommand):
    help = '필답 기출의 주제별 출제 빈도를 계산해 문항에 기록한다'

    def add_arguments(self, parser):
        parser.add_argument('--cert', default='자연생태복원기사')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--threshold', type=float, default=THRESHOLD)

    def handle(self, *args, **opt):
        cert = Certification.objects.filter(name=opt['cert']).first()
        if not cert:
            self.stderr.write(f'자격증 없음: {opt["cert"]}')
            return

        exams = list(GisaEssayQuestion.objects
                     .filter(certification=cert, source='기출')
                     .order_by('-year', '-round', 'number'))
        preds = list(GisaEssayQuestion.objects
                     .filter(certification=cert, source='예상')
                     .order_by('section', 'number'))

        # 1) 기출로 주제 군집을 만든다
        clusters = []      # [{'kw': set, 'members': [q], 'rounds': set}]
        for q in exams:
            kw = keywords(q)
            best, bs = None, 0.0
            for c in clusters:
                s = sim(kw, c['kw'])
                if s > bs:
                    best, bs = c, s
            if best and bs >= opt['threshold']:
                best['members'].append(q)
                best['kw'] |= kw
                best['rounds'].add((q.year, q.round))
            else:
                clusters.append({'kw': set(kw), 'members': [q],
                                 'rounds': {(q.year, q.round)}})

        # 2) 예상문제를 기출 주제에 붙인다 (회차 수는 늘리지 않는다)
        attached = 0
        for q in preds:
            kw = keywords(q)
            best, bs = None, 0.0
            for c in clusters:
                s = sim(kw, c['kw'])
                if s > bs:
                    best, bs = c, s
            if best and bs >= opt['threshold']:
                best.setdefault('preds', []).append(q)
                attached += 1

        clusters.sort(key=lambda c: -len(c['rounds']))

        self.stdout.write(f'기출 {len(exams)}문항 → 주제 {len(clusters)}개')
        self.stdout.write(f'예상 {len(preds)}문항 중 {attached}개가 기출 주제와 연결')

        dist = {}
        for c in clusters:
            n = len(c['rounds'])
            dist[n] = dist.get(n, 0) + 1
        self.stdout.write('\n[주제별 출제 회차 수 분포]')
        for n in sorted(dist, reverse=True):
            self.stdout.write(f'  {n}회 출제 주제 {dist[n]}개')

        self.stdout.write('\n[상위 12개 주제]')
        for c in clusters[:12]:
            rs = ' '.join(f'{y}-{r}' for y, r in sorted(c['rounds'], reverse=True)[:8])
            self.stdout.write(f'  {len(c["rounds"]):2d}회  {c["members"][0].text[:46]}')
            self.stdout.write(f'        {rs}')

        if opt['dry_run']:
            self.stdout.write(self.style.WARNING('\n[dry-run] 저장하지 않음'))
            return

        n = 0
        with transaction.atomic():
            for c in clusters:
                rounds = sorted(c['rounds'], reverse=True)
                key = hashlib.md5(
                    c['members'][0].text[:80].encode('utf-8')).hexdigest()[:16]
                note = ' '.join(f'{y}-{r}' for y, r in rounds[:14])
                if len(rounds) > 14:
                    note += f' 외 {len(rounds) - 14}'
                for q in c['members'] + c.get('preds', []):
                    q.topic_key = key
                    q.freq_rounds = len(rounds)
                    q.freq_note = note[:200]
                    q.save(update_fields=['topic_key', 'freq_rounds', 'freq_note'])
                    n += 1

        self.stdout.write(self.style.SUCCESS(f'\n기록 완료: {n}문항'))
