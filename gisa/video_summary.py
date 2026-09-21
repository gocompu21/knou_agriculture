# -*- coding: utf-8 -*-
"""유튜브 강의 영상을 Gemini 로 요약한다 — 주소만 넘기면 된다.

**Gemini 는 유튜브 주소를 그대로 받는다**(`file_data.file_uri`). 영상을 내려받아
올릴 필요가 없고, 자막이 아니라 **화면을 본다**. 조경 작도 강의처럼 '말이 아니라
손이 내용'인 영상에서 차이가 크다 — 실측에서 "T자와 삼각자로 경계선", "원형
템플릿으로 교목 심볼", "인출선을 묶어 정돈" 같은 것을 읽어냈고, 이것은 자막에
없는 말이다.

**비용은 초당 약 95토큰**이다(실측: 11분 영상 62,782토큰). 처음에 초당 263으로
어림잡아 "영상 직접은 수백 원"이라고 보았는데, 재 보니 한 편에 30원 남짓이었다.
`media_resolution` 을 낮춰도 유튜브 주소는 토큰 수가 같으므로 만지지 않는다.

**공개 영상만 된다** — 비공개·일부공개는 Gemini 가 못 본다. 그때는 오류를 그대로
전한다. 퍼가기를 막은 영상(`embeddable=False`)은 상관없다. 그쪽은 우리 화면에
못 박는다는 뜻일 뿐이라 요약은 된다.
"""
import re

from django.conf import settings
from django.utils import timezone

# **보는 길이의 상한(초).** 길이를 미리 알아내 막는 대신 `end_offset` 으로
# 여기까지만 보게 한다 — 두 시간짜리 통강의를 물려도 토큰이 이만큼에서 멈춘다.
#
# 길이를 재서 막으려 했다가 걷어냈다. watch 페이지의 `lengthSeconds` 는 집에서는
# 읽히는데 **서버(데이터센터 IP)에서는 응답에 아예 없어** 늘 0이 나왔다 — 막으려던
# 바로 그 자리에서 관문이 열려 있었다. oEmbed 도 길이를 주지 않는다.
# 실측: 11분 영상 62,724토큰, `end_offset=120s` 로 자르면 10,935토큰.
MAX_SECONDS = 90 * 60

_PROMPT = """이 영상은 «{cert}» {part} 수험 강의다. 수험생이 "이 영상을 볼지,
어디부터 볼지" 를 정할 수 있게 정리하라.

다음 두 부분만, 한국어로, 아래 형식 그대로 쓴다.

## 요약
- 3~4줄. 무엇을 다루는 영상이고 누구에게 쓸모 있는지.

## 목차
- `M:SS 소제목` 으로 시작하는 줄을 5~10개. 소제목은 12자 안팎.
- 각 줄 아래 한 줄 들여써서 그 대목에서 실제로 하는 일을 적는다.
- **화면에서 무엇을 그리거나 보여 주는지**를 반드시 적어라. 말로 설명만 하는
  대목과 실제로 손을 움직이는 대목은 수험생에게 값어치가 다르다.

지키기:
- 시각은 영상에 실제로 나오는 시점이어야 한다. 어림잡아 쓰지 마라.
- 영상에 없는 내용을 채워 넣지 마라. 짧으면 짧은 대로 둔다.
- 광고·인사·채널 구독 안내는 목차에 넣지 마라."""

_PART_LABEL = {
    'written': '필기',
    'practical': '실기 필답형',
    'work': '실기 작업형(도면)',
    'both': '',
}


