"""
기사시험 기출문제 텍스트 파일을 파싱하여 DB에 import하는 커맨드.

사용법:
    python manage.py import_gisa_questions 식물보호기사20111002.txt

텍스트 파일 형식:
    - 1행: "식물보호기사 2011년 10월 02일 필기 기출문제"
    - 과목 구분: "===..." 라인 사이에 "N과목 : 과목명"
    - 문제: "번호. 문제텍스트" + "① ... ② ... ③ ... ④ ..."
    - 정답표: "정답표" 섹션 아래 "번호: ① ..." 형태
"""
import os
import re
from datetime import date

from django.core.management.base import BaseCommand

from gisa.models import Certification, GisaExam, GisaQuestion, GisaSubject


# ① → 1, ② → 2, ③ → 3, ④ → 4
CIRCLE_MAP = {'①': '1', '②': '2', '③': '3', '④': '4'}


def parse_answer_table(text):
    """정답표 섹션에서 {문항번호: 정답번호} 딕셔너리 추출"""
    answers = {}
    # "1: ④" 또는 " 1: ④" 패턴 매칭
    for m in re.finditer(r'(\d+)\s*:\s*([①②③④])', text):
        num = int(m.group(1))
        ans = CIRCLE_MAP.get(m.group(2), '0')
        answers[num] = ans
    return answers


def parse_questions(text, subject_name, subject_obj, answer_map):
    """과목 텍스트에서 문제 목록을 추출하여 딕셔너리 리스트 반환"""
    questions = []

    # 문제 분리: "번호. " 로 시작하는 줄을 기준으로 분리
    # 번호는 1~100 범위
    pattern = re.compile(r'^(\d{1,3})\.\s+', re.MULTILINE)
    splits = pattern.split(text)

    # splits: ['앞부분', '번호1', '문제내용1', '번호2', '문제내용2', ...]
    i = 1
    while i < len(splits) - 1:
        num = int(splits[i])
        content = splits[i + 1].strip()
        i += 2

        # 보기 추출: ① ② ③ ④ 로 분리
        choice_pattern = re.compile(r'[①②③④]\s*')
        choice_splits = choice_pattern.split(content)

        # choice_splits[0] = 문제 텍스트, [1]~[4] = 보기 1~4
        q_text = choice_splits[0].strip()

        choices = ['', '', '', '']
        for j in range(1, min(5, len(choice_splits))):
            choices[j - 1] = choice_splits[j].strip()

        answer = answer_map.get(num, '0')

        questions.append({
            'number': num,
            'text': q_text,
            'choice_1': choices[0],
            'choice_2': choices[1],
            'choice_3': choices[2],
            'choice_4': choices[3],
            'answer': answer,
            'subject': subject_obj,
        })

    return questions


