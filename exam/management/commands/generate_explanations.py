import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from google import genai
from pydantic import BaseModel, Field

from exam.models import Question
from main.models import Subject

CIRCLE_NUMBERS = {'1': '①', '2': '②', '3': '③', '4': '④'}


class QuestionExplanation(BaseModel):
    explanation: str = Field(description="정답에 대한 설명 (정답설명)")
    choice_1_exp: str = Field(description="보기 ①에 대한 해설")
    choice_2_exp: str = Field(description="보기 ②에 대한 해설")
    choice_3_exp: str = Field(description="보기 ③에 대한 해설")
    choice_4_exp: str = Field(description="보기 ④에 대한 해설")


def build_prompt(question):
    # 복수 정답 지원: "1,2" → "①②"
    answer_parts = [a.strip() for a in question.answer.split(',')]
    answer_circle = ''.join(CIRCLE_NUMBERS.get(a, '?') for a in answer_parts)
    return (
        f"당신은 한국방송통신대학교 교수이다.\n"
        f"다음은 한국방송통신대학교 {question.subject.name} 기말고사문제이다.\n\n"
        f"{question.number}. {question.text}\n"
        f"① {question.choice_1}\n"
        f"② {question.choice_2}\n"
        f"③ {question.choice_3}\n"
        f"④ {question.choice_4}\n\n"
        f"정답은 {answer_circle}\n\n"
        f"해당 문제에 대해 [정답설명]과 [선지별 해설]을 해줘.\n"
        f"공부팁이나 인사말 기타 내용은 넣지마"
    )


def create_client():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return genai.Client(api_key=api_key)


def generate_explanation(client, question, model_name):
    prompt = build_prompt(question)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": QuestionExplanation,
        },
    )
    return QuestionExplanation.model_validate_json(response.text)


def save_explanation(question, result):
    question.explanation = result.explanation
    question.choice_1_exp = result.choice_1_exp
    question.choice_2_exp = result.choice_2_exp
    question.choice_3_exp = result.choice_3_exp
    question.choice_4_exp = result.choice_4_exp

    # 정답 선지에는 정답설명을 넣음 (복수 정답 지원)
    answer_parts = [a.strip() for a in question.answer.split(',')]
    for a in answer_parts:
        if a in ('1', '2', '3', '4'):
            setattr(question, f'choice_{a}_exp', result.explanation)

    question.save(update_fields=[
        'explanation',
        'choice_1_exp', 'choice_2_exp',
        'choice_3_exp', 'choice_4_exp',
    ])


class Command(BaseCommand):
    help = 'Gemini API를 사용하여 기출문제 해설을 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--subject', type=str, help='과목명으로 필터링 (예: 토양학)')
        parser.add_argument('--grade', type=int, help='학년으로 필터링 (예: 3)')
        parser.add_argument('--year', type=int, help='출제연도로 필터링 (예: 2019)')
        parser.add_argument('--force', action='store_true', help='이미 해설이 있는 문제도 덮어쓰기')
        parser.add_argument('--delay', type=float, default=0.5, help='API 호출 간 대기 시간(초) (기본: 0.5)')
        parser.add_argument('--model', type=str, default='gemini-3-flash-preview', help='Gemini 모델 (기본: gemini-3-flash-preview)')
        parser.add_argument('--dry-run', action='store_true', help='실제 API 호출 없이 대상 문제만 확인')

    def handle(self, *args, **options):
        qs = Question.objects.select_related('subject').all()

        if options['subject']:
            subject_qs = Subject.objects.filter(name=options['subject'])
            if options['grade']:
                subject_qs = subject_qs.filter(grade=options['grade'])
            if not subject_qs.exists():
                raise CommandError(f"과목을 찾을 수 없습니다: {options['subject']}")
            if subject_qs.count() > 1:
                names = ', '.join(str(s) for s in subject_qs)
                raise CommandError(f"동일 과목명이 {subject_qs.count()}개 있습니다. --grade로 학년을 지정하세요: {names}")
            qs = qs.filter(subject=subject_qs.first())

        if options['year']:
            qs = qs.filter(year=options['year'])

        if not options['force']:
            qs = qs.filter(explanation='')

        qs = qs.order_by('subject__name', 'year', 'number')
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('생성할 문제가 없습니다.'))
            return

        self.stdout.write(f'대상 문제: {total}개 (모델: {options["model"]})\n')

        if options['dry_run']:
            for q in qs:
                self.stdout.write(f'  {q}')
            return

        client = create_client()
        success = 0
        failed = 0

        for i, question in enumerate(qs, 1):
            if question.answer in ('0', ''):
                self.stdout.write(f'[{i}/{total}] {question} ... ' + self.style.WARNING('정답 미확인 - 건너뜀'))
                continue

            self.stdout.write(f'[{i}/{total}] {question} ... ', ending='')

            try:
                result = generate_explanation(client, question, options['model'])
                save_explanation(question, result)
                success += 1
                self.stdout.write(self.style.SUCCESS('OK'))
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'실패: {e}'))

            if i < total and options['delay'] > 0:
                time.sleep(options['delay'])

        self.stdout.write(self.style.SUCCESS(
            f'\n완료: 성공 {success}개, 실패 {failed}개 (총 {total}개)'
        ))
