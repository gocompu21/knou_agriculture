# -*- coding: utf-8 -*-
"""필답 문항을 출제기준(2025~2027) 주요항목 8개로 분류한다.

⚠️ 화면에서는 더 이상 이 값을 쓰지 않는다. topic_group(주제 분류)이 대신한다.

이 분류는 실패했다. 424문항(58%)이 8번 "생태계 종합평가"에 몰려 SLOSS 논쟁도
지방의제 21도 거기 들어갔다. 8번 키워드가 57개로 다른 항목(4~33개)보다 압도적인
데다 ('법', 1) 처럼 아무 데나 걸리는 것이 있었고, 예상문제를 지운 뒤로는 모든
문항의 section 이 '기출'이라 SECTION_FALLBACK['기출']=8 로 109문항이 무조건
8번에 떨어졌다.

근본적으로 출제기준 8항목은 실무 수행 순서(구상→기반환경→…→종합평가)라
학술 지식을 묻는 필답 기출과 맞지 않는다. 그래서 "실제로 무엇을 묻는가"로
나눈 topic_group 을 따로 두었다(renumber_essay.py 참조).

이 명령을 다시 실행하면 잘못된 분류가 되살아나므로 쓰지 말 것. 출제기준과의
대응이 필요할 때를 위해 필드와 코드만 남겨 둔다.

사용:
  python manage.py classify_essay_std
  python manage.py classify_essay_std --dry-run
  python manage.py classify_essay_std --show 8      # 특정 항목 분류 결과 보기
"""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from gisa.models import Certification, GisaEssayQuestion

# 출제기준 주요항목 8개
MAJOR_NAMES = {
    1: '생태복원 구상',
    2: '생태기반환경복원 계획',
    3: '복원 후 관리계획',
    4: '서식지 복원계획',
    5: '생태시설물 계획',
    6: '모니터링 계획',
    7: '생태복원 현장관리',
    8: '생태계 종합평가',
}

# (키워드, 가중치) — 가중치가 큰 키워드가 우선
KEYWORDS = {
    1: [('목표종', 3), ('공간구상', 3), ('사업목표', 3), ('핵심구역', 3), ('완충구역', 3),
        ('전이구역', 3), ('협력구역', 3), ('프로그래밍', 3), ('컨셉', 2), ('기본구상', 3),
        ('생물권보전지역', 2), ('MAB', 2), ('적지분석', 2), ('대안', 1), ('기본방향', 2)],
    2: [('토지이용', 3), ('동선', 3), ('지형복원', 3), ('표토', 3), ('객토', 3), ('절토', 3),
        ('성토', 3), ('토양', 2), ('토심', 3), ('토성', 3), ('사토', 2), ('식토', 2),
        ('수환경', 3), ('수리', 2), ('수문', 2), ('토양개량', 3), ('비탈면', 2), ('녹화', 2),
        ('식재기반', 3), ('배수', 2), ('용적', 2), ('토량', 3), ('오염토양', 3), ('LID', 3),
        ('저영향개발', 3), ('빗물', 2), ('우수', 2), ('불투수', 2), ('투수', 2)],
    3: [('유지관리', 3), ('관리계획', 3), ('순응적', 3), ('이용자 관리', 3), ('관리목표', 3),
        ('사후관리', 3), ('세부관리', 3), ('멀칭', 2), ('전정', 2), ('시비', 2)],
    4: [('서식지', 3), ('서식처', 3), ('숲복원', 3), ('초지', 3), ('습지', 3), ('생태통로', 3),
        ('하천', 2), ('인공지반', 3), ('벽면녹화', 3), ('옥상', 2), ('비오톱 조성', 3),
        ('양서류', 2), ('조류', 2), ('곤충', 2), ('어류', 2), ('남생이', 2), ('반딧불이', 2),
        ('식재', 2), ('파종', 2), ('이식', 2), ('수생식물', 2), ('정수식물', 2), ('식물종', 1),
        ('여울', 2), ('소(', 1), ('호안', 2), ('대체습지', 3), ('생태네트워크', 2),
        ('생태축', 2), ('코리더', 2), ('단편화', 2), ('파편화', 2), ('메타개체군', 2)],
    5: [('관찰시설', 3), ('체험시설', 3), ('전시', 2), ('편의시설', 3), ('보전시설', 3),
        ('관리시설', 3), ('탐조', 3), ('데크', 3), ('안내판', 2), ('울타리', 2),
        ('유도울타리', 3), ('시설물', 2)],
    6: [('모니터링', 3), ('조사주기', 2), ('조사시기', 2), ('예산 수립', 2)],
    7: [('공정', 3), ('예산관리', 3), ('품질', 3), ('안전', 3), ('공사', 2), ('내역', 3),
        ('품셈', 3), ('시방', 3), ('수량표', 3), ('원가', 3), ('시공', 2), ('공법', 2)],
    8: [('비오톱', 3), ('가치평가', 3), ('생태자연도', 3), ('녹지자연도', 3), ('식생보전등급', 3),
        ('국토환경성평가', 3), ('종다양', 3), ('군집', 3), ('식생조사', 3), ('경관생태', 3),
        ('천이', 3), ('개체군', 3), ('먹이', 2), ('생물다양성', 3), ('방형구', 3),
        ('우점도', 3), ('피도', 3), ('상대밀도', 3), ('중요도', 2), ('빈도', 2),
        ('지수', 2), ('유사도', 3), ('Shannon', 3), ('Jaccard', 3), ('Sorensen', 3),
        ('생물지리', 3), ('SLOSS', 3), ('패치', 3), ('조각', 2), ('경관', 2),
        ('멸종위기', 2), ('IUCN', 3), ('교란', 2), ('환경영향평가', 3), ('전략환경', 3),
        ('생태계서비스', 3), ('환경기준', 3), ('수질', 2), ('생물지표', 3), ('채집', 3),
        ('포획', 2), ('조사방법', 3), ('자연환경조사', 3), ('니치', 3), ('생산성', 2),
        ('생산력', 2), ('물질순환', 2), ('질소순환', 3), ('먹이망', 3), ('생태피라미드', 3),
        ('용도지역', 2), ('용도지구', 2), ('국토계획', 2), ('환경계획', 2), ('협약', 2),
        ('의정서', 2), ('법', 1)],
}

