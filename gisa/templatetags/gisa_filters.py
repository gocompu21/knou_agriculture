import os
import re

from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = Library()


_TABLE_STYLE = (
    "border-collapse:collapse;width:auto;max-width:100%;"
    "margin:4px 0;font-size:0.92em;line-height:1.5;"
)
_CELL_STYLE = "border:1px solid #999;padding:3px 10px;text-align:left;"
_TH_STYLE = _CELL_STYLE + "background:#f2f2f2;font-weight:600;white-space:nowrap;"

# 표 셀 안의 줄바꿈. 원문이 <br> 로 적어 두는데, 셀 내용은 escape 를 거쳐
# 들어오므로 &lt;br&gt; 형태가 된다. 표 안에서만 태그로 되돌린다.
_CELL_BR = re.compile(r"&lt;\s*br\s*/?\s*&gt;", re.IGNORECASE)


def _table_rows(block):
    """표 덩어리를 행 목록으로 정규화한다.

    원문에는 두 가지 흐트러짐이 있다.
      - 셀 안에 줄바꿈이 들어가 다음 줄이 `|` 로 시작하지 않는 경우
        (2021-3-94: 서식지 특성 3줄이 한 셀에 들어 있다) -> 앞 행에 이어붙인다
      - 표 뒤에 빈 줄과 각주가 이어지는 경우
        (2017-3-45, 2013-3-43: "*본 표의 면적은 1ha...") -> 표는 거기서 끝난다

    반환: (행목록, 표 뒤에 남은 줄들)
    """
    rows, tail = [], []
    ended = False
    for raw in block.split("\n"):
        ln = raw.strip()
        if ended:
            tail.append(raw)
            continue
        if not ln:
            if rows:
                ended = True
            continue
        if ln.startswith("|"):
            rows.append(ln)
        elif rows:
            # 셀 안 줄바꿈 - 직전 행 마지막 셀에 이어붙인다
            base = rows[-1].rstrip()
            if base.endswith("|"):
                base = base[:-1].rstrip()
            rows[-1] = base + "<br>" + ln + " |"
        else:
            return [], block.split("\n")
    return rows, tail


def _md_table(block):
    """마크다운 표 -> HTML <table>.

    `| a | b |` 행이 이어지고 둘째 줄이 `|---|---|` 인 덩어리만 표로 본다.
    표가 아니면 None 을 돌려준다.
    """
    lines, tail = _table_rows(block)
    if len(lines) < 2:
        return None
    if not re.match(r"^\|[\s:\-|]+\|$", lines[1]):
        return None

    def cells(ln):
        # 셀 안에서 줄을 나눌 때 원문이 <br> 을 쓴다. 이 함수는 escape 를 거친
        # 텍스트를 받으므로 &lt;br&gt; 형태로 들어오는데, 그대로 두면 글자로
        # 보인다. 표 안에서만 태그로 되돌린다.
        return [_CELL_BR.sub("<br>", c.strip()) for c in ln.strip("|").split("|")]

    head = cells(lines[0])
    body = [cells(ln) for ln in lines[2:]]
    ncol = len(head)

    # +, 0, - 나 '많다/적다'처럼 짧은 값만 든 열은 가운데 정렬이 읽기 좋다.
    # 서술이 든 열까지 가운데로 몰면 오히려 나빠지므로 열 단위로 판단한다.
    def _short(c):
        return "<br>" not in c and len(c) <= 8

    center = [
        all(_short(row[i]) for row in body if i < len(row) and row[i])
        for i in range(ncol)
    ]

    def _align(style, i):
        if i < len(center) and center[i]:
            return style.replace("text-align:left", "text-align:center")
        return style

    out = ['<table style="%s">' % _TABLE_STYLE]
    out.append("<thead><tr>")
    for i, h in enumerate(head):
        out.append('<th style="%s">%s</th>' % (_align(_TH_STYLE, i), h))
    out.append("</tr></thead><tbody>")
    for row in body:
        if len(row) < ncol:
            row = row + [""] * (ncol - len(row))
        out.append("<tr>")
        for i, cel in enumerate(row[:ncol]):
            out.append('<td style="%s">%s</td>' % (_align(_CELL_STYLE, i), cel))
        out.append("</tr>")
    out.append("</tbody></table>")
    note = "\n".join(tail).strip()
    if note:
        out.append('<div style="margin-top:6px;font-size:0.92em;line-height:1.6;">%s</div>'
                   % note.replace("\n", "<br>"))
    return "".join(out)


