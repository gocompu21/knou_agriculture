import re

from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = Library()


@register.filter(name="qtext")
def qtext(value):
    """문제 텍스트를 HTML로 변환.

    지원 마크업:
      [box]...[/box]  → 테두리 박스
      줄바꿈           → <br>
    """
    text = escape(value)
    # <u>...</u> 밑줄 복원 (escape가 &lt;u&gt;로 변환한 것을 되돌림)
    text = text.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
    # [box]...[/box] → <div class="q-box">...</div>
    text = re.sub(
        r"\[box\](.*?)\[/box\]",
        lambda m: '<div class="q-box" style="border:2px solid #333;border-radius:4px;padding:6px 12px;margin:6px 0;background:#fff;line-height:1.7;text-indent:0;font-weight:normal;display:block">' + m.group(1).strip() + "</div>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # ^{X} → <sup>X</sup> 위첨자
    text = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", text)
    # _{X} → <sub>X</sub> 아래첨자
    text = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", text)
    # 줄바꿈 → <br> (q-box 내부 포함)
    text = text.replace("\n", "<br>")
    return mark_safe(text)
