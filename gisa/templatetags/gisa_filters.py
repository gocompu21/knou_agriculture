import re

from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = Library()


def _render_qtext(value):
    """내부 공통 렌더링"""
    text = escape(value)
    text = text.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
    text = re.sub(
        r"\[box\](.*?)\[/box\]",
        lambda m: '<div class="q-box" style="border:2px solid #333;border-radius:4px;padding:6px 12px;margin:6px 0;background:#fff;line-height:1.7;text-indent:0;font-weight:normal;display:inline-block;max-width:100%">' + m.group(1).strip() + "</div>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", text)
    text = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", text)
    text = text.replace("\n", "<br>")
    return text


@register.filter(name="qtext")
def qtext(value):
    """문제 텍스트를 HTML로 변환.

    지원 마크업:
      [box]...[/box]  → 테두리 박스
      줄바꿈           → <br>
    """
    return mark_safe(_render_qtext(value))


@register.filter(name="qtext_pre")
def qtext_pre(value):
    """[box] 이전 부분만 렌더링 (box가 없으면 전체 반환).
    배지가 질문문 바로 옆에 붙도록 끝쪽 공백/개행을 제거한다."""
    idx = value.find("[box]")
    if idx == -1:
        return mark_safe(_render_qtext(value))
    pre = value[:idx].rstrip()
    return mark_safe(_render_qtext(pre))


@register.filter(name="qtext_box")
def qtext_box(value):
    """[box] 이후 부분만 렌더링 (box가 없으면 빈 문자열).
    박스가 항상 다음 줄에 오도록 <br>로 개행을 선행한다."""
    idx = value.find("[box]")
    if idx == -1:
        return ""
    return mark_safe("<br>" + _render_qtext(value[idx:]))
