# -*- coding: utf-8 -*-
"""실기 필답형 채점 엔진.

**채점은 LLM이 한다.** 채점 기준표(rubric)의 포인트마다 "사용자 답안이 이
내용을 담고 있는가"를 판정시킨다. 자유 채점이 아니라 기준표 대조이므로
결과가 비교적 일정하다.

한때 단답·빈칸을 문자열 비교로 채점했으나 걷어냈다. 모범답안이
"야생절멸(EW)"일 때 "야생절멸"만 쓴 정답을 0점 처리하는 사고가 났고,
이런 예외(동의어·표기 변형·괄호 부연·띄어쓰기)는 규칙으로 끝이 없다.
절약되는 비용은 세션당 1원 미만이라 정확도와 바꿀 가치가 없다.

계산형만 예외다. 최종 답 수치가 정확히 일치하면 규칙으로 만점을 준다
(LLM이 산수를 틀릴 여지를 없앤다). 어긋나면 계산 전용 LLM이 판단한다.

반환 형식은 어느 경로든 같다:
    {
      "score": 3.0,
      "max": 4.0,
      "points": [{"point": "...", "matched": true, "comment": "..."}],
      "summary": "빠진 항목: ...",
      "engine": "rule" | "llm" | "llm-calc",
    }
"""
import re
import unicodedata

from django.conf import settings

# 숫자 허용 오차 (상대)
NUM_TOLERANCE = 0.02

# 원문자·번호 기호 제거용
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩㉠㉡㉢㉣㉤ㄱㄴㄷㄹㅁ'


def normalize(s):
    """비교용 정규화: 공백·문장부호·번호기호 제거, 전각→반각, 소문자화."""
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', str(s))
    s = re.sub(rf'[{CIRCLED}]', ' ', s)
    s = re.sub(r'[\s\-_·,./()\[\]{}<>:;!?\'"「」『』]+', '', s)
    return s.lower().strip()


def extract_numbers(s):
    """문자열에서 수치를 뽑는다 (쉼표 제거, 지수 표기 일부 지원)."""
    if not s:
        return []
    s = str(s).replace(',', '')
    return [float(m) for m in re.findall(r'-?\d+(?:\.\d+)?', s)]


def final_answer_numbers(question):
    """계산형 모범답안에서 '최종 답'의 수치만 뽑는다.

    교재 풀이는 계산 과정을 모두 적어 두어(10,000 × 60% × 1.3 = 7,800 …)
    중간값까지 정답 수치로 잡으면 최종 답만 쓴 답안이 오답 처리된다.
    '답', '∴', '=' 뒤에 오는 값을 우선하고, 없으면 각 줄의 마지막 수치를 쓴다.
    """
    blob = ' \n'.join(list(question.answer_items or []) + [question.answer_text or ''])
    lines = [ln.strip() for ln in blob.split('\n') if ln.strip()]
    finals = []

    # 1) "답" 표지(② 답 / 답: / ∴)가 있으면 그 줄 이후만 최종 답으로 본다.
    #    교재는 "① 계산식 … ② 답 …" 구조라 표지 뒤가 결론이다.
    marker = re.compile(r'(②\s*답|(^|\s)답\s*[:：]|∴|답은)')
    take, marked = [], False
    for ln in lines:
        if marker.search(ln):
            marked = True
            after = marker.split(ln)[-1]
            nums = extract_numbers(after)
            take.extend(nums if nums else extract_numbers(ln)[-1:])
            continue
        if marked and re.match(r'^[•\-]', ln):     # 표지 뒤 이어지는 항목
            nums = extract_numbers(ln.split('=')[-1])
            if nums:
                take.append(nums[-1])
    if take:
        finals = take

    # 2) 표지가 없으면 등호가 있는 줄의 우변 마지막 값
    if not finals:
        for ln in lines:
            if '=' in ln:
                nums = extract_numbers(ln.split('=')[-1])
                if nums:
                    finals.append(nums[-1])

    # 3) 그래도 없으면 전체에서 마지막 수치
    if not finals:
        nums = extract_numbers(blob)
        if nums:
            finals = [nums[-1]]

    # 중복 제거 (순서 유지)
    seen, out = set(), []
    for n in finals:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def numbers_match(user, answer_numbers):
    """정답 수치가 사용자 답안에 모두 있는지 (상대오차 허용)."""
    if not answer_numbers:
        return None                      # 수치가 없으면 판정 불가
    u_nums = extract_numbers(user)
    if not u_nums:
        return False
    for a in answer_numbers:
        ok = any(abs(u - a) <= max(abs(a) * NUM_TOLERANCE, 1e-9) for u in u_nums)
        if not ok:
            return False
    return True


def build_rubric(question):
    """문항의 채점 기준표를 만든다. 저장된 rubric이 있으면 그것을 쓴다."""
    if question.rubric:
        return question.rubric
    items = list(question.answer_items or [])
    if not items:
        text = (question.answer_text or '').strip()
        return [{'point': text[:300], 'score': float(question.points)}]
    base = float(question.points) / len(items)
    return [{'point': it, 'score': round(base, 2)} for it in items]