def _render_box(inner):
    """[box] 안쪽을 렌더링. 마크다운 표가 있으면 HTML 표로 바꾼다."""
    inner = inner.strip()
    tbl = _md_table(inner)
    if tbl is not None:
        # 표만 있는 박스는 테두리가 이중이 되므로 박스 테두리를 뺀다
        return (
            '<div class="q-box q-box-table" style="margin:6px 0;'
            'text-indent:0;font-weight:normal;display:block;'
            'max-width:100%;overflow-x:auto">' + tbl + "</div>"
        )
    return (
        '<div class="q-box" style="border:2px solid #333;border-radius:4px;'
        "padding:6px 12px;margin:6px 0;background:#fff;line-height:1.7;"
        'text-indent:0;font-weight:normal;display:block;max-width:100%">'
        + inner
        + "</div>"
    )


def _tables_anywhere(text):
    """본문 중간에 있는 마크다운 표 덩어리를 찾아 HTML 표로 바꾼다.

    [box] 밖에 표만 있는 해설(191건)이 있어 박스 처리와 별개로 필요하다.
    `|`로 시작하는 줄이 2줄 이상 연속하고 둘째 줄이 구분행인 덩어리만 바꾼다.
    """
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < n and lines[j].lstrip().startswith("|"):
                j += 1
            block = "\n".join(lines[i:j])
            tbl = _md_table(block)
            if tbl is not None:
                out.append(tbl)
                i = j
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


# 해설에 직접 그린 도해를 싣기 위한 SVG 통과 처리 --------------------------
# escape() 를 그대로 통과시키면 태그가 글자로 보이므로, [svg]...[/svg] 로 감싼
# 것만 따로 빼두었다가 escape 뒤에 되돌린다. 되돌리기 전에 스크립트·외부 참조를
# 걸러 내용이 관리자 손을 거치지 않고 들어와도 위험하지 않게 한다.
_SVG_BLOCK = re.compile(r"\[svg\](.*?)\[/svg\]", re.DOTALL | re.IGNORECASE)
_SVG_BAD = re.compile(
    r"<\s*(script|foreignObject|iframe|object|embed|image|use)\b"
    r"|\bon[a-z]+\s*=" r"|javascript:" r"|<!\s*ENTITY",
    re.IGNORECASE,
)


def _sanitize_svg(src):
    """도해로 쓸 수 있는 SVG만 통과시킨다. 아니면 빈 문자열."""
    s = (src or "").strip()
    if not s.lower().startswith("<svg") or _SVG_BAD.search(s):
        return ""
    # 폭이 넘치지 않도록 감싸고, 화면 낭독기에는 그림임을 알린다
    return (
        '<div class="q-svg" role="img" style="margin:8px 0;max-width:100%;'
        'overflow-x:auto">' + s + "</div>"
    )


_EQ_BLOCK = re.compile(r"\[eq\](.*?)\[/eq\]", re.DOTALL | re.IGNORECASE)

# 수식 안의 나눗셈은 분수로 보여 준다 — a / b 를 세로 분수로 쌓는다.
# 피연산자는 괄호로 묶인 덩어리, 함수 표기(ln1.5), 숫자·변수까지만 잡는다.
_FRAC_TERM = r"(?:\([^()]*\)|(?:ln|log|sin|cos|tan)[\d.]*|[A-Za-z0-9,.₀-₉]+)"
# 단위 표기(g/m², 본/m², 입/g, 개체/ha)는 나눗셈이 아니라 한 덩어리다.
# 분자가 한 글자 단위이고 분모가 m²·g·ha 류면 분수로 만들지 않는다.
_UNIT = re.compile(
    r"^(?:[gkmcLl]|㎡|m²|m2|본|입|개체|주|ha|㏊|kg|mg|cm|mm|km|년|일|초|회)$")
_FRAC = re.compile(r"(%s)\s*/\s*(%s)" % (_FRAC_TERM, _FRAC_TERM))
# 분수는 인라인 블록을 vertical-align:middle 로 앉힌다 — 분수막이 등호·
# 부등호가 그려지는 x-height 중앙과 같은 높이가 된다. 앞뒤는 &nbsp; 로
# 띄운다(일반 공백은 렌더링 과정에서 눌려 기호와 분수가 붙어 보였다).
_FRAC_STYLE = (
    "display:inline-block;vertical-align:middle;text-align:center;"
    "margin:0 .3em;line-height:1.3;font-size:0.95em;"
)


def frac_span(num, den):
    """세로 분수 마크업 — [eq] 박스와 학습자료의 공식 줄이 함께 쓴다."""
    return (
        '&nbsp;<span style="%s">'
        '<span style="display:block;padding:0 .35em">%s</span>'
        '<span style="display:block;border-top:1px solid currentColor;'
        'padding:0 .35em">%s</span></span>&nbsp;'
    ) % (_FRAC_STYLE, num, den)


