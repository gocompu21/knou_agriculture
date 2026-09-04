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
    "- 취소선이 그어진 글자는 제외한다.\n"
    "- 답안 박스 안에는 글씨를 가지런히 쓰도록 **연한 파란 점선 괘선**이\n"
    "  인쇄되어 있다. 이 괘선은 글자가 아니므로 무시한다. 획으로 읽지 않는다.\n\n"
    "한글 손글씨 판독 시 주의:\n"
    "- 받침을 흘려 쓴 경우가 많다. 아래 자모는 특히 혼동되니 문맥으로 판단한다.\n"
    "  ㄴ/ㄹ, ㅁ/ㅇ, ㅂ/ㅍ, ㄱ/ㅋ, ㅅ/ㅈ/ㅊ, ㅐ/ㅔ, ㅗ/ㅜ, ㅓ/ㅏ\n"
    "- 아래 [출제 용어] 목록에 있는 낱말과 비슷하게 보이면 그 표기를 채택한다.\n"
    "  이 시험의 전문 용어는 표기가 고정돼 있으므로 목록을 우선한다.\n"
    "- 다만 목록에 없는 낱말을 목록의 낱말로 억지로 바꾸지 않는다.\n"
    "- 영문 약어는 대문자로, 화학식은 유니코드 첨자로 옮긴다.\n"
    "- 정말 알아볼 수 없는 글자만 [?]로 표시한다. 남발하지 않는다.\n\n"
    "수식·표는 모양을 살려 옮긴다 (화면이 이 표기를 그대로 분수와 표로 그린다):\n"
    "- 가로줄 위아래로 쓴 **분수**는 [eq]분자 / 분모[/eq] 로 적는다. 분자·분모가\n"
    "  여러 항이면 괄호로 묶는다. 예: [eq]1,000 × 1,000 / 40 = 25,000[/eq],\n"
    "  [eq](3 + 2) / 2 = 2.5[/eq]. 계산식 한 줄 전체를 [eq] 안에 넣는다.\n"
    "- 지수는 ^ 로 적는다. 예: 10^0.35, 1.01^n. 첨자는 유니코드(N₀, H⁺)로 적는다.\n"
    "- 줄과 칸을 그어 만든 **표**는 마크다운 표로 옮긴다. 첫 줄이 머리글이고\n"
    "  둘째 줄은 |---|---| 구분행이다. 예:\n"
    "  | 구분 | A군집 | B군집 |\n  |---|---|---|\n  | 종1 | 4 | 4 |\n"
    "  칸이 비었으면 비워 둔다. 표 밖의 글은 표 앞뒤 줄에 따로 쓴다.\n"
    "- 화살표·순서 나열(ㄱ → ㄴ → ㄷ)은 → 기호로 옮긴다.\n"
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

    lines += ["",
              "함께 읽어야 할 것:",
              "- 페이지 오른쪽 아래(첫 쪽은 오른쪽 위에도)에 '시험지 코드'라는 작은 글씨와 영문·숫자 10자가 "
              "인쇄돼 있으면 그 코드를 paper_code 에 그대로 적는다. 보이지 않으면 빈 문자열.",
              "- 각 답안 위에 인쇄된 문제문(발문)의 첫 15자 안팎을 stem 에 읽히는 대로 적는다. "
              "위 목록과 다르더라도 고쳐 쓰지 말고 사진에 인쇄된 대로 적는다.",
              "  (이 사진이 정말 이 시험지인지 대조하는 데 쓴다)"]

    terms = _collect_terms(questions)
    if terms:
        lines += ["", "[출제 용어] 답안에 나올 가능성이 높은 표기입니다.",
                  ' · '.join(terms)]
    return '\n'.join(lines)


# 시험지 코드는 16진수 대문자다. 판독 모델이 0↔O, 1↔I 처럼 헷갈리는 글자를
# 코드에 나올 수 있는 쪽으로 되돌린 뒤 비교한다.
_CODE_FIX = str.maketrans({'O': '0', 'Q': '0', 'I': '1', 'L': '1', 'Z': '2',
                           'S': '5', 'G': '6', 'B': '8'})


