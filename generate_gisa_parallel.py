"""
기사시험 해설을 병렬로 생성하는 스크립트.

사용법:
    python generate_gisa_parallel.py --year 2012 --round 1 --model gemini-3-pro-preview --workers 50
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.conf import settings
from google import genai
from pydantic import BaseModel, Field

from gisa.models import GisaQuestion

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


def process_question(client, question, model_name):
    prompt = build_prompt(question)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": QuestionExplanation,
        },
    )
    result = QuestionExplanation.model_validate_json(response.text)

    question.explanation = result.explanation
    question.choice_1_exp = result.choice_1_exp
    question.choice_2_exp = result.choice_2_exp
    question.choice_3_exp = result.choice_3_exp
    question.choice_4_exp = result.choice_4_exp

    if question.answer in ('1', '2', '3', '4'):
        setattr(question, f'choice_{question.answer}_exp', result.explanation)

    question.save(update_fields=[
        'explanation',
        'choice_1_exp', 'choice_2_exp',
        'choice_3_exp', 'choice_4_exp',
    ])
    return question.number


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cert', type=str, default='식물보호')
    parser.add_argument('--year', type=int)
    parser.add_argument('--round', type=int)
    parser.add_argument('--model', type=str, default='gemini-3-flash-preview')
    parser.add_argument('--workers', type=int, default=50)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    qs = GisaQuestion.objects.select_related(
        'exam__certification', 'subject'
    ).filter(
        exam__certification__name=args.cert,
    )
    if args.year:
        qs = qs.filter(exam__year=args.year)
    if args.round:
        qs = qs.filter(exam__round=args.round)
    qs = qs.order_by('exam__year', 'subject__order', 'number')

    if not args.force:
        qs = qs.filter(explanation='')

    questions = list(qs)
    total = len(questions)

    if total == 0:
        print('생성할 문제가 없습니다.')
        return

    print(f'대상: {args.cert} {args.year}년 {args.round}회 - {total}문제 (모델: {args.model}, 워커: {args.workers})')

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    success = 0
    failed = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_question, client, q, args.model): q
            for q in questions
        }
        for future in as_completed(futures):
            q = futures[future]
            try:
                num = future.result()
                success += 1
                print(f'  [{success + failed}/{total}] {q.number}번 ({q.subject.name}) ... OK')
            except Exception as e:
                failed += 1
                print(f'  [{success + failed}/{total}] {q.number}번 ({q.subject.name}) ... 실패: {e}')

    elapsed = time.time() - start
    print(f'\n완료: 성공 {success}개, 실패 {failed}개 (총 {total}개, {elapsed:.1f}초)')


if __name__ == '__main__':
    main()