def _fractions(s):
    """a / b → 세로 분수. 이미 태그가 낀 부분은 건드리지 않는다."""
    def one(m):
        num, den = m.group(1), m.group(2)
        # 단위 표기(g/m², 본/m², 입/g)는 나눗셈이 아니라 한 덩어리다
        if _UNIT.match(num) and _UNIT.match(den):
            return m.group(0)
        return frac_span(num, den)

    out, last = [], 0
    for m in re.finditer(r"<[^>]+>", s):        # 태그 밖에서만 치환
        out.append(_FRAC.sub(one, s[last:m.start()]))
        out.append(m.group())
        last = m.end()
    out.append(_FRAC.sub(one, s[last:]))
    return "".join(out)

_EQ_STYLE = (
    # 수식은 흰 바탕에 검은 글씨로 — 배경이 옅은 초록이면 글자가 묻힌다
    "display:block;margin:8px 0;padding:11px 16px;background:#fff;color:#111;"
    "border:1px solid #dde5e0;border-left:3px solid #2d6a4f;"
    "border-radius:0 6px 6px 0;"
    # 숫자·기호는 세리프 수식체, 한글은 본문 고딕(SUIT)으로 폴백시킨다.
    # 스택이 serif 로 끝나면 한글 글리프가 없는 앞 폰트를 지나 명조로
    # 떨어져, 박스 안 한글만 본문과 다른 글씨가 됐다.
    "font-family:'Cambria Math','Times New Roman','SUIT',sans-serif;"
    "font-size:1em;"
    "line-height:2;letter-spacing:0.01em;overflow-x:auto;"
)

# 붙어 있는 연산 기호는 좌우로 띄운다 — 0.7−0.1+0.3−0.1=0.8 처럼
# 공백 없이 이어지면 숫자와 기호가 한 덩어리로 보인다.
# 줄바꿈은 건드리지 않는다 — 여러 줄로 쓴 풀이가 한 줄로 이어지면 못 읽는다.
# 그래서 \s 대신 [^\S\n](줄바꿈 아닌 공백)만 먹는다.
_EQ_OPS = re.compile(r"[^\S\n]*([=+×÷≥≤<>≒≠])[^\S\n]*")
# 음수 부호와 뺄셈을 가른다: 여는 괄호나 다른 연산자 뒤의 −는 부호다
_EQ_MINUS = re.compile(r"(?<=[\w),.\]])[^\S\n]*([−–—-])[^\S\n]*(?=[\w(])")


def _spaced_ops(s):
    """수식의 연산 기호 좌우에 여백을 준다. 태그 안은 건드리지 않는다."""
    def one(chunk):
        chunk = _EQ_OPS.sub(r" \1 ", chunk)
        chunk = _EQ_MINUS.sub(r" \1 ", chunk)
        # 줄머리 들여쓰기는 살린다 (= 로 이어지는 줄이 계단처럼 보이게)
        return re.sub(r"(?<!\n)[^\S\n]{2,}", " ", chunk)

    out, last = [], 0
    for m in re.finditer(r"<[^>]+>", s):
        out.append(one(s[last:m.start()]))
        out.append(m.group())
        last = m.end()
    out.append(one(s[last:]))
    return "".join(out)