def _norm_code(s):
    import re
    s = re.sub(r'[^0-9A-Za-z]', '', s or '').upper()
    return s.translate(_CODE_FIX)


def _stem_match(stem, text):
    """사진에서 읽은 발문 머리가 실제 문항의 발문과 같은가.

    글자 단위 겹침으로 본다. 손글씨 판독처럼 정밀할 필요는 없고, 전혀 다른
    문제를 걸러내면 된다 — 같은 문항이면 대개 0.8 이상, 다른 문항이면 0.3 아래다.
    """
    import re
    a = re.sub(r'[^가-힣A-Za-z0-9]', '', stem or '')
    b = re.sub(r'[^가-힣A-Za-z0-9]', '', (text or '').split('\n')[0])
    if len(a) < 4:
        return None                 # 읽지 못했으면 판단 보류
    head = b[:max(len(a) + 4, 12)]
    hit = sum(1 for ch in a if ch in head)
    return hit / len(a)


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
        stem: str = Field(default='', description="답안 위에 인쇄된 문제문의 첫 15자 안팎, 읽히는 대로")
        text: str = Field(description="손글씨를 그대로 옮긴 답안. 비었으면 빈 문자열")

    class PageResult(BaseModel):
        paper_code: str = Field(default='', description="페이지 오른쪽 아래(첫 쪽은 오른쪽 위에도 있음)의 시험지 코드. 없으면 빈 문자열")
        answers: list[AnswerItem]

    client = genai.Client(api_key=api_key)
    model = settings.GEMINI_ESSAY_OCR_MODEL
    collected = {}
    rejected = []          # [{'page_no', 'reason'}] — 이 시험지가 아닌 사진
    want_code = _norm_code(session.paper_code)

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

        # ── 이 시험지가 맞는가 ─────────────────────────────────────
        # 번호만 보고 넣으면 다른 회차 시험지도 번호가 같으면 그대로 들어간다.
        # 1) 코드가 보이면 코드로 판정한다 — 가장 확실하다.
        got_code = _norm_code(parsed.paper_code)
        if want_code and len(got_code) >= 6 and got_code != want_code:
            rejected.append({
                'page_no': up.page_no,
                'reason': f'다른 시험지 사진입니다 (사진의 코드 {parsed.paper_code.strip()}, '
                          f'이 시험지는 {session.paper_code})',
                'got_code': got_code,   # 뷰가 이 코드의 시험지를 찾아 이어갈 길을 낸다
            })
            continue

        # 2) 코드가 안 보이면(2쪽부터는 없을 수 있다) 인쇄된 발문으로 판정한다.
        #    읽힌 발문이 있는 문항 가운데 절반 넘게 어긋나면 다른 시험지다.
        judged, wrong = 0, []
        for item in parsed.answers:
            q = by_number.get(item.number)
            if not q:
                continue
            r = _stem_match(item.stem, q.text)
            if r is None:
                continue
            judged += 1
            if r < 0.5:
                wrong.append(item.number)
        if judged >= 2 and len(wrong) * 2 > judged:
            rejected.append({
                'page_no': up.page_no,
                'reason': '다른 시험지 사진입니다 — 인쇄된 문제가 이 시험지의 '
                          f'{", ".join(str(n) for n in wrong)}번과 다릅니다',
            })
            continue

        for item in parsed.answers:
            q = by_number.get(item.number)
            if not q:
                continue
            # 발문이 읽혔는데 다른 문제면 그 답만 빼고, 나머지는 살린다
            r = _stem_match(item.stem, q.text)
            if r is not None and r < 0.5:
                rejected.append({
                    'page_no': up.page_no,
                    'reason': f'{item.number}번 답안 위에 인쇄된 문제가 이 시험지의 '
                              f'{item.number}번과 달라 넣지 않았습니다',
                })
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
    return results, rejected