# ---------------------------------------------------------------- 규칙 채점 (계산형만)

def grade_calc_by_rule(question, user_answer):
    """계산형에서 최종 답 수치가 전부 맞으면 만점을 준다.

    교재 풀이는 계산 과정을 통째로 적어 두어 "어디까지가 최종 답인지"를
    기계적으로 100% 가려내기 어렵다. 그래서 확실히 맞은 경우에만 여기서
    끝내고, 하나라도 어긋나면 None을 반환해 계산 전용 LLM이 판단하게 한다.
    """
    targets = final_answer_numbers(question)
    if not targets:
        return None
    u_nums = extract_numbers(user_answer)
    if not u_nums:
        return None
    hit = [a for a in targets
           if any(abs(u - a) <= max(abs(a) * NUM_TOLERANCE, 1e-9) for u in u_nums)]
    if len(hit) != len(targets):
        return None
    max_score = float(question.points)
    return {
        'score': max_score, 'max': max_score, 'engine': 'rule',
        'points': [{'point': f'{a:,g}', 'matched': True, 'comment': ''}
                   for a in targets],
        'summary': '정답입니다.',
    }


# ---------------------------------------------------------------- LLM 채점

GRADE_SYSTEM = (
    "당신은 국가기술자격 실기 필답형 채점위원이다.\n"
    "채점 기준표의 각 포인트에 대해, 수험자 답안이 그 내용을 담고 있는지만 판정한다.\n\n"
    "판정 원칙:\n"
    "- 표현이 달라도 의미가 같으면 인정한다 (동의어·줄임말·순서 바뀜 허용).\n"
    "- **괄호 안의 부연은 선택 사항이다.** 기준이 '야생절멸(EW)'이면 '야생절멸'만\n"
    "  써도 정답이고, 'EW'만 써도 정답이다. 한자·영문 병기도 마찬가지다.\n"
    "- 띄어쓰기·맞춤법 차이는 감점하지 않는다 ('매트이식'='매트 이식').\n"
    "- 단답형에서 정답 용어를 맞혔다면, 부연 설명이 없어도 인정한다.\n"
    "- 빈칸형은 각 빈칸의 값이 맞는지만 본다. 순서 표기(①②)는 무시한다.\n"
    "- 핵심 용어가 빠졌거나 뜻이 달라지면 인정하지 않는다.\n"
    "- 기준표에 없는 내용을 썼다고 감점하지 않는다.\n"
    "- 부분적으로만 맞으면 matched=false로 하되 comment에 무엇이 부족한지 적는다.\n"
    "- comment는 한 문장 이내로 간결하게, 존댓말로 쓴다.\n"
    "- 채점 기준표에 없는 내용을 지어내지 않는다.\n"
)


def _grade_prompt(question, user_answer, rubric):
    lines = [
        f"[문제] ({question.qtype}형, 배점 {question.points}점)",
        question.text.strip(),
        "",
        "[채점 기준표]",
    ]
    for i, r in enumerate(rubric, 1):
        lines.append(f"{i}. ({r.get('score', 0)}점) {r['point']}")
    if question.answer_text:
        lines += ["", "[모범답안 보충]", question.answer_text.strip()[:1500]]
    lines += ["", "[수험자 답안]", (user_answer or '').strip() or '(빈 답안)']
    return '\n'.join(lines)


CALC_SYSTEM = (
    "당신은 국가기술자격 실기 필답형 계산 문제 채점위원이다.\n\n"
    "채점 원칙:\n"
    "- 배점의 70%는 '최종 답이 맞았는가', 30%는 '풀이 과정이 타당한가'로 본다.\n"
    "- 최종 답이 맞으면 과정을 생략했더라도 최소 70%는 준다. 실제 시험에서\n"
    "  답이 맞으면 점수를 주기 때문이다.\n"
    "- 구하는 값이 여럿(예: 운반량과 성토량)이면 맞힌 개수에 비례해 배분한다.\n"
    "- 단위 누락은 감점하지 않는다. 반올림 차이(1% 이내)도 정답으로 본다.\n"
    "- 답이 틀렸어도 과정·공식이 옳으면 30% 범위에서 부분점수를 준다.\n"
    "- 채점 근거를 comment에 한 문장으로 적는다. 존댓말을 쓴다.\n"
)