# 키워드 매칭 실패 시 영역별 기본 항목
SECTION_FALLBACK = {
    '생태학': 8,
    '생태조사방법': 8,
    '법규': 8,
    '환경영향평가': 8,
    '환경계획A': 1,
    '환경계획B': 1,
    '생태복원': 4,
    '기출': 8,
}


def classify(text_blob, section):
    scores = Counter()
    for major, kws in KEYWORDS.items():
        for kw, w in kws:
            if kw in text_blob:
                scores[major] += w
    if scores:
        top = scores.most_common(1)[0]
        if top[1] >= 2:      # 가중치 2 이상일 때만 신뢰
            return top[0]
    return SECTION_FALLBACK.get(section, 0)


class Command(BaseCommand):
    help = '필답 문항을 출제기준 주요항목으로 분류한다'

    def add_arguments(self, parser):
        parser.add_argument('--cert', default='자연생태복원기사')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--show', type=int, default=0,
                            help='해당 주요항목으로 분류된 문항 예시 출력')

    def handle(self, *args, **opt):
        cert = Certification.objects.filter(name=opt['cert']).first()
        if not cert:
            self.stderr.write(f'자격증 없음: {opt["cert"]}')
            return

        qs = GisaEssayQuestion.objects.filter(certification=cert)
        result = Counter()
        changed = []

        for q in qs:
            blob = ' '.join([q.text or '', ' '.join(q.answer_items or []),
                             q.answer_text or ''])
            major = classify(blob, q.section)
            result[major] += 1
            if major != q.std_major:
                changed.append((q, major))

        self.stdout.write('[분류 결과]')
        for m in sorted(result):
            name = MAJOR_NAMES.get(m, '미분류')
            self.stdout.write(f'  {m} {name}: {result[m]}문항')

        if opt['show']:
            self.stdout.write(f'\n[{opt["show"]}번 항목 예시]')
            shown = 0
            for q in qs:
                blob = ' '.join([q.text or '', ' '.join(q.answer_items or [])])
                if classify(blob, q.section) == opt['show']:
                    self.stdout.write(f'  [{q.section}] {q.text[:60]}')
                    shown += 1
                    if shown >= 15:
                        break

        if opt['dry_run']:
            self.stdout.write(self.style.WARNING(f'\n[dry-run] {len(changed)}건 변경 예정'))
            return

        with transaction.atomic():
            for q, major in changed:
                q.std_major = major
                q.save(update_fields=['std_major'])
        self.stdout.write(self.style.SUCCESS(f'\n분류 저장 완료: {len(changed)}건 갱신'))
