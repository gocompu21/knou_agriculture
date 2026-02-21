"""
Gemini API를 사용하여 기사시험 기출문제 해설을 생성하는 커맨드.

사용법:
    python manage.py generate_gisa_explanations
    python manage.py generate_gisa_explanations --cert 식물보호 --subject 식물병리학
    python manage.py generate_gisa_explanations --year 2011 --force
    python manage.py generate_gisa_explanations --dry-run
"""
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from google import genai
from pydantic import BaseModel, Field

from gisa.models import Certification, GisaQuestion, GisaSubject

CIRCLE_NUMBERS = {'1': '①', '2': '②', '3': '③', '4': '④'}


class QuestionExplanation(BaseModel):
    explanation: str = Field(description="정답에 대한 설명 (정답설명)")
    choice_1_exp: str = Field(description="보기 ①에 대한 해설")
    choice_2_exp: str = Field(description="보기 ②에 대한 해설")
    choice_3_exp: str = Field(description="보기 ③에 대한 해설")
    choice_4_exp: str = Field(description="보기 ④에 대한 해설")


def build_prompt(question):
    answer_circle = CIRCLE_NUMBERS.get(question.answer, '?')
    cert = question.exam.certification
    return (
        f"당신은 {cert.name}{cert.category} 시험 전문가이다.\n"
        f"다음은 {cert.name}{cert.category} {question.subject.name} 기출문제이다.\n\n"
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

    # 정답 선지에는 정답설명을 넣음
    if question.answer in ('1', '2', '3', '4'):
        setattr(question, f'choice_{question.answer}_exp', result.explanation)

    question.save(update_fields=[
        'explanation',
        'choice_1_exp', 'choice_2_exp',
        'choice_3_exp', 'choice_4_exp',
    ])


class Command(BaseCommand):
    help = 'Gemini API를 사용하여 기사시험 기출문제 해설을 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--cert', type=str, help='자격증명으로 필터링 (예: 식물보호)')
        parser.add_argument('--subject', type=str, help='과목명으로 필터링 (예: 식물병리학)')
        parser.add_argument('--year', type=int, help='출제연도로 필터링 (예: 2011)')
        parser.add_argument('--round', type=int, help='회차로 필터링 (예: 1)')
        parser.add_argument('--force', action='store_true', help='이미 해설이 있는 문제도 덮어쓰기')
        parser.add_argument('--delay', type=float, default=0.5, help='API 호출 간 대기 시간(초) (기본: 0.5)')
        parser.add_argument('--model', type=str, default='gemini-3-flash-preview', help='Gemini 모델 (기본: gemini-3-flash-preview)')
        parser.add_argument('--dry-run', action='store_true', help='실제 API 호출 없이 대상 문제만 확인')

    def handle(self, *args, **options):
        qs = GisaQuestion.objects.select_related('exam__certification', 'subject').all()

        if options['cert']:
            certs = Certification.objects.filter(name=options['cert'])
            if not certs.exists():
                raise CommandError(f"자격증을 찾을 수 없습니다: {options['cert']}")
            qs = qs.filter(exam__certification__in=certs)

        if options['subject']:
            subjects = GisaSubject.objects.filter(name=options['subject'])
            if not subjects.exists():
                raise CommandError(f"과목을 찾을 수 없습니다: {options['subject']}")
            qs = qs.filter(subject__in=subjects)

        if options['year']:
            qs = qs.filter(exam__year=options['year'])

        if options['round']:
            qs = qs.filter(exam__round=options['round'])

        if not options['force']:
            qs = qs.filter(explanation='')

        qs = qs.order_by('exam__certification__name', 'exam__year', 'subject__order', 'number')
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('생성할 문제가 없습니다.'))
            return

        self.stdout.write(f'대상 문제: {total}개 (모델: {options["model"]})\n')

        if options['dry_run']:
            for q in qs:
                cert = q.exam.certification
                self.stdout.write(f'  [{cert.name}{cert.category}] {q.exam.year}년 {q.subject.name} {q.number}번')
            return

        client = create_client()
        success = 0
        failed = 0

        for i, question in enumerate(qs, 1):
            if question.answer in ('0', ''):
                self.stdout.write(f'[{i}/{total}] {question} ... ' + self.style.WARNING('정답 미확인 - 건너뜀'))
                continue

            cert = question.exam.certification
            label = f'{cert.name}{cert.category} {question.exam.year}년 {question.subject.name} {question.number}번'
            self.stdout.write(f'[{i}/{total}] {label} ... ', ending='')

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
