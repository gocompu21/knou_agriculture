# -*- coding: utf-8 -*-
"""필답 기출을 주제별로 묶어 출제 빈도를 문항에 기록한다.

같은 주제가 표현만 바꿔 되풀이 출제되므로 문항을 그대로 세면 빈출을
알 수 없다. 문제문·답의 낱말 겹침으로 군집을 만들고, 그 주제가 몇 장의
시험지에 나왔는지를 각 문항의 freq_rounds 에 쓴다.

**기사와 산업기사는 함께 묶어 센다**(`essay_topics.SIBLING_GROUPS`).
두 급수가 같은 문제를 돌려쓰므로 따로 세면 빈출이 흩어져 보이지 않는다 —
식물보호에서 배액 조제 계산은 두 급수 18장 전부에 나왔는데, 급수별로
세면 "기사 9장 / 산기 9장" 으로 갈려 최상위 주제인 줄 알 수 없다.
그래서 시험지를 (자격증, 연도, 회차) 로 세고, 묶음 전체에서 군집을 만든다.
급수가 다른 문항이 한 주제로 묶이므로 topic_key 도 두 자격증이 공유한다.

예상문제는 회차 개념이 없으므로, 기출 주제와 묶이면 그 빈도를 물려받는다.
빈출 주제를 예상문제로 먼저 익히는 흐름을 만들기 위해서다.

⚠️ **자연생태복원기사는 다시 돌리지 말 것.** 군집이 바뀌면 topic_key 가 바뀌고,
거기 묶여 있는 것이 둘이나 끊어진다 — 쪽집게 노트 제목 파일
(`essay_topic_titles.json`, 키가 대표 문항의 '연도-회차-번호'라 대표가 바뀌면
엉뚱한 주제에 붙는다)과 정리 자료(freq58·calc)의 topic_key 연결이다.
실제로 2026-09 에 잡음 낱말을 늘리고 `[eq]` 를 걷어내면서 자연생태복원 군집이
563 → 514 개로 달라졌다. 그래서 `--force` 없이는 거부한다.

사용:
  python manage.py tag_essay_frequency --cert 식물보호기사 --dry-run
  python manage.py tag_essay_frequency --cert 식물보호기사   # 묶음이면 둘 다 돈다
"""
import hashlib
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.essay_topics import siblings, threshold as cert_threshold
from gisa.models import Certification, GisaEssayQuestion

STOP = re.compile(
    r'(에\s*대하여|에\s*대해|다음|설명하시오|쓰시오|서술하시오|기술하시오|구하시오|'
    r'채우시오|고르시오|무엇인가|무엇이라|하는가|것은|것을|하시오|알맞은|각각|모두|'
    r'대하여|관하여|경우|이하|이상|가지|보기|안에|들어갈|해당하는|나열한|따른|의한|'
    r'있는|하는|되는|위한|위하여)')

NOISE = {'생태', '환경', '자연', '지역', '조성', '방법', '기능', '특징', '개념', '정의',
         '설명', '내용', '사항', '경우', '이용', '관리', '계획', '사업', '대상', '구분',
         '종류', '이유', '변화', '영향', '이란', '무엇', '어떤', '이때', '이를', '그에',
         '따라', '통해', '위해', '또는', '그리고', '한다', '있다', '된다', '하여', '되어',
         # 식물보호 기출에서 거의 모든 문항에 나와 주제를 가르지 못하는 낱말.
         # 상자 안까지 세면서 발문 상투어가 더 많이 걸려 들어와 늘렸다.
         '작물', '식물', '발생', '사용', '문제', '아래', '용어', '해당', '보고',
         '괄호', '특징', '학명', '다음', '각각', '알맞은', '무엇', '쓰시', '이용',
         '중심', '중심으로', '방제', '피해', '대책', '조사'}

THRESHOLD = 0.40
# 겹치는 낱말이 이보다 적으면 묶지 않는다. sim() 설명 참조.
MIN_SHARED = 3


def keywords(q):
    """문항을 대표하는 낱말 집합.

    **`[box]` 안은 버리지 않는다.** 자연생태복원은 상자가 긴 지문이라 걷어내는
    편이 나았지만, 식물보호는 묻는 알맹이가 상자 안에 들어 있다 — 빈칸 문항의
    상자 밖은 "다음 설명을 보고 괄호 안에 알맞은 용어를 쓰시오"뿐이라, 상자를
    버리면 낱말이 거의 남지 않아 **빈칸 유형끼리 통째로 한 덩어리가 된다**
    (실제로 29문항이 그렇게 뭉쳤다). 상자가 아주 길면 앞부분만 쓴다.
    """
    box = ' '.join(re.findall(r'\[box\](.*?)\[/box\]', q.text or '', flags=re.S))
    outside = re.sub(r'\[box\].*?\[/box\]', ' ', q.text or '', flags=re.S)
    s = outside + ' ' + box[:400] + ' ' + ' '.join((q.answer_items or [])[:3])
    # 계산식은 숫자뿐이라 주제를 가르지 못하고, 오히려 단위(mL·kg)가 겹쳐
    # 서로 다른 계산 문항을 한 주제로 붙여 버린다.
    s = re.sub(r'\[eq\].*?\[/eq\]', ' ', s, flags=re.S)
    s = re.sub(r'[①-⑮㉠-㉦ㄱ-ㅎ]', ' ', s)
    s = STOP.sub(' ', s)
    ko = {w for w in re.findall(r'[가-힣]{2,}', s) if w not in NOISE}
    en = {w.upper() for w in re.findall(r'[A-Za-z]{2,}', s)}
    return ko | en