def _render_qtext(value):
    """내부 공통 렌더링"""
    if value is None:
        return ""

    # SVG 도해는 escape 대상에서 빼둔다 (아래에서 검사 후 되돌린다)
    svgs = []

    def _stash(m):
        svgs.append(m.group(1))
        return f"\x00SVG{len(svgs) - 1}\x00"

    value = _SVG_BLOCK.sub(_stash, value)

    text = escape(value)
    text = text.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
    # 빈칸 괄호 ( ) 가 너무 좁아 보기 흉하므로 넓혀서 표시한다 (데이터는 그대로)
    text = re.sub(r"\(\s{1,3}\)", "(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)", text)
    text = re.sub(
        r"\[box\](.*?)\[/box\]",
        lambda m: _render_box(m.group(1)),
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = _tables_anywhere(text)
    # LaTeX-style $...$ 수식: 내부의 ^{X}, _{X}를 <sup>, <sub>로 바꾸고 $ 제거
    def _latex_inline(m):
        inner = m.group(1)
        inner = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", inner)
        inner = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", inner)
        inner = re.sub(r"\^([A-Za-z0-9+\-])", r"<sup>\1</sup>", inner)
        inner = re.sub(r"_([A-Za-z0-9+\-])", r"<sub>\1</sub>", inner)
        return inner
    text = re.sub(r"\$([^$]+)\$", _latex_inline, text)
    # 일반 ^{X}, _{X} 첨자
    text = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", text)
    text = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", text)
    # 괄호 없는 ^X, _X (계산 풀이에 자주 쓰인다). 뒤에 오는 한 토막만 올린다.
    # ^(rt) 처럼 괄호로 묶은 것도 받는다
    text = re.sub(r"\^\(([^)]{1,12})\)", r"<sup>\1</sup>", text)
    # 소수 지수(10^0.35)까지 한 덩어리로 올린다 — 0만 올리면 10⁰.35가 된다
    text = re.sub(r"\^(-?\d+(?:\.\d+)?|[A-Za-z]\d?)(?![\w.])",
                  r"<sup>\1</sup>", text)
    text = re.sub(r"(?<=[A-Za-z])_([A-Za-z0-9]{1,3})(?![A-Za-z0-9])",
                  r"<sub>\1</sub>", text)
    # **강조** — 해설에서 핵심어를 짚는 데 쓴다. 문제 지문에는 거의 없으나
    # 있어도 별표가 그대로 보이는 것보다는 강조로 처리되는 편이 낫다
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"<strong>\1</strong>", text)
    # 수식 박스 — 계산 풀이가 본문에 섞이면 한쪽으로 치우쳐 읽기 나쁘다.
    # [eq]...[/eq] 로 묶으면 여백을 준 박스에 세리프체로 보여 준다.
    # 박스 안 줄머리 공백은 &nbsp; 로 살린다 — 데이터에 쓴 들여쓰기가
    # 그대로 보이게 하는 것이 규칙이다. CSS 로 들여쓰기를 흉내내면
    # (음수 text-indent 등) 데이터와 따로 놀아 정렬이 어긋난다.
    # 한글 항이 섞인 분수는 [frac]분자|분모[/frac] 로 적어 둔다 —
    # 띄어쓰기 때문에 항의 경계를 자동으로 가를 수 없다.
    text = re.sub(
        r"\[frac\]([^|\[\]]+)\|([^|\[\]]+)\[/frac\]",
        lambda m: frac_span(m.group(1).strip(), m.group(2).strip()),
        text,
    )

    def _eq_box(m):
        body = _spaced_ops(_fractions(m.group(1).strip("\n")))
        body = re.sub(r"(^|\n)( +)",
                      lambda x: x.group(1) + "&nbsp;" * len(x.group(2)), body)
        return '<span class="q-eq" style="%s">%s</span>' % (_EQ_STYLE, body)

    text = _EQ_BLOCK.sub(_eq_box, text)

    # 계산 문항의 '계산)' 아래 풀이는 한 단 들여써서 라벨과 구분한다
    m = re.match(r'계산\)\s*\n(.+)$', text, re.DOTALL)
    if m:
        text = ('계산)\n<span class="q-calc" style="display:block;'
                'padding-left:1.1em">' + m.group(1) + '</span>')

    text = text.replace("\n", "<br>")

    # 빼두었던 SVG를 검사해 되돌린다. 자리표시자 앞뒤의 <br>은 그림이 제 줄을
    # 차지하도록 흡수한다 (안 그러면 그림 위아래에 빈 줄이 생긴다)
    for i, src in enumerate(svgs):
        text = re.sub(
            r"(?:<br>)?\x00SVG%d\x00(?:<br>)?" % i,
            lambda m, s=src: _sanitize_svg(s),
            text,
        )
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


# 빈출 등급 별표 -------------------------------------------------------------
# GisaQuestion.freq_tier: 1~5 (5가 최다 빈출), 0 이면 미산정이라 표시하지 않는다.
# 등급은 쪽집게 노트의 절 단위로 "그 주제에 연결된 기출 수"를 세어 산출한다.

_TIER_LABEL = {
    5: "최다 빈출",
    4: "자주 출제",
    3: "보통",
    2: "가끔 출제",
    1: "드물게 출제",
}


@register.filter(name="freq_stars")
def freq_stars(tier):
    """빈출 등급을 별표 배지로 렌더링. 0/None 이면 아무것도 출력하지 않는다."""
    try:
        t = int(tier or 0)
    except (TypeError, ValueError):
        return ""
    if t < 1 or t > 5:
        return ""
    label = _TIER_LABEL.get(t, "")
    return mark_safe(
        '<span class="freq-stars freq-t%d" title="%s (기출 빈도 %d/5)" aria-label="%s">%s</span>'
        % (t, label, t, label, "★" * t)
    )


