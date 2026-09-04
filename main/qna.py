# -*- coding: utf-8 -*-
"""질의응답 — 과목 맥락을 붙여 Gemini 에게 묻는다.

**과목은 사용자가 고르지 않는다.** 질문한 화면에서 자동으로 잡는다.
회원 대부분이 한쪽 시험만 쓰고(방송대 59 / 기사 8 / 둘 다 24), 방송대는
동명 과목이 5개라 목록에서 고르게 하면 오히려 헷갈린다.

**쪽집게 노트는 있으면 근거로 붙이고, 없으면 그냥 답한다.** 노트에서
질문과 겹치는 절만 잘라 쓴다 — 한 과목 노트가 3만~27만 자라 통째로
넣으면 토큰 한도에 걸린다. 노트를 못 찾았을 때 답을 막지 않는 것이
중요하다. 교재에 없는 것을 묻는 경우가 오히려 흔하다.
"""
import re

from django.conf import settings
from django.utils import timezone

# 답변에 근거로 붙일 노트 분량. 절 2~3개 정도이며, 이보다 늘리면
# 토큰만 먹고 답이 산만해진다.
NOTE_BUDGET = 2500
DAILY_LIMIT = 20

_STOP = set("""무엇 어떻게 하는 이란 인가 인지 대해 대하여 관해 관하여 알려 설명
주세요 하나요 인가요 뭔가요 뭐예요 뭐야 그리고 하지만 있는 없는 것은 것이 되는
차이 무슨 어떤 왜요 궁금 질문 답변 부탁 정도 경우 때문 통해 위해""".split())


# 조사를 떼지 않으면 "양이온치환용량이" 가 통째로 잡혀 노트의
# "양이온치환용량" 과 어긋난다. 손글씨 판독에서 쓰던 방식과 같다.
_JOSA = ("으로서", "이라는", "에서는", "이라고", "으로", "에서", "에게", "이란",
         "이나", "라는", "과의", "와의", "은", "는", "이", "가", "을", "를",
         "의", "에", "도", "만", "과", "와", "로", "고")


def _strip_josa(w):
    for j in _JOSA:
        if len(w) > len(j) + 1 and w.endswith(j):
            return w[: -len(j)]
    return w


def _tokens(text):
    """질문에서 뜻이 있는 낱말만 추린다. 조사는 떼어 낸다."""
    out = []
    for w in re.findall(r"[가-힣A-Za-z]{2,}", text or ""):
        if w in _STOP:
            continue
        out.append(w)
        stripped = _strip_josa(w)
        if stripped != w and len(stripped) >= 2 and stripped not in _STOP:
            out.append(stripped)
    return out


def _score(passage, words, title=""):
    """노트 한 대목이 질문과 얼마나 겹치는가.

    출현 횟수로 세면 "토양" 처럼 흔한 낱말이 많이 나오는 절이 이겨,
    "토양의 완충능" 을 물었는데 "토양분류" 절이 뽑힌다. 그래서
      - 낱말마다 한 번만 센다 (횟수 무시)
      - 긴 낱말일수록 크게 친다 (완충능 > 토양)
      - 제목에서 걸리면 그 절의 주제라는 뜻이라 가중치를 준다
    """
    if not passage:
        return 0
    body = passage
    hit = 0
    for w in {w for w in words if len(w) >= 2}:
        weight = len(w) ** 2          # 2글자 4점, 4글자 16점, 8글자 64점
        if w in title:
            hit += weight * 3         # 절 제목에 있으면 주제어다
        elif w in body:
            hit += weight
    return hit


def _split_sections(content):
    """노트 마크다운을 절 단위로 자른다. 제목을 함께 남긴다."""
    if not content:
        return []
    parts = re.split(r"^(#{2,4}\s+.+)$", content, flags=re.M)
    out, title = [], ""
    for i, p in enumerate(parts):
        if re.match(r"^#{2,4}\s+", p or ""):
            title = re.sub(r"^#+\s*", "", p).strip()
        elif p and p.strip():
            out.append((title, p.strip()))
    return out


def find_note(question, subject=None, cert_name="", cert_subject=""):
    """질문과 가장 겹치는 노트 대목을 찾는다. 없으면 (None, '')."""
    words = _tokens(question)
    if not words:
        return None, ""

    sections = []
    if subject is not None:
        from exam.models import StudyNote
        for n in StudyNote.objects.filter(subject=subject):
            for title, body in _split_sections(n.content):
                sections.append((f"{n.title} · {title}" if title else n.title, body))
    elif cert_name:
        from gisa.models import GisaTextbook
        qs = GisaTextbook.objects.filter(certification__name=cert_name)
        # 실기는 과목 구분이 없다(생태복원 전문실무 하나). 과목으로 좁히면
        # 그런 이름의 노트가 없어 근거를 아예 못 찾으므로 전체에서 찾는다.
        if cert_subject and cert_subject != "실기":
            qs = qs.filter(subject__name=cert_subject)
        for tb in qs:
            head = tb.subject.name if tb.subject_id else cert_name
            for title, body in _split_sections(tb.content):
                sections.append((f"{head} · {title}" if title else head, body))

    if not sections:
        return None, ""

    ranked = sorted(sections, key=lambda s: -_score(s[1], words, s[0]))
    best = ranked[0]
    # 2글자 낱말 하나(4점)만 걸린 것은 근거가 못 된다. 3글자 이상이
    # 본문에 있거나(9점) 2글자가 제목에 있으면(12점) 통과한다.
    if _score(best[1], words, best[0]) < 9:
        return None, ""

    picked, used, titles = [], 0, []
    for title, body in ranked[:3]:
        if used >= NOTE_BUDGET:
            break
        room = NOTE_BUDGET - used
        chunk = body[:room]
        picked.append(f"[{title}]\n{chunk}")
        titles.append(title)
        used += len(chunk)
    return "\n\n".join(picked), " / ".join(titles[:2])


