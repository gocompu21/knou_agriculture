# -*- coding: utf-8 -*-
"""시험지 사진에서 손글씨 답안을 판독한다.

판독과 채점을 분리하는 것이 핵심이다. 한 번에 시키면 오독인지 오답인지
구분할 수 없다. 여기서는 "무엇이라고 썼는가"만 뽑고, 사용자가 확인·수정한
뒤에 채점 엔진으로 넘긴다.

정확도를 위해 페이지 이미지와 함께 "그 페이지에 있는 문항 번호와 문제문"을
같이 보낸다. 모델이 문항 경계를 찾는 데 결정적이다.
"""
import pathlib

from django.conf import settings

OCR_SYSTEM = (
    "당신은 한국어 손글씨 답안지를 텍스트로 옮기는 전사자(transcriber)이다.\n"
    "답안은 대부분 한글이며, 전문 용어에 영문 약어(LID, HGM, GPP, NPP, IUCN, MAB, "
    "CITES 등)와 화학식(N₂, NH₄⁺, NO₃⁻, CO₂)이 섞여 있다.\n\n"
    "규칙:\n"
    "- 답안에 쓰인 내용을 있는 그대로 옮긴다. 맞춤법·오답을 고치지 않는다.\n"
    "- 채점하지 않는다. 평가·의견을 쓰지 않는다.\n"
    "- 문항 번호를 보고 어느 문제의 답인지 정확히 매칭한다.\n"
    "- ①②③ 같은 번호 기호는 그대로 옮긴다. 줄바꿈도 유지한다.\n"
    "- 빈칸이면 빈 문자열을 반환한다. 내용을 지어내지 않는다.\n"
    "- 취소선이 그어진 글자는 제외한다.\n\n"
    "한글 손글씨 판독 시 주의:\n"
    "- 받침을 흘려 쓴 경우가 많다. 아래 자모는 특히 혼동되니 문맥으로 판단한다.\n"
    "  ㄴ/ㄹ, ㅁ/ㅇ, ㅂ/ㅍ, ㄱ/ㅋ, ㅅ/ㅈ/ㅊ, ㅐ/ㅔ, ㅗ/ㅜ, ㅓ/ㅏ\n"
    "- 아래 [출제 용어] 목록에 있는 낱말과 비슷하게 보이면 그 표기를 채택한다.\n"
    "  이 시험의 전문 용어는 표기가 고정돼 있으므로 목록을 우선한다.\n"
    "- 다만 목록에 없는 낱말을 목록의 낱말로 억지로 바꾸지 않는다.\n"
    "- 영문 약어는 대문자로, 화학식은 유니코드 첨자로 옮긴다.\n"
    "- 정말 알아볼 수 없는 글자만 [?]로 표시한다. 남발하지 않는다.\n"
)


def _collect_terms(questions, limit=140):
    """이 시험지 문항들의 모범답안에서 핵심 용어를 뽑는다.

    판독 모델에 '이런 낱말이 나올 것'이라고 알려주면 한글 손글씨의
    받침 오독이 크게 준다.
    """
    import re
    from collections import Counter

    # 낱말 끝의 조사·어미를 떼어 명사형만 남긴다
    JOSA = ('으로서', '으로써', '이라고', '에서는', '에게서', '으로부터',
            '에서', '에게', '으로', '이나', '이란', '이며', '이고', '이다',
            '하는', '하여', '하고', '되는', '되어', '들과', '들의', '들을', '들이',
            '과의', '와의', '로의', '의', '을', '를', '이', '가', '은', '는',
            '와', '과', '로', '에', '도', '만', '및')
    # 서술어·기능어 (조사를 뗀 뒤 걸러낸다)
    STOP = {'있다', '없다', '한다', '위한', '위하여', '대한', '통해', '경우', '방법',
            '사용', '이용', '발생', '가능', '필요', '실시', '수행', '작성', '고려',
            '포함', '이상', '이하', '미만', '초과', '하나', '다른', '작은', '커다란',
            '따라', '의해', '또는', '그리고', '이때', '해당', '각각', '모두', '전체',
            '사항', '관한', '내용', '경우에', '지역', '상태', '것으', '하지', '한다는'}

    def strip_josa(w):
        for j in JOSA:
            if len(w) > len(j) + 1 and w.endswith(j):
                return w[:-len(j)]
        return w

    counter = Counter()
    for q in questions:
        blob = ' '.join(q.answer_items or []) + ' ' + (q.answer_text or '')
        for w in re.findall(r'[가-힣]{2,12}', blob):
            w = strip_josa(w)
            if len(w) >= 2 and w not in STOP:
                counter[w] += 1
        for w in re.findall(r'\b[A-Z]{2,6}\b', blob):
            counter[w] += 1

    return [w for w, _ in counter.most_common(limit)]