# 이미지 캐시 무력화 -----------------------------------------------------------
# 문항 이미지를 교체해도 파일명이 그대로면 브라우저가 옛 이미지를 계속 쓴다
# (nginx 응답에 Cache-Control/ETag 가 없어 재검증도 하지 않는다).
# 파일 수정시각을 쿼리로 붙여 파일이 바뀔 때만 새로 받게 한다.

@register.filter(name="vurl")
def vurl(field):
    """ImageFieldFile → `url?v=<mtime>`. 파일이 없으면 url 만 돌려준다."""
    if not field:
        return ""
    try:
        url = field.url
    except (ValueError, AttributeError):
        return ""
    try:
        ts = int(os.path.getmtime(field.path))
    except (OSError, ValueError, AttributeError, NotImplementedError):
        return url
    sep = "&" if "?" in url else "?"
    return "%s%sv=%d" % (url, sep, ts)


# 빈출 주제의 출제 회차 배지 ---------------------------------------------------
# freq_note 에 "2026-2 2025-3 2021-3 …" 형태로 최신순 회차가 들어 있다.
# 이걸 배지로 펼쳐 어느 해에 나왔는지 한눈에 보이게 한다.

# 최신일수록 진하게. 최근 출제가 눈에 먼저 들어와야 학습 우선순위가 잡힌다.

def _round_tone(year, newest):
    """출제 연도가 최신에서 얼마나 떨어졌는지로 색을 정한다."""
    try:
        gap = int(newest) - int(year)
    except (TypeError, ValueError):
        gap = 99
    if gap <= 1:
        return "#1b4332", "#fff", "#1b4332"      # 가장 최근 — 진한 초록 채움
    if gap <= 3:
        return "#40806b", "#fff", "#40806b"
    if gap <= 6:
        return "#dbe9e0", "#1f4d3a", "#a9c8b8"
    if gap <= 10:
        return "#eef3ef", "#40624f", "#cfdcd4"
    return "#f6f7f6", "#8b968f", "#e2e6e3"       # 오래된 회차 — 흐리게


@register.filter(name="note_badges")
def note_badges(rounds_line):
    """학습자료의 「출제」 줄 → 두 자리 연도 배지 (2024-2 → 24-2).

    노트는 한 줄에 다섯 회차가 늘어서서 숫자 띠처럼 보였다. 배지로 끊고
    연도를 두 자리로 줄이면 한눈에 몇 회차인지 잡힌다. 회차 뒤에 붙는
    설명(— 다섯 회차 모두 …)은 배지 뒤에 그대로 흘려 둔다.
    """
    if not rounds_line:
        return ""
    text = str(rounds_line).strip()
    # 회차 뒤 괄호는 배점·유형 주석(2022-2(4.5점 표그림)) — 배지 안에 붙인다
    found = list(re.finditer(r"\b(\d{4})-(\d)\b(?:\s*\(([^)]{1,20})\))?", text))
    if not found:
        return escape(text)

    newest = max(int(m.group(1)) for m in found)
    out = []
    for m in found:
        y, r, memo = m.group(1), m.group(2), m.group(3)
        bg, fg, bd = _round_tone(y, newest)
        inner = "%s-%s" % (y[2:], r)
        if memo:
            inner += '<i class="fq-memo">%s</i>' % escape(memo)
        out.append(
            '<span class="fq-r" style="background:%s;color:%s;border-color:%s">'
            "%s</span>" % (bg, fg, bd, inner)
        )

    # 마지막 회차 뒤에 남은 설명 꼬리를 살린다
    tail = text[found[-1].end():].strip(" —-·")
    if tail:
        out.append('<span class="fq-tail">%s</span>' % escape(tail))
    return mark_safe("".join(out))


@register.filter(name="freq_badges")
def freq_badges(note):
    """freq_note → 연도별 색이 다른 회차 배지들.

    freq_note 는 이미 최신순으로 정렬돼 있어 그대로 쓴다.
    """
    if not note:
        return ""
    rounds = [r for r in str(note).split() if r]
    if not rounds:
        return ""

    years = []
    for r in rounds:
        y = r.split("-")[0]
        if y.isdigit():
            years.append(int(y))
    newest = max(years) if years else 0

    out = []
    for r in rounds:
        y = r.split("-")[0]
        bg, fg, bd = _round_tone(y if y.isdigit() else None, newest)
        out.append(
            '<span class="fq-r" style="background:%s;color:%s;border-color:%s">%s</span>'
            % (bg, fg, bd, escape(r))
        )
    return mark_safe("".join(out))