def build_prompt(q):
    """질문 하나에 대한 프롬프트. (프롬프트, 참고한 노트 제목)"""
    ask = q.title.strip()
    if q.body.strip():
        ask += "\n" + q.body.strip()

    if q.subject is not None:
        grade = f"{q.subject.grade}학년 " if q.subject.grade else ""
        head = (f"한국방송통신대학교 농학과 {grade}**{q.subject.name}** 과목에 "
                f"관한 질문이다.\n"
                f"대학 학부 수준으로 답하라. 기말시험(객관식) 대비 학습이 목적이다.")
        style = ("- 핵심을 먼저 한두 문장으로 밝히고, 필요하면 항목을 나눠 설명한다.\n"
                 "- 시험에 나오는 형태(정의·비교·분류)를 염두에 두고 정리한다.")
    elif q.cert_name and "실기" in (q.cert_subject or ""):
        head = (f"**{q.cert_name}** 실기 필답형에 관한 질문이다.\n"
                f"국가기술자격 기사 실기 수준으로 답하라.")
        style = ("- **답안지에 그대로 쓸 수 있는 형태**로 ① ② ③ 항목을 나눠 답한다.\n"
                 "- 항목마다 한 문장으로 채점 포인트가 분명하게 쓴다.\n"
                 "- 설명문이 아니라 답안 형식이어야 한다.")
    else:
        where = f"{q.cert_name} 필기"
        if q.cert_subject:
            where += f" **{q.cert_subject}** 과목"
        head = (f"**{where}**에 관한 질문이다.\n"
                f"국가기술자격 기사 필기 수준으로 답하라.")
        style = ("- 핵심을 먼저 밝히고 항목을 나눠 설명한다.\n"
                 "- 선택지로 헷갈리기 쉬운 지점이 있으면 짚어 준다.")

    note, titles = find_note(ask, q.subject, q.cert_name, q.cert_subject)
    if note:
        ground = (f"\n[우리 교재(쪽집게 노트)의 관련 대목]\n{note}\n\n"
                  f"위 교재 내용을 **우선 근거로** 삼아 답하되, 부족한 부분은 "
                  f"보충해도 좋다. 교재와 어긋나는 내용을 쓰지 마라.\n")
        tail = ""
    else:
        ground = ""
        tail = ("\n우리 교재에서 관련 대목을 찾지 못했다. 일반적인 학술 내용으로 "
                "답하되, **교재 범위를 벗어날 수 있다는 점을 답 끝에 한 줄로** "
                "알려라.\n")

    prompt = f"""{head}

{ground}[질문]
{ask}
{tail}
[답변 방식]
{style}
- 한국어로, 700자 안팎으로 간결하게.
- 확실하지 않은 것은 단정하지 말고 그렇다고 밝힌다.
- 인사말·머리말 없이 곧바로 답부터 쓴다.
- **LaTeX 를 쓰지 마라.** $\text{{H}}^+$ 같은 표기 대신 H⁺, Ca²⁺, NH₄⁺ 처럼
  유니코드 첨자를 그대로 쓴다. 화면에 수식이 렌더링되지 않아 기호가
  글자로 드러난다."""
    return prompt, titles


def ask_gemini(q):
    """질문에 답을 채워 저장한다. 성공하면 True."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        q.error = "GEMINI_API_KEY 가 설정되지 않았습니다."
        q.save(update_fields=["error"])
        return False

    prompt, titles = build_prompt(q)
    model = getattr(settings, "GEMINI_QNA_MODEL", "gemini-3.7-flash")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        res = client.models.generate_content(model=model, contents=prompt)
        text = (res.text or "").strip()
        if not text:
            raise ValueError("빈 응답")
    except Exception as e:                     # noqa: BLE001
        q.error = f"{type(e).__name__}: {e}"[:200]
        q.save(update_fields=["error"])
        return False

    q.answer = text
    q.answer_model = model
    q.note_ref = titles
    q.answered_at = timezone.now()
    q.error = ""
    q.save(update_fields=["answer", "answer_model", "note_ref",
                          "answered_at", "error"])
    return True


def remaining_today(user):
    """오늘 남은 질문 수 — 비용보다 오남용을 막기 위한 것이다."""
    from .models import QnaQuestion
    used = QnaQuestion.objects.filter(
        user=user, created_at__date=timezone.localdate()).count()
    return max(0, DAILY_LIMIT - used)