def sim(a, b):
    if not a or not b:
        return 0.0
    # 겹치는 낱말이 너무 적으면 비율이 높아도 우연이다. 낱말이 서너 개뿐인
    # 짧은 문항은 min() 을 분모로 쓰는 이 식에서 아무하고나 1.0 이 나온다.
    if len(a & b) < MIN_SHARED:
        return 0.0
    return len(a & b) / min(len(a), len(b))


class Command(BaseCommand):
    help = '필답 기출의 주제별 출제 빈도를 계산해 문항에 기록한다'

    # 이미 태깅이 끝났고 topic_key 에 다른 자료가 묶여 있는 자격증.
    # 다시 돌리면 그 연결이 끊어지므로 --force 를 요구한다(머리말 참조).
    LOCKED = {'자연생태복원기사'}

    def add_arguments(self, parser):
        parser.add_argument('--cert', default='자연생태복원기사')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true',
                            help='태깅이 끝난 자격증을 다시 돌린다(topic_key 가 바뀐다)')
        parser.add_argument('--threshold', type=float, default=None,
                            help='군집 임계값. 안 주면 essay_topics.threshold()')

    def handle(self, *args, **opt):
        # 묶음이 있으면 급수를 함께 돌린다. 없으면 자기 하나만 담긴다.
        names = siblings(opt['cert'])
        locked = self.LOCKED & set(names)
        if locked and not opt['dry_run'] and not opt['force']:
            self.stderr.write(
                f'{", ".join(sorted(locked))}: 이미 태깅이 끝났다. 다시 돌리면 '
                'topic_key 가 바뀌어 쪽집게 노트 제목과 정리 자료 연결이 끊어진다. '
                '정말 다시 만들려면 --force 를 붙여라.')
            return
        certs = list(Certification.objects.filter(name__in=names))
        if not certs:
            self.stderr.write(f'자격증 없음: {opt["cert"]}')
            return
        cut = opt['threshold'] or cert_threshold(opt['cert'])
        if len(certs) > 1:
            self.stdout.write('묶어서 센다: ' + ' + '.join(c.name for c in certs))

        exams = list(GisaEssayQuestion.objects
                     .filter(certification__in=certs, source='기출')
                     .order_by('certification', '-year', '-round', 'number'))
        preds = list(GisaEssayQuestion.objects
                     .filter(certification__in=certs, source='예상')
                     .order_by('certification', 'section', 'number'))

        # 시험지는 (자격증, 연도, 회차) 로 센다 — 급수가 다르면 다른 시험지다.
        short = {c.pk: ('산기' if '산업' in c.name else '기사') for c in certs}
        one = len(certs) == 1

        def sheet(q):
            return (q.certification_id, q.year, q.round)

        def sheet_label(s):
            if one:
                return '%d-%d' % (s[1], s[2])
            return '%s%d-%d' % (short.get(s[0], ''), s[1], s[2])

        # 1) 기출로 주제 군집을 만든다
        clusters = []      # [{'kw': set, 'members': [q], 'rounds': set}]
        for q in exams:
            kw = keywords(q)
            best, bs = None, 0.0
            for c in clusters:
                s = sim(kw, c['kw'])
                if s > bs:
                    best, bs = c, s
            if best and bs >= cut:
                best['members'].append(q)
                best['kw'] |= kw
                best['rounds'].add(sheet(q))
            else:
                clusters.append({'kw': set(kw), 'members': [q],
                                 'rounds': {sheet(q)}})

        # 2) 예상문제를 기출 주제에 붙인다 (회차 수는 늘리지 않는다)
        attached = 0
        for q in preds:
            kw = keywords(q)
            best, bs = None, 0.0
            for c in clusters:
                s = sim(kw, c['kw'])
                if s > bs:
                    best, bs = c, s
            if best and bs >= cut:
                best.setdefault('preds', []).append(q)
                attached += 1

        clusters.sort(key=lambda c: -len(c['rounds']))

        self.stdout.write(f'기출 {len(exams)}문항 → 주제 {len(clusters)}개')
        self.stdout.write(f'예상 {len(preds)}문항 중 {attached}개가 기출 주제와 연결')

        dist = {}
        for c in clusters:
            n = len(c['rounds'])
            dist[n] = dist.get(n, 0) + 1
        self.stdout.write(f'시험지 {len({sheet(q) for q in exams})}장')
        self.stdout.write('\n[주제별 출제 시험지 수 분포]')
        for n in sorted(dist, reverse=True):
            self.stdout.write(f'  {n}장에 출제 — 주제 {dist[n]}개')
        two = sum(v for k, v in dist.items() if k >= 2)
        self.stdout.write(f'  2장 이상 = {two}개 (쪽집게 노트 대상)')

        self.stdout.write('\n[상위 12개 주제]')
        for c in clusters[:12]:
            rs = ' '.join(sheet_label(x) for x in sorted(c['rounds'], reverse=True)[:8])
            self.stdout.write(f'  {len(c["rounds"]):2d}장  {c["members"][0].text[:46]}')
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
                note = ' '.join(sheet_label(x) for x in rounds[:14])
                if len(rounds) > 14:
                    note += f' 외 {len(rounds) - 14}'
                for q in c['members'] + c.get('preds', []):
                    q.topic_key = key
                    q.freq_rounds = len(rounds)
                    q.freq_note = note[:200]
                    q.save(update_fields=['topic_key', 'freq_rounds', 'freq_note'])
                    n += 1

        self.stdout.write(self.style.SUCCESS(f'\n기록 완료: {n}문항'))