class Command(BaseCommand):
    help = '기사시험 기출문제 텍스트 파일을 DB에 import합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            help='import할 텍스트 파일 (예: 식물보호기사20111002.txt)',
        )
        parser.add_argument(
            '--data-dir',
            default=None,
            help='데이터 파일 디렉토리 (기본: kisa_exam/)',
        )

    def handle(self, *args, **options):
        filename = options['filename']

        # 파일 경로 결정
        if options['data_dir']:
            filepath = os.path.join(options['data_dir'], filename)
        else:
            # kisa_exam 디렉토리에서 찾기 (knou_agriculture의 형제 디렉토리)
            # __file__ → commands → management → gisa → knou_agriculture
            knou_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))
            kisa_dir = os.path.join(os.path.dirname(knou_dir), 'kisa_exam')
            filepath = os.path.join(kisa_dir, filename)

        if not os.path.exists(filepath):
            self.stderr.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {filepath}'))
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # 1행에서 메타정보 추출: "식물보호기사 2011년 10월 02일 필기 기출문제"
        first_line = full_text.split('\n')[0].strip()
        self.stdout.write(f'첫 줄: {first_line}')

        # 자격증명 추출
        cert_match = re.match(r'(.+?)\s+(\d{4})년\s+(\d{1,2})월\s+(\d{1,2})일\s+(필기|실기)', first_line)
        if not cert_match:
            self.stderr.write(self.style.ERROR(f'첫 줄에서 메타정보를 추출할 수 없습니다: {first_line}'))
            return

        cert_name = cert_match.group(1).strip()
        year = int(cert_match.group(2))
        month = int(cert_match.group(3))
        day = int(cert_match.group(4))
        exam_type = cert_match.group(5)
        exam_date = date(year, month, day)

        self.stdout.write(f'자격증: {cert_name}, {year}년 {month}월 {day}일 {exam_type}')

        # 자격증 등급 추정
        category = '기사'
        if '산업기사' in cert_name:
            category = '산업기사'
            cert_name = cert_name.replace('산업기사', '').strip()
        elif '기능사' in cert_name:
            category = '기능사'
            cert_name = cert_name.replace('기능사', '').strip()
        elif '기사' in cert_name:
            category = '기사'
            cert_name = cert_name.replace('기사', '').strip()

        # Certification 생성
        cert, created = Certification.objects.update_or_create(
            name=cert_name,
            category=category,
            defaults={'description': f'{cert_name} {category} 자격증'},
        )
        action = '생성' if created else '기존'
        self.stdout.write(f'자격증 {action}: {cert}')

        # GisaExam 생성 (회차는 같은 해 같은 유형 시험 수 + 1)
        existing_rounds = GisaExam.objects.filter(
            certification=cert, year=year, exam_type=exam_type
        ).count()
        exam_round = existing_rounds + 1

        exam, created = GisaExam.objects.update_or_create(
            certification=cert,
            year=year,
            round=exam_round,
            exam_type=exam_type,
            defaults={'exam_date': exam_date},
        )
        action = '생성' if created else '기존'
        self.stdout.write(f'시험 {action}: {exam}')

        # 정답표 파싱
        answer_section_match = re.search(r'정답표\s*=+\s*\n([\s\S]+)$', full_text)
        answer_map = {}
        if answer_section_match:
            answer_map = parse_answer_table(answer_section_match.group(1))
            self.stdout.write(f'정답 {len(answer_map)}개 추출')
        else:
            self.stderr.write(self.style.WARNING('정답표 섹션을 찾을 수 없습니다.'))

        # 과목 분리: "=====...N과목 : 과목명...=====" 패턴
        subject_pattern = re.compile(
            r'={3,}\s*\n\s*(\d+)과목\s*:\s*(.+?)\s*\n\s*={3,}',
            re.MULTILINE
        )
        subject_matches = list(subject_pattern.finditer(full_text))

        if not subject_matches:
            self.stderr.write(self.style.ERROR('과목 구분을 찾을 수 없습니다.'))
            return

        self.stdout.write(f'과목 {len(subject_matches)}개 발견')

        all_questions = []
        for idx, sm in enumerate(subject_matches):
            subj_order = int(sm.group(1))
            subj_name = sm.group(2).strip()

            # 과목 텍스트 범위: 현재 과목 구분선 끝 ~ 다음 과목 구분선 시작 (또는 정답표)
            start = sm.end()
            if idx + 1 < len(subject_matches):
                end = subject_matches[idx + 1].start()
            else:
                # 마지막 과목: 정답표 섹션 전까지
                ans_match = re.search(r'={3,}\s*\n\s*정답표', full_text[start:])
                if ans_match:
                    end = start + ans_match.start()
                else:
                    end = len(full_text)

            subject_text = full_text[start:end]

            # GisaSubject 생성
            subject, created = GisaSubject.objects.update_or_create(
                certification=cert,
                name=subj_name,
                defaults={'order': subj_order},
            )
            action = '생성' if created else '기존'
            self.stdout.write(f'  과목 {action}: {subj_order}. {subj_name}')

            # 문제 파싱
            questions = parse_questions(subject_text, subj_name, subject, answer_map)
            all_questions.extend(questions)
            self.stdout.write(f'    → {len(questions)}문제 파싱')

        # DB 저장
        created_count = 0
        updated_count = 0
        for qdata in all_questions:
            subject = qdata.pop('subject')
            number = qdata['number']

            _, created = GisaQuestion.objects.update_or_create(
                exam=exam,
                number=number,
                defaults={
                    'subject': subject,
                    **qdata,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n완료! 신규 {created_count}개, 갱신 {updated_count}개 (총 {len(all_questions)}문제)'
        ))