def _page_prompt(questions):
    """이 페이지에 있을 문항 목록과 예상 용어를 알려준다."""
    lines = ["이 시험지에 있는 문항 목록입니다. 각 문항의 답안을 찾아 옮기세요.", ""]
    for q in questions:
        text = (q.text or '').split('\n')[0][:110]
        lines.append(f"{q.number}번: {text}")

    terms = _collect_terms(questions)
    if terms:
        lines += ["", "[출제 용어] 답안에 나올 가능성이 높은 표기입니다.",
                  ' · '.join(terms)]
    return '\n'.join(lines)


def transcribe_uploads(session, uploads):
    """업로드된 페이지 이미지들을 판독해 {question_id: text} 를 만든다."""
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field

    from .models import GisaEssayAttempt, GisaEssayQuestion

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY 미설정')

    qs = GisaEssayQuestion.objects.filter(
        certification=session.certification, source=session.source)
    if session.source == '기출':
        qs = qs.filter(year=session.year, round=session.round)
    else:
        qs = qs.filter(section=session.section)
    questions = list(qs.order_by('number'))
    by_number = {q.number: q for q in questions}

    class AnswerItem(BaseModel):
        number: int = Field(description="문항 번호")
        text: str = Field(description="손글씨를 그대로 옮긴 답안. 비었으면 빈 문자열")

    class PageResult(BaseModel):
        answers: list[AnswerItem]

    client = genai.Client(api_key=api_key)
    model = settings.GEMINI_ESSAY_OCR_MODEL
    collected = {}

    for up in uploads:
        path = pathlib.Path(up.image.path)
        if not path.exists():
            continue
        mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
        response = client.models.generate_content(
            model=model,
            contents=[
                OCR_SYSTEM,
                _page_prompt(questions),
                types.Part.from_bytes(data=path.read_bytes(), mime_type=mime),
            ],
            config={
                'response_mime_type': 'application/json',
                'response_schema': PageResult,
                'temperature': 0,
            },
        )
        parsed = PageResult.model_validate_json(response.text)
        for item in parsed.answers:
            q = by_number.get(item.number)
            if not q:
                continue
            text = (item.text or '').strip()
            if not text:
                continue
            # 같은 문항이 여러 페이지에 걸치면 이어 붙인다
            prev = collected.get(q.pk, '')
            collected[q.pk] = (prev + '\n' + text).strip() if prev else text

        up.transcribed = True
        up.save(update_fields=['transcribed'])

    # 판독 결과를 Attempt에 저장 (아직 확정 전 — transcribe_confirmed=False)
    results = []
    for qid, text in collected.items():
        q = by_number.get(GisaEssayQuestion.objects.get(pk=qid).number)
        att, _ = GisaEssayAttempt.objects.update_or_create(
            session=session, question_id=qid,
            defaults={'transcribed_text': text, 'answer_text': text,
                      'transcribe_confirmed': False},
        )
        results.append({
            'question_id': qid,
            'number': q.number if q else 0,
            'text': text,
        })
    results.sort(key=lambda r: r['number'])
    return results
