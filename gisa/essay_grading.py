# -*- coding: utf-8 -*-
"""실기 필답형 채점 엔진.

**채점은 LLM이 한다.** 채점 기준표(rubric)의 포인트마다 "사용자 답안이 이
내용을 담고 있는가"를 판정시킨다. 자유 채점이 아니라 기준표 대조이므로
결과가 비교적 일정하다.

한때 단답·빈칸을 문자열 비교로 채점했으나 걷어냈다. 모범답안이
"야생절멸(EW)"일 때 "야생절멸"만 쓴 정답을 0점 처리하는 사고가 났고,
이런 예외(동의어·표기 변형·괄호 부연·띄어쓰기)는 규칙으로 끝이 없다.
절약되는 비용은 세션당 1원 미만이라 정확도와 바꿀 가치가 없다.

계산형도 LLM이 채점한다(계산 전용 프롬프트). 예전에는 최종 답 수치가
모두 맞으면 규칙으로 만점을 주었는데, 수치만 보고 **단위를 보지 못해**
42.67m²/hr(정답 m³/hr)에 만점을 주었다. 3.2 × 0.8 을 적은 답안이 허용 오차
2% 때문에 2.56 과 일치한 것으로 잡히기도 했다. 그래서 걷어냈다.

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

from django.conf import settings

from .essay_examinfo import exam_info


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


# ------------------------------------------------- 'N가지' 를 요구한 문항

_NUM_WORD = {'하나': 1, '한': 1, '둘': 2, '두': 2, '셋': 3, '세': 3, '넷': 4, '네': 4,
             '다섯': 5, '여섯': 6, '일곱': 7, '여덟': 8, '아홉': 9, '열': 10}
# 앞이 한글이면 낱말 꼬리다 — '다양한 가지'의 '한'을 세면 안 된다
_ASK_RE = re.compile(
    r'(\d+|(?<![가-힣])(?:하나|한|둘|두|셋|세|넷|네|다섯|여섯|일곱|여덟|아홉|열))\s*가지')


def asked_count(text):
    """문제문이 요구한 개수. '3가지'·'두 가지' 하나만 있을 때 그 수를 돌려준다.

    **하나만 있을 때로 못박는 까닭**이 있다. 'A를 2가지와 B를 3가지 쓰시오'
    처럼 묶음이 둘이면 기준표가 길어도 보기 목록이 아니라 다섯을 다 써야
    하는 문항이다. '각각 …씩'도 대상마다 따로 요구하는 것이라 뺀다.
    """
    t = text or ''
    if '각각' in t or '씩' in t:
        return None
    got = [m.group(1) for m in _ASK_RE.finditer(t)]
    if len(got) != 1:
        return None
    return int(got[0]) if got[0].isdigit() else _NUM_WORD[got[0]]


def _pick_group(question, rubric, parsed):
    """모델이 '이 가운데 N가지만 쓰면 된다'고 본 보기 묶음을 검증해 돌려준다.

    돌려주는 것은 (요구 개수, 항목 번호 집합) 이거나 None. 모델 말을 그대로
    믿지 않고 **문제문에 그 개수가 실제로 적혀 있는지** 대조한다 — 지어낸
    개수로 만점을 주면 안 된다.
    """
    need = int(getattr(parsed, 'pick_count', 0) or 0)
    idx = {int(i) for i in (getattr(parsed, 'pick_indices', None) or [])
           if isinstance(i, (int, float)) and 1 <= int(i) <= len(rubric)}
    if need < 1 or len(idx) <= need:
        return None
    if need != asked_count(question.text):
        return None
    return need, idx


def _sum_points(question, rubric, results, parsed):
    """항목 점수를 합쳐 (총점, 만점 여부)를 돌려준다.

    보통은 그냥 더한다. 보기 목록 문항('5가지 가운데 3가지를 쓰시오')이면
    **보기 묶음의 배점 전부를 요구한 개수로 나눠** 준다 — 다섯 항목에 1점씩
    붙어 있어도 셋만 요구했으면 하나가 1.67점이다. 그래야 셋을 맞힌 답안이
    3점이 아니라 만점이 된다.
    """
    pick = _pick_group(question, rubric, parsed)
    if not pick:
        got = sum(x['score'] for x in results)
        return got, all(x['score'] >= x['max'] - 1e-9 for x in results)

    need, idx = pick
    group = [results[i - 1] for i in sorted(idx)]
    rest = [x for j, x in enumerate(results, 1) if j not in idx]
    pool = sum(x['max'] for x in group)
    ratios = sorted(((x['score'] / x['max']) if x['max'] else 0.0) for x in group)
    got = sum(x['score'] for x in rest) + pool * sum(ratios[::-1][:need]) / need

    # 요구한 개수를 채웠으면 못 쓴 보기는 '다른 정답'이지 빠뜨린 것이 아니다.
    # 화면이 ✕ 대신 따로 그리도록 표시해 둔다.
    met = sum(1 for x in group if x['max'] and x['score'] >= x['max'] - 1e-9) >= need
    if met:
        for x in group:
            if x['score'] < x['max'] - 1e-9:
                x['alt'] = True
                x['comment'] = f'다른 정답입니다 — {need}가지를 이미 채웠으므로 쓰지 않아도 됩니다.'
    return got, met and all(x['score'] >= x['max'] - 1e-9 for x in rest)


# ---------------------------------------------------------------- LLM 채점

GRADE_SYSTEM = (
    "당신은 국가기술자격 **기사·산업기사 실기 필답형** 채점위원이다.\n"
    "어느 종목의 어느 과목인지는 [시험] 줄에 적혀 있다. 그 분야의 관용 표기와\n"
    "약어를 아는 채점위원으로서 판정한다.\n\n"
    "**채점 기준표의 항목마다 배점이 적혀 있다. 그 범위 안에서 점수를 매긴다.**\n"
    "- matched: 그 항목을 온전히 담았으면 true\n"
    "- score: 그 항목에 주는 점수. 0 이상 배점 이하로, 아래를 기준 삼는다.\n"
    "    배점 전부      온전히 담았다 (matched=true 와 함께)\n"
    "    배점의 50~90%  핵심은 맞으나 일부가 빠졌거나 설명이 얕다\n"
    "    배점의 20~40%  방향은 맞으나 핵심 용어가 빠져 답으로 보기 어렵다\n"
    "    0              전혀 담기지 않았거나 틀렸다\n"
    "  예: 배점 2.5점짜리 항목을 반만 맞혔으면 score=1.25 로 적는다.\n"
    "  **실제 필답 채점에서도 반만 쓴 답에 반점을 주므로 0점 아니면 만점으로\n"
    "  가르지 않는다.** 0.5점 단위로 끊어도 좋다.\n"
    "  다만 **단답·빈칸은 맞거나 틀리거나 둘뿐이다** — 배점 전부 또는 0 만 준다.\n\n"
    "판정 원칙:\n"
    "- 표현이 달라도 의미가 같으면 인정한다 (동의어·줄임말·순서 바뀜 허용).\n"
    "- **괄호 안의 부연은 선택 사항이다.** 기준이 '야생절멸(EW)'이면 '야생절멸'만\n"
    "  써도 정답이고, 'EW'만 써도 정답이다. 한자·영문 병기도 마찬가지다.\n"
    "- 띄어쓰기·맞춤법 차이는 감점하지 않는다 ('매트이식'='매트 이식').\n"
    "- 단답형에서 정답 용어를 맞혔다면, 부연 설명이 없어도 인정한다.\n"
    "- 빈칸형은 각 빈칸의 값이 맞는지만 본다. 순서 표기(①②)는 무시한다.\n"
    "- 핵심 용어가 빠졌거나 뜻이 달라지면 인정하지 않는다.\n"
    "- 기준표에 없는 내용을 썼다고 감점하지 않는다.\n"
    "- 부분적으로만 맞으면 matched=false 로 두되 **score 에 부분 점수를 적고**\n"
    "  comment 에 무엇이 부족한지 쓴다.\n"
    "- comment는 한 문장 이내로 간결하게, 존댓말로 쓴다.\n"
    "- 채점 기준표에 없는 내용을 지어내지 않는다.\n\n"
    "**'N가지를 쓰시오' — 기준표가 보기 목록일 때 (pick_count·pick_indices)**\n"
    "기준표 항목 수가 문제가 요구한 개수보다 많으면, 그 항목들은 대개 '인정되는\n"
    "답을 모아 둔 목록'이다. 답안이 그 가운데 요구한 개수만큼 맞혔으면 만점이며,\n"
    "쓰지 않은 나머지는 빠뜨린 것이 아니다.\n"
    "- pick_count: 문제문이 요구한 개수('3가지'의 3). 그런 목록이 아니면 0.\n"
    "- pick_indices: 서로 바꿔 써도 되는 보기에 해당하는 기준표 항목 번호.\n"
    "- **반드시 써야 하는 항목은 pick_indices 에 넣지 않는다.** '개념을 쓰고 목적\n"
    "  3가지를 설명하시오'라면 개념 항목은 필수이고 목적 항목만 보기다.\n"
    "- 'A를 2가지, B를 3가지'처럼 묶음이 둘이거나 '각각 1가지씩'처럼 대상마다\n"
    "  따로 요구하면 보기 목록이 아니다 — pick_count=0 으로 둔다.\n"
    "- 보기 항목도 판정은 그대로 한다. 답안에 없으면 matched=false, score=0 이다.\n"
    "  몇 개를 채웠는지 세어 점수로 바꾸는 일은 채점 프로그램이 한다.\n"
)

# 첨삭 — 채점위원이 빨간 색연필로 답안지에 표시하듯. 퀴즈 화면이 답안 글자 위에
# 겹쳐 그리므로 **답안에서 글자 그대로 옮긴 구절(quote)** 이 닻이다. 점수에는 쓰지 않는다.
MARK_RULES = (
    "\n첨삭(marks·missing) — 채점위원이 빨간 색연필로 답안지에 표시하듯 적는다.\n"
    "- quote 는 [수험자 답안]에서 **글자 그대로 복사한** 구절이어야 한다. 고쳐 쓰거나\n"
    "  요약하지 않는다. 낱말이나 짧은 구(20자 이내)를 고른다.\n"
    "- kind: wrong = 틀린 내용(줄을 긋고 X), weak = 방향은 맞으나 부족·모호(물결 밑줄),\n"
    "  good = 점수를 받은 핵심 용어(밑줄과 ✓).\n"
    "- note 는 그 옆 여백에 손으로 적는 짧은 첨삭, 12자 이내 명사구다\n"
    "  (예: '광보상점 아님', '근거 부족', '단위 누락', '정답'). good 은 비워도 된다.\n"
    "- 표시는 모두 합쳐 6개 이내로, 틀린 곳부터 고른다.\n"
    "- missing: 답안에 아예 없는 핵심 내용을 12자 이내로 적는다. 없으면 빈 목록.\n"
)


def _clean_marks(marks, missing, user_answer):
    """모델이 준 첨삭을 다듬는다 — 답안에서 찾을 수 없는 구절은 버리고 개수를 자른다.

    띄어쓰기만 다른 구절은 살린다(화면이 공백을 무시하고 찾는다). 글자가 다르면
    줄을 그을 자리가 없으므로 버린다.
    """
    ans = user_answer or ''
    squash = re.sub(r'\s+', '', ans)
    out = []
    for m in marks or []:
        quote = (getattr(m, 'quote', '') or '').strip()
        kind = (getattr(m, 'kind', '') or '').strip()
        if not quote or kind not in ('wrong', 'weak', 'good'):
            continue
        if quote not in ans and re.sub(r'\s+', '', quote) not in squash:
            continue
        out.append({'quote': quote[:60], 'kind': kind,
                    'note': (getattr(m, 'note', '') or '').strip()[:20]})
    miss = [str(x).strip()[:20] for x in (missing or []) if str(x).strip()]
    return out[:6], miss[:3]


def _exam_header(question):
    """어느 시험의 문항인지 한 줄로 알린다.

    "국가기술자격 실기 필답형"이라고만 하면 모델이 어느 분야인지 모른 채
    용어를 판정한다. 종목·과목을 알려 주면 그 분야의 관용 표기와 약어를
    제대로 본다 — '엽면적지수'와 'LAI', '무황산근'과 '황산근이 없는 비료'가
    같은 말인지는 식물보호 실무를 아는 채점위원이라야 가른다.
    """
    cert = question.certification.name
    info = exam_info(cert) or {}
    subject = info.get('practical_subject')
    bits = [f"{cert} 실기 필답형"]
    if subject:
        bits.append(f"과목 「{subject}」")
    if info.get('essay_points'):
        bits.append(f"필답 {info['essay_points']}점 만점")
    return "[시험] " + " · ".join(bits)


def _grade_prompt(question, user_answer, rubric):
    lines = [
        _exam_header(question),
        "",
        f"[문제] ({question.qtype}형, 배점 {question.points}점)",
        question.text.strip(),
        "",
        "[채점 기준표]",
    ]
    for i, r in enumerate(rubric, 1):
        lines.append(f"{i}. ({r.get('score', 0)}점) {r['point']}")
    need = asked_count(question.text)
    if need and len(rubric) > need:
        lines += ["", f"[유의] 문제는 {need}가지를 요구했는데 기준표에는 "
                      f"{len(rubric)}개가 적혀 있다. 기준표가 '인정되는 답을 모아 둔 "
                      f"목록'이라면 pick_count={need} 로 두고 그 보기들의 번호를 "
                      f"pick_indices 에 적는다. 정의·개념처럼 반드시 써야 하는 "
                      f"항목은 빼고 적는다."]
    if question.answer_text:
        lines += ["", "[모범답안 보충]", question.answer_text.strip()[:1500]]
    lines += ["", "[수험자 답안]", (user_answer or '').strip() or '(빈 답안)']
    return '\n'.join(lines)


CALC_SYSTEM = (
    "당신은 국가기술자격 **기사·산업기사 실기 필답형** 계산 문제 채점위원이다.\n"
    "어느 종목의 어느 과목인지는 [시험] 줄에 적혀 있다.\n\n"
    "**문제의 배점이 적혀 있다. 그 범위 안에서 점수를 매긴다.**\n\n"
    "채점 원칙:\n"
    "- 배점의 70%는 '최종 답이 맞았는가', 30%는 '풀이 과정이 타당한가'로 본다.\n"
    "- 최종 답이 맞으면 과정을 생략했더라도 최소 70%는 준다. 실제 시험에서\n"
    "  답이 맞으면 점수를 주기 때문이다.\n"
    "- 구하는 값이 여럿(예: 운반량과 성토량)이면 맞힌 개수에 비례해 배분한다.\n"
    "- 반올림 차이(1% 이내)는 정답으로 본다.\n"
    "- **단위를 반드시 확인한다.** 최종 답의 단위가 모범답안과 다르면(예: m³/hr 를\n"
    "  m²/hr·m2/hr 로, m³ 를 m² 로, 분을 초로) 수치가 맞아도 최종 답은 틀린 것이다 —\n"
    "  answer_correct=false, answer_score=0. marks 에 그 단위를 wrong 으로 짚고\n"
    "  note 에 '단위 오류'라고 적는다. 과정이 옳으면 process_score 는 줄 수 있다.\n"
    "- 단위를 아예 안 쓴 경우: 문제가 구할 단위를 지정했으면(예: '작업량(m³/hr)을\n"
    "  구하시오') 생략해도 정답이다. 지정하지 않았으면 단위 없는 답은 틀린 것이다\n"
    "  (실기 답안 작성 유의사항).\n"
    "- m3·m^3 처럼 위첨자를 못 쓴 표기는 m³ 와 같은 단위로 본다. m2 는 m² 다.\n"
    "- 답이 틀렸어도 과정·공식이 옳으면 30% 범위에서 부분점수를 준다.\n"
    "- answer_score 와 process_score 에 각각 준 점수를 적는다. 둘을 더한 것이\n"
    "  이 문항의 점수이며 배점을 넘지 않아야 한다.\n"
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

    class Mark(BaseModel):
        quote: str = Field(description="수험자 답안에서 글자 그대로 복사한 구절")
        kind: str = Field(description="wrong | weak | good")
        note: str = Field(description="여백 첨삭, 12자 이내")

    class CalcResult(BaseModel):
        answer_correct: bool = Field(description="최종 답이 모두 맞으면 true")
        answer_score: float = Field(
            description=f"최종 답에 주는 점수. 0 이상 {max_score * 0.7:g}점 이하")
        process_ok: bool = Field(description="풀이 과정·공식이 타당하면 true")
        process_score: float = Field(
            description=f"풀이 과정에 주는 점수. 0 이상 {max_score * 0.3:g}점 이하")
        comment: str = Field(description="채점 근거 한 문장")
        marks: list[Mark] = Field(default_factory=list, description="답안 위 첨삭, 6개 이내")
        missing: list[str] = Field(default_factory=list, description="빠진 핵심, 12자 이내")

    prompt = (
        f"{_exam_header(question)}\n\n"
        f"[문제] (배점 {max_score}점)\n{question.text.strip()}\n\n"
        f"[모범답안 / 풀이]\n{model_answer.strip()[:2000]}\n\n"
        f"[수험자 답안]\n{(user_answer or '').strip() or '(빈 답안)'}"
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or settings.GEMINI_ESSAY_GRADE_MODEL,
        contents=[CALC_SYSTEM + MARK_RULES, prompt],
        config={
            'response_mime_type': 'application/json',
            'response_schema': CalcResult,
            'temperature': 0,
        },
    )
    r = CalcResult.model_validate_json(response.text)

    # 점수는 모델이 매긴 것을 쓰되, 70/30 상한을 넘지 않게 자른다
    a_cap, p_cap = max_score * 0.7, max_score * 0.3
    a_got = a_cap if (r.answer_correct and r.answer_score <= 0) \
        else max(0.0, min(a_cap, float(r.answer_score)))
    p_got = max(0.0, min(p_cap, float(r.process_score)))
    score = round(min(a_got + p_got, max_score), 2)
    marks, missing = _clean_marks(r.marks, r.missing, user_answer)

    return {
        'score': score, 'max': max_score, 'engine': 'llm-calc',
        'points': [
            {'point': '최종 답', 'matched': r.answer_correct,
             'score': round(a_got, 2), 'max': round(a_cap, 2),
             'comment': '' if r.answer_correct else '최종 답이 모범답안과 다릅니다'},
            {'point': '풀이 과정', 'matched': r.process_ok,
             'score': round(p_got, 2), 'max': round(p_cap, 2),
             'comment': '' if r.process_ok else '과정이 제시되지 않았거나 오류가 있습니다'},
        ],
        'summary': r.comment,
        'marks': marks, 'missing': missing,
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
        matched: bool = Field(description="수험자 답안이 이 항목을 온전히 담고 있으면 true")
        score: float = Field(
            description="이 항목에 주는 점수. 0 이상 그 항목 배점 이하. "
                        "온전하면 배점 전부, 반쯤 맞으면 절반 식으로 매긴다")
        comment: str = Field(description="한 문장 이내 근거. 인정이면 빈 문자열도 가능")

    class Mark(BaseModel):
        quote: str = Field(description="수험자 답안에서 글자 그대로 복사한 구절")
        kind: str = Field(description="wrong | weak | good")
        note: str = Field(description="여백 첨삭, 12자 이내")

    class GradeResult(BaseModel):
        points: list[PointResult]
        summary: str = Field(description="빠진 내용 위주의 총평 두 문장 이내")
        marks: list[Mark] = Field(default_factory=list, description="답안 위 첨삭, 6개 이내")
        missing: list[str] = Field(default_factory=list, description="빠진 핵심, 12자 이내")
        pick_count: int = Field(
            default=0,
            description="기준표가 '이 가운데 N가지만 쓰면 되는' 보기 목록이면 "
                        "문제가 요구한 개수 N. 아니면 0")
        pick_indices: list[int] = Field(
            default_factory=list,
            description="서로 바꿔 써도 되는 보기에 해당하는 기준표 항목 번호. "
                        "반드시 써야 하는 항목은 넣지 않는다")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model or settings.GEMINI_ESSAY_GRADE_MODEL,
        contents=[GRADE_SYSTEM + MARK_RULES, _grade_prompt(question, user_answer, rubric)],
        config={
            'response_mime_type': 'application/json',
            'response_schema': GradeResult,
            'temperature': 0,
        },
    )
    parsed = GradeResult.model_validate_json(response.text)

    # 점수는 **모델이 매긴 것을 그대로 쓴다.** 코드가 하는 일은 두 가지뿐이다 —
    # 항목 배점을 넘거나 음수인 값을 잘라 내고, 합산한다. 합계까지 모델에게
    # 맡기지 않는 까닭은 채점 판단과 달리 덧셈은 틀릴 이유가 없기 때문이다.
    by_index = {p.index: p for p in parsed.points}
    results = []
    for i, r in enumerate(rubric, 1):
        p = by_index.get(i)
        matched = bool(p and p.matched)
        cap = float(r.get('score', 0))
        if p is None:
            given = 0.0
        elif matched and p.score <= 0:
            # 인정해 놓고 점수를 안 준 경우 — 판정을 따른다
            given = cap
        else:
            given = max(0.0, min(cap, float(p.score)))
        results.append({
            'point': r['point'],
            'matched': matched,
            'score': round(given, 2),
            'max': round(cap, 2),
            'comment': (p.comment if p else '판정 없음'),
        })

    got, all_matched = _sum_points(question, rubric, results, parsed)

    # 균등 배분에서 생기는 반올림 오차 보정 — 전부 맞았으면 만점
    if all_matched:
        got = float(question.points)
    marks, missing = _clean_marks(parsed.marks, parsed.missing, user_answer)
    if got >= float(question.points) - 1e-9:
        missing = []   # 만점인데 '빠짐'이 적히면 무엇이 틀렸나 찾게 된다

    return {
        'score': round(min(got, float(question.points)), 2),
        'max': float(question.points),
        'engine': 'llm',
        'points': results,
        'summary': parsed.summary,
        'marks': marks, 'missing': missing,
    }


# ---------------------------------------------------------------- 진입점

def grade_answer(question, user_answer, model=None):
    """문항 하나를 채점한다.

    빈 답안은 호출 없이 0점, 계산형은 계산 전용 LLM, 나머지는 LLM이
    기준표와 대조해 채점한다.
    """
    if not (user_answer or '').strip():
        rubric = build_rubric(question)
        return {
            'score': 0.0, 'max': float(question.points), 'engine': 'rule',
            'points': [{'point': r['point'], 'matched': False, 'score': 0.0,
                        'max': float(r.get('score', 0)), 'comment': '답안 없음'}
                       for r in rubric],
            'summary': '답안이 비어 있습니다.',
        }
    if question.qtype == '계산':
        return grade_calc_by_llm(question, user_answer, model=model)
    return grade_by_llm(question, user_answer, model=model)


def grade_session(session, model=None):
    """세션의 모든 답안을 채점하고 총점을 저장한다.

    **풀면서 '바로 채점'으로 이미 매긴 문항은 건너뛴다** — 답이 그때와 똑같을
    때만이다(채점한 답안을 `feedback['answer']` 에 남겨 둔다). 같은 답을 두 번
    채점하면 LLM 호출이 두 배가 되고, 문항 점수가 화면에서 본 것과 달라지는
    일까지 생긴다. 옛 기록에는 그 키가 없으므로 그때는 다시 채점한다.
    """
    from django.utils import timezone

    total = 0.0
    for att in session.attempts.select_related('question'):
        done = att.feedback if isinstance(att.feedback, dict) else None
        if att.graded_at and done and done.get('answer') == att.answer_text:
            total += att.score
            continue
        try:
            res = grade_answer(att.question, att.answer_text, model=model)
        except Exception as e:
            # 실패한 것은 `answer` 를 남기지 않는다 — 다음에 다시 채점해야 한다
            res = {
                'score': 0.0, 'max': float(att.question.points), 'engine': 'error',
                'points': [], 'summary': f'채점 실패: {e}',
            }
        else:
            res = dict(res, answer=att.answer_text)
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