def summarize(res, model=None):
    """`GisaResource` 한 건을 요약한다. `{'ok': …, 'summary'/'error': …}`."""
    from google import genai
    from google.genai import types

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return {'ok': False, 'error': 'GEMINI_API_KEY 가 설정되어 있지 않다'}
    if not res.video_id:
        return {'ok': False, 'error': '유튜브 영상이 아니다'}

    prompt = _PROMPT.format(cert=res.certification.name,
                            part=_PART_LABEL.get(res.part, ''))
    url = f'https://www.youtube.com/watch?v={res.video_id}'
    # **client 를 변수에 담아 둘 것.** 임시 객체로 두고 `.models.generate_content`
    # 를 바로 부르면 호출 도중 수거되어 "Cannot send a request, as the client has
    # been closed" 가 난다(실제로 당했다).
    client = genai.Client(api_key=api_key)
    try:
        resp = client.models.generate_content(
            model=model or settings.GEMINI_VIDEO_MODEL,
            contents=types.Content(parts=[
                types.Part(file_data=types.FileData(file_uri=url),
                           video_metadata=types.VideoMetadata(
                               end_offset=f'{MAX_SECONDS}s')),
                types.Part(text=prompt)]))
    except Exception as e:                                   # noqa: BLE001
        return {'ok': False, 'error': _friendly(e)}

    text = (resp.text or '').strip()
    if not text:
        return {'ok': False, 'error': '요약이 비어 있다 — 다시 시도해 보라'}

    res.summary = text
    res.summary_at = timezone.now()
    res.save(update_fields=['summary', 'summary_at'])
    u = getattr(resp, 'usage_metadata', None)
    return {'ok': True, 'summary': text, 'summary_html': render(text),
            'tokens': getattr(u, 'prompt_token_count', 0) if u else 0}


def _friendly(e):
    """Gemini 오류를 관리자가 무엇을 해야 할지 아는 말로 바꾼다."""
    s = str(e)
    if 'PERMISSION_DENIED' in s or 'private' in s.lower():
        return '비공개 영상이라 읽을 수 없다 (공개 영상만 요약된다)'
    if 'RESOURCE_EXHAUSTED' in s or '429' in s:
        return 'API 한도에 걸렸다 — 잠시 뒤 다시'
    if 'not found' in s.lower() or 'NOT_FOUND' in s:
        return '영상을 찾을 수 없다 (삭제되었을 수 있다)'
    return f'요약 실패 ({type(e).__name__}: {s[:150]})'


# ─────────────────────────────────────────────────────────────────────────
# 화면에 그리기

_TS = re.compile(r'(?<![\d:])((?:\d{1,2}:)?\d{1,2}:\d{2})(?![\d:])')
_BOLD = re.compile(r'\*\*(.+?)\*\*')


def _secs(ts):
    p = [int(x) for x in ts.split(':')]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def render(text):
    """요약 글을 HTML 로. **시각은 눌러서 그 대목부터 트는 단추가 된다.**

    목차만 읽고 끝나면 반쪽이다 — 10:48 을 눌러 바로 그 대목을 보는 것이
    이 기능의 값어치다. 단추는 `data-t` 에 초를 싣고, `_videos.html` 의
    위임 리스너가 `&start=` 를 붙여 그 자리에 영상을 끼운다.
    """
    from django.utils.html import escape

    out, in_ul = [], False
    for raw in (text or '').splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith('#'):
            if in_ul:
                out.append('</ul>'); in_ul = False
            out.append(f'<h5>{escape(line.lstrip("# ").strip())}</h5>')
            continue
        indent = len(line) - len(line.lstrip())
        body = line.lstrip().lstrip('-*').strip()
        if not body:
            continue
        html = _BOLD.sub(lambda m: f'<strong>{escape(m.group(1))}</strong>',
                         escape(body))
        # 이스케이프 뒤에 부른다 — 단추 마크업이 다시 이스케이프되지 않도록
        html = _TS.sub(
            lambda m: f'<button type="button" class="vd-ts" '
                      f'data-t="{_secs(m.group(1))}">{m.group(1)}</button>',
            html)
        if not in_ul:
            out.append('<ul>'); in_ul = True
        out.append(f'<li class="{"sub" if indent >= 2 else ""}">{html}</li>')
    if in_ul:
        out.append('</ul>')
    return '\n'.join(out)
