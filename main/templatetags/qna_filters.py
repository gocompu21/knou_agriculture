# -*- coding: utf-8 -*-
"""질의응답 화면용 필터."""
import re

from django import template

register = template.Library()

_MD = [
    (re.compile(r"^#{1,6}\s*", re.M), ""),          # 제목 표시
    (re.compile(r"\*\*(.+?)\*\*", re.S), r"\1"),    # 굵게
    (re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", re.S), r"\1"),
    (re.compile(r"`([^`]+)`"), r"\1"),
    (re.compile(r"^\s*[*\-•]\s+", re.M), ""),       # 목록 기호
    (re.compile(r"^\s*\d+\.\s+", re.M), ""),
    (re.compile(r"\$"), ""),                        # LaTeX 잔재
    (re.compile(r"\text\{([^}]*)\}"), r"\1"),
    # "① [공간적 위치와 개념적 정의]" — 펼치면 소제목이 되는 자리라 대괄호는 걷어낸다
    (re.compile(r"([①-⑳]\s*)\[([^\]\n]{2,40})\]"), r"\1\2"),
]


@register.filter(name="qna_refs")
def qna_refs(text):
    """근거 절 문자열을 배지 목록으로 — "과목 · 7.7 제목 / 과목 · 2.5 제목" 을 쪼갠다.

    한 줄로 이어 붙이면 어디서 어디까지가 한 절인지 안 보인다.
    """
    return [s.strip() for s in str(text or "").split("/") if s.strip()]


@register.filter(name="qna_peek")
def qna_peek(text, limit=180):
    """답 앞부분을 미리보기로 — 마크다운 기호는 걷어낸다.

    목록에서 세 줄만 스치듯 보여 주는 자리라 ** 나 ### 이 그대로 남으면
    글이 지저분해진다. 펼쳤을 때는 JS 가 제대로 렌더링한다.
    """
    s = str(text or "")
    for pat, rep in _MD:
        s = pat.sub(rep, s)
    s = re.sub(r"\s+", " ", s).strip()
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 180
    return s[:limit] + ("…" if len(s) > limit else "")