def grade_calc_by_llm(question, user_answer, model=None):
    """계산형 전용 채점. 최종 답 정확성을 주 기준으로 본다."""
    from google import genai
    from pydantic import BaseModel, Field

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY 미설정')

    max_score = float(question.points)
    model_answer = (question.answer_text or '\n'.join(question.answer_items or ''))

    class CalcResult(BaseModel):
        answer_correct: bool = Field(description="최종 답이 모두 맞으면 true")
        partial_ratio: float = Field(
            description="0.0~1.0. 구하는 값이 여럿일 때 맞힌 비율. 전부 맞으면 1.0")
        process_ok: bool = Field(description="풀이 과정·공식이 타당하면 true")
        comment: str = Field(description="채점 근거 한 문장")

    prompt = (
        f"[문제] (배점 {max_score}점)\n{question.text.strip()}\n\n"
        f"[모범답안 / 풀이]\n{model_answer.strip()[:2000]}\n\n"
        f"[수험자 답안]\n{(user_answer or '').strip() or '(빈 답안)'}"
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or settings.GEMINI_ESSAY_GRADE_MODEL,
        contents=[CALC_SYSTEM, prompt],
        config={
            'response_mime_type': 'application/json',
            'response_schema': CalcResult,
            'temperature': 0,
        },
    )
    r = CalcResult.model_validate_json(response.text)

    ratio = max(0.0, min(1.0, r.partial_ratio if not r.answer_correct else 1.0))
    score = max_score * 0.7 * ratio
    if r.process_ok:
        score += max_score * 0.3 * (1.0 if r.answer_correct else 0.6)
    score = round(min(score, max_score), 2)

    return {
        'score': score, 'max': max_score, 'engine': 'llm-calc',
        'points': [
            {'point': '최종 답', 'matched': r.answer_correct,
             'comment': '' if r.answer_correct else f'맞힌 비율 {int(ratio * 100)}%'},
            {'point': '풀이 과정', 'matched': r.process_ok,
             'comment': '' if r.process_ok else '과정이 제시되지 않았거나 오류가 있습니다'},
        ],
        'summary': r.comment,
    }


def grade_by_llm(question, user_answer, model=None):
    """Gemini로 기준표 대조 채점을 수행한다."""
    from google import genai
    from pydantic import BaseModel, Field

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY 미설정')

    rubric = build_rubric(question)

    class PointResult(BaseModel):
        index: int = Field(description="채점 기준표 항목 번호 (1부터)")
        matched: bool = Field(description="수험자 답안이 이 항목을 담고 있으면 true")
        comment: str = Field(description="한 문장 이내 근거. 인정이면 빈 문자열도 가능")

    class GradeResult(BaseModel):
        points: list[PointResult]
        summary: str = Field(description="빠진 내용 위주의 총평 두 문장 이내")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or settings.GEMINI_ESSAY_GRADE_MODEL,
        contents=[GRADE_SYSTEM, _grade_prompt(question, user_answer, rubric)],
        config={
            'response_mime_type': 'application/json',
            'response_schema': GradeResult,
            'temperature': 0,
        },
    )
    parsed = GradeResult.model_validate_json(response.text)

    by_index = {p.index: p for p in parsed.points}
    results, got = [], 0.0
    all_matched = True
    for i, r in enumerate(rubric, 1):
        p = by_index.get(i)
        matched = bool(p and p.matched)
        if matched:
            got += float(r.get('score', 0))
        else:
            all_matched = False
        results.append({
            'point': r['point'],
            'matched': matched,
            'comment': (p.comment if p else '판정 없음'),
        })

    # 균등 배분에서 생기는 반올림 오차 보정 — 전부 맞았으면 만점
    if all_matched:
        got = float(question.points)

    return {
        'score': round(min(got, float(question.points)), 2),
        'max': float(question.points),
        'engine': 'llm',
        'points': results,
        'summary': parsed.summary,
    }


# ---------------------------------------------------------------- 진입점

def grade_answer(question, user_answer, model=None):
    """문항 하나를 채점한다.

    빈 답안은 호출 없이 0점, 계산형은 수치가 다 맞으면 규칙으로 만점,
    나머지는 모두 LLM이 기준표와 대조해 채점한다.
    """
    if not (user_answer or '').strip():
        rubric = build_rubric(question)
        return {
            'score': 0.0, 'max': float(question.points), 'engine': 'rule',
            'points': [{'point': r['point'], 'matched': False, 'comment': '답안 없음'}
                       for r in rubric],
            'summary': '답안이 비어 있습니다.',
        }
    if question.qtype == '계산':
        result = grade_calc_by_rule(question, user_answer)
        if result is not None:
            return result
        return grade_calc_by_llm(question, user_answer, model=model)
    return grade_by_llm(question, user_answer, model=model)


def grade_session(session, model=None):
    """세션의 모든 답안을 채점하고 총점을 저장한다."""
    from django.utils import timezone

    total = 0.0
    for att in session.attempts.select_related('question'):
        try:
            res = grade_answer(att.question, att.answer_text, model=model)
        except Exception as e:
            res = {
                'score': 0.0, 'max': float(att.question.points), 'engine': 'error',
                'points': [], 'summary': f'채점 실패: {e}',
            }
        att.ai_score = res['score']
        att.feedback = res
        att.graded_at = timezone.now()
        att.save(update_fields=['ai_score', 'feedback', 'graded_at'])
        total += att.score

    session.score = round(total, 2)
    session.status = 'done'
    session.submitted_at = session.submitted_at or timezone.now()
    session.save(update_fields=['score', 'status', 'submitted_at'])
    return session.score
