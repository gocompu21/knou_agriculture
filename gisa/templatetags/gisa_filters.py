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
        return [c.strip() for c in ln.strip("|").split("|")]

    head = cells(lines[0])
    body = [cells(ln) for ln in lines[2:]]
    ncol = len(head)

    out = ['<table style="%s">' % _TABLE_STYLE]
    out.append("<thead><tr>")
    for h in head:
        out.append('<th style="%s">%s</th>' % (_TH_STYLE, h))
    out.append("</tr></thead><tbody>")
    for row in body:
        if len(row) < ncol:
            row = row + [""] * (ncol - len(row))
        out.append("<tr>")
        for cel in row[:ncol]:
            out.append('<td style="%s">%s</td>' % (_CELL_STYLE, cel))
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
    # **강조** — 해설에서 핵심어를 짚는 데 쓴다. 문제 지문에는 거의 없으나
    # 있어도 별표가 그대로 보이는 것보다는 강조로 처리되는 편이 낫다
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"<strong>\1</strong>", text)
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
