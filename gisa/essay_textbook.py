# -*- coding: utf-8 -*-
"""실기 쪽집게 노트 — 기출을 주제(topic_key) 단위로 묶어 필기 교재처럼 보여 준다.

재료는 셋이다.
  1. 문항 메타: topic_key(같은 주제 묶음), topic_group(8개 분류), freq_rounds(출제
     회차 수), written_freq(필기 등장 횟수), qtype.
  2. 정리 자료 `freq58` — 3회 이상 나온 58주제를 정의·이유·사례 세 층으로 쓴 마크다운.
  3. 정리 자료 `calc` — 계산 18주제의 공식·대입·함정.

주제마다 별(출제 회차 수)·기출 배지(어느 회차)·정리 본문·모범답안·관련 문항을 붙여
분류별 아코디언으로 낸다. 어느 주제를 넣는가: 2회 이상 출제, 계산, 재출제 유력
(1회 출제이나 필기 10회 이상 등장). 1회만 나온 나머지는 회차별 학습에서 본다.
"""
import json
import os
import re

import markdown as md
from django.core.cache import cache
from django.db.models import Q

from .models import GisaEssayNote, GisaEssayQuestion
from .templatetags.gisa_filters import frac_span, qtext

CACHE_TTL = 600

# 직접 지은 주제 제목 — 대표 문항의 "연도-회차-번호" → 제목. 발문을 규칙으로 잘라
# 만든 제목은 문제의 부분집합이 되기 쉬워(예: "토양은 입경에 따라 사토, 미사토…"),
# 정리 자료가 없는 주제는 여기서 문제의 뜻을 제목으로 적어 둔다. 규칙은 여기 없을 때만.
_TITLES_PATH = os.path.join(os.path.dirname(__file__), 'essay_topic_titles.json')
_titles_cache = {'mtime': None, 'data': {}}


def _custom_titles():
    try:
        mtime = os.path.getmtime(_TITLES_PATH)
    except OSError:
        return {}
    if _titles_cache['mtime'] != mtime:
        with open(_TITLES_PATH, encoding='utf-8') as f:
            data = json.load(f)
        _titles_cache.update(mtime=mtime,
                             data={k: v for k, v in data.items() if not k.startswith('_')})
    return _titles_cache['data']


# ------------------------------------------------------------------ 수식 표기

# 항: 괄호 묶음, ln/log 식, 숫자·문자 덩어리. 분자는 ×·로 이어진 곱까지, 분모는 항 하나만
# (20÷50×100 은 20/50 × 100 이지 20/(50×100) 이 아니다).
_SYM = r"(?:\([^()]*\)|(?:ln|log)\s?\(?[\d.,A-Za-z₀-₉]*\)?|[A-Za-z0-9.,₀-₉]+(?:<su[bp]>[^<]*</su[bp]>)*)"
_CHAIN = r"%s(?:\s*[×·]\s*%s)*" % (_SYM, _SYM)
_DIV = re.compile(r"(?<![가-힣])(%s)\s*÷\s*(%s)" % (_CHAIN, _SYM))
_FRAC_TAG = re.compile(r"\[frac\]([^|\[\]]+)\|([^|\[\]]+)\[/frac\]")


def _latex_plain(x):
    """$…$ 안의 LaTeX 를 화면용 평문으로. 우리 노트에 쓰인 범위만 다룬다."""
    x = re.sub(r'\\(ln|log|sin|cos|tan|exp)\b\s*', r'\1', x)
    for a, b in (('\\times', '×'), ('\\div', '÷'), ('\\approx', '≈'), ('\\cdot', '·'),
                 ('\\ge', '≥'), ('\\le', '≤'), ('\\rightarrow', '→'), ('\\to', '→'),
                 ('\\,', ' '), ('\\;', ' '), ('\\!', ''), ('\\left', ''), ('\\right', '')):
        x = x.replace(a, b)
    x = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'[frac]\1|\2[/frac]', x)
    x = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', x)
    x = re.sub(r'_([A-Za-z0-9])', r'<sub>\1</sub>', x)
    return x.strip()


def mathify(s):
    """마크다운 본문의 수식 표기를 화면용으로 바꾼다.

    - $$…$$ / $…$ 의 LaTeX → 평문 (\\ln → ln, \\frac → 분수, N_0 → N₀ 꼴)
    - x^{n} · e^(rt) · (1.01)^t → 위첨자
    - A ÷ B, [frac]A|B[/frac] → 세로 분수
    노트를 LaTeX 로 적어 두면 화면에 $ 기호가 그대로 남았다. 마크다운 변환 전에 돈다.
    """
    s = re.sub(r'\$\$(.+?)\$\$', lambda m: _latex_plain(m.group(1)), s, flags=re.S)
    s = re.sub(r'(?<![\\$])\$(?!\$)([^$\n]{1,120}?)\$', lambda m: _latex_plain(m.group(1)), s)
    s = re.sub(r'\^\{([^}]{1,12})\}', r'<sup>\1</sup>', s)
    s = re.sub(r'\^\(([^)]{1,12})\)', r'<sup>\1</sup>', s)
    s = re.sub(r'\^(-?\d+(?:\.\d+)?|[A-Za-z]\d?)(?![\w.])', r'<sup>\1</sup>', s)
    s = _DIV.sub(lambda m: frac_span(m.group(1), m.group(2)), s)
    s = _FRAC_TAG.sub(lambda m: frac_span(m.group(1).strip(), m.group(2).strip()), s)
    return s


def number_sections(html):
    """절 제목(<h3>)에 (1) (2) 번호를 붙이고, 그 아래 내용을 .nt-sec 으로 감싸 들여쓴다.

    한 주제 안에 정의·이유·사례·공식·대입이 잇달아 나와 어디서 절이 바뀌는지
    눈이 놓치기 쉽다. 번호와 들여쓰기가 뼈대를 보여 준다.
    """
    parts = re.split(r'(<h3>.*?</h3>)', html, flags=re.S)
    if len(parts) < 3:
        return html
    out, n = [parts[0]], 0
    for i in range(1, len(parts), 2):
        n += 1
        head = parts[i]
        # 제목 맨 앞의 ⚠️·★ 같은 표시는 번호 뒤에 오면 어수선하다 → 제목 끝으로
        head = re.sub(r'<h3>\s*([⚠★☆✅❗]+️?)\s*(.*?)\s*</h3>', r'<h3>\2 \1</h3>', head, flags=re.S)
        head = head.replace('<h3>', '<h3><span class="nt-hno">(%d)</span> ' % n, 1)
        body = parts[i + 1] if i + 1 < len(parts) else ''
        out.append(head + '<div class="nt-sec">' + body + '</div>')
    return ''.join(out)


def _bigrams(s):
    s = re.sub(r'[^가-힣A-Za-z0-9]', '', s or '')
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _pick_rep(cert, title, rounds, is_calc):
    """정리 항목의 대표 문항 — 「출제」 줄의 회차들 안에서 제목과 글자쌍이 가장
    많이 겹치는 문항.

    전에는 첫 회차 + 빈출 수로 좁힌 뒤 낱말 겹침으로 골랐는데, 한글은 띄어쓰기가
    들쭉날쭉해 낱말이 통째로 어긋난다("중규모 교란설" vs "중규모교란설에서").
    그래서 같은 회차의 다른 4회 주제(K-전략종)에 붙는 사고가 났다. 글자쌍
    겹침은 띄어쓰기에 흔들리지 않는다. 첫 회차에서 뚜렷하지 않으면 나머지 회차도 본다.
    """
    pairs = re.findall(r'(\d{4})-(\d)', rounds or '')
    if not pairs:
        return None
    tb = _bigrams(title)
    best, best_score = None, -1.0
    for i, (y, r) in enumerate(pairs):
        cand = GisaEssayQuestion.objects.filter(
            certification=cert, source='기출', year=int(y), round=int(r))
        if is_calc:
            cand = cand.filter(qtype='계산')
        for q in cand:
            hay = _bigrams((q.text or '') + ' ' + ' '.join(q.answer_items or [])
                           + ' ' + (q.answer_text or ''))
            score = len(tb & hay) / max(1, len(tb))
            if score > best_score:
                best, best_score = q, score
        if best_score >= 0.5:        # 첫 회차에서 뚜렷하면 거기서 끝
            break
    return best


def _loosen(md_text):
    """문단 줄 바로 다음에 붙은 목록·표 앞에 빈 줄을 넣는다.

    nl2br 을 빼면 마크다운이 "문단\\n- 항목" 을 한 문단으로 이어 붙여 목록이
    사라진다(nl2br 이 있을 때는 줄바꿈이 살아 목록처럼 보였을 뿐이다).
    """
    out, prev = [], ''
    for ln in md_text.split('\n'):
        starts_block = re.match(r'^\s*(?:[-*+]\s|\d+\.\s|\|)', ln)
        prev_para = prev.strip() and not re.match(r'^\s*(?:[-*+]\s|\d+\.\s|\||#|>)', prev)
        if starts_block and prev_para:
            out.append('')
        out.append(ln)
        prev = ln
    return '\n'.join(out)


# ------------------------------------------------------------------ 정리 자료 파싱

def parse_note_items(cert, note):
    """`## N회 · 분류 · 주제` 단위로 잘라 (머리말 마크다운, 항목 목록)을 돌려준다.

    essay_note 화면과 쪽집게 노트가 같이 쓴다. 항목마다 대표 문항(rep_pk)을
    찾아 두어야 회차 배지에서 기출을 펼치고, 주제(topic_key)와 이어 붙일 수 있다.
    """
    text = note.content
    # 분류명에도 가운뎃점이 들어가고(법규·제도) 주제명에도 들어가므로
    # (복원·복구·대체) 구분자만으로는 못 가른다. 분류명을 명시해 집는다.
    groups = '|'.join(re.escape(g) for _, g in GisaEssayQuestion.TOPIC_CHOICES)
    parts = re.split(r'^## (\d+)회 · (%s) · (.+)$' % groups, text, flags=re.M)
    intro_md = parts[0]
    items = []
    for i in range(1, len(parts), 4):
        freq, group, title, body = parts[i:i + 4]
        m = re.search(r'\*\*출제\*\*\s*(.+)', body)
        rounds = m.group(1).strip() if m else ''

        rep = _pick_rep(cert, title, rounds, note.slug == 'calc')

        # 「공식 / 대입 / 함정」처럼 라벨이 붙은 문단은 따로 떼어 낸다 —
        # 한 덩어리로 렌더링하면 줄바꿈만으로 구분돼 빽빽해 보인다.
        body_rest = re.sub(r'^\*\*출제\*\*.*$', '', body, flags=re.M)
        body_rest = re.sub(r'^\s*---\s*$', '', body_rest, flags=re.M)
        blocks = []
        for lab in ('공식', '대입', '함정', '유형', '주의'):
            bm = re.search(r'^\*\*%s\*\*\s*(.+)$' % lab, body_rest, flags=re.M)
            if not bm:
                continue
            raw = re.sub(r'_\{([^}]{1,12})\}', r'<sub>\1</sub>', bm.group(1).strip())
            blocks.append({
                'label': lab,
                'html': md.markdown(mathify(raw), extensions=['tables']),
            })
            body_rest = body_rest.replace(bm.group(0), '')

        items.append({
            'freq': int(freq),
            'group': group.strip(),
            'title': title.strip(),
            'rounds': rounds,
            'rep_pk': rep.pk if rep else None,
            'topic_key': rep.topic_key if rep else '',
            'blocks': blocks,
            'warned': '⚠️ 요구가 커진 지점' in body,
            # 본문에도 ÷·지수·LaTeX 가 섞여 있다(1.5배 도달 연수 풀이 등).
            # nl2br 은 쓰지 않는다 — 원문이 40자 안팎으로 줄을 끊어 둔 것이 화면에
            # 그대로 나와 문단이 좁게 토막났다. 문단은 화면 폭에 맞게 흐르게 둔다.
            'html': number_sections(
                md.markdown(mathify(_loosen(body_rest)), extensions=['tables'])),
        })
    return intro_md, items


# ------------------------------------------------------------------ 주제 제목

_DIRECTIVE = re.compile(
    r'\s*(?:에 대하여|에 대해|을|를|은|는|의)?\s*'
    r'(?:각각\s*)?(?:간단히\s*)?(?:무엇인지\s*|어떻게\s*|왜\s*)?'
    r'(?:쓰시오|서술하시오|설명하시오|구하시오|열거하시오|적으시오|답하시오|기술하시오|'
    r'나열하시오|계산하시오|제시하시오|약술하시오|비교하시오|정의하시오|그리시오|채우시오)'
    r'\.?\s*$')


# 발문만으로 주제가 안 보이는 꼴. "다음 표에서 사토와 식토를 구분하여…"처럼 내용이
# 담긴 긴 발문은 여기 걸리지 않게 강한 신호만 본다.
_GENERIC = re.compile(r'설명하는|해당하는|무엇인가|무엇이라|알맞은|빈칸|괄호|\(\s*\)|보기에서|골라|고르|다음 설명|다음 중|^다음(?:은|의|에서)?\s*$')
_TAIL_VERB = re.compile(r'\s*(?:나누어|비교하여|구분하여|정리하여|이용하여|들어|찾아|골라|각각)$')
# 발문에서 주제어(머리 명사구)를 떼는 꼴. 조사(을/는)만 보고 자르면 "침입종 때문에
# 고유종이 멸종위기에 처하게 되|는" 처럼 동사 어미에서 잘리므로, 뒤에 오는 말까지
# 확인되는 꼴만 쓴다. 안 맞으면 발문 전체를 둔다.
_HEAD_PATTERNS = [
    re.compile(r'^(.{2,44}?)(?:이란|란)\s*(?:무엇|어떤|어떻게|그\s*정의|정의|$)'),
    re.compile(r'^(.{2,44}?)\s*(?:에 대하여|에 대해)(?:\s|$)'),
    re.compile(r'^(.{2,44}?)(?:은|는)\s*(?:어떻게 다른지|무엇인지|무엇을|몇\s)'),
    re.compile(r'^(.{2,60}?)(?:의\s*(?:종류|유형|기능|특징|방법|원인|조건|사례|예|목표|평가항목|내용|이유))?'
               r'\s*\d+\s*가지(?:\s*이상)?(?:를|을)?(?:\s|$)'),
    re.compile(r'^(.{2,44}?)의\s*(?:정의|개념)(?:을|를)?(?:\s|$)'),
]


def _clip(t, n=60):
    return (t[:n - 2] + '…') if len(t) > n else t


# 답 항목의 "표지 : 값" 꼴. 표지는 ㄱ·㉠·①·A 같은 빈칸 이름.
#   "ㄱ : 20", "① ㄱ : 구조", "(A) : 4분의 1", "(A) 다년생", "㉠ 가장자리"
_KEY = r'[ㄱ-ㅎ㉠-㉭①-⑳A-Za-z]'
_ANS_KV = re.compile(
    r'^[①-⑳\d.)\s]*(?:\(\s*(%s)\s*\)|(%s))\s*[:：\-–—]?\s*(.+)$' % (_KEY, _KEY))
# 발문의 안내 문장 — 빈칸 문항에서 주제를 담지 않는 부분
_LEAD = re.compile(
    r'^(?:다음|아래|위)?[^.\n]{0,30}?(?:빈칸|괄호|\(\s*\)|알맞은|들어갈|채우시오|쓰시오)[^.\n]*[.?]?\s*',
    re.M)


def _clause(text, n=60):
    """첫 문장에서 끊는다. 문장이 너무 길면 쉼표에서, 그것도 없으면 글자 수로."""
    text = text.strip()
    m = re.search(r'[.!?]\s', text + ' ')
    if m and m.end() <= n + 12:
        return text[:m.start() + 1]
    m = re.search(r',\s', text)
    if m and 24 <= m.start() <= n:
        return text[:m.start()] + ' …'
    return _clip(text, n)


def _fill_blanks(q):
    """빈칸 문항: ( ㄱ )·( ① )·(   ) 에 답을 채운 문장을 돌려준다.

    "다음 빈칸에 알맞은 말을 채우시오"는 발문으로는 주제를 알 수 없고, 답만
    떼면 'ㄱ'·'경성' 같은 조각이 남는다. 문항 전체 맥락(상자 문장, 상자가
    없으면 발문의 본문)에 답을 넣어 읽으면 그 자체가 주제 요약이다:
    "경관생태학에서 (구조)은 이질적인 공간요소들이 이루는 유형을 말한다."
    """
    text = q.text or ''
    m = re.search(r'\[box\](.*?)\[/box\]', text, flags=re.S)
    if m:
        body = m.group(1)
    else:
        body = _LEAD.sub('', text)          # 안내 문장을 뗀 나머지가 본문
    body = re.sub(r'\[/?(?:eq|svg|frac)\]', '', body)
    body = re.sub(r'\s+', ' ', body).strip()
    if not body:
        return ''

    items = [str(a) for a in (q.answer_items or [])]
    keyed, seq = {}, []
    for a in items:
        a = a.strip()
        kv = _ANS_KV.match(a)
        circ = re.match(r'^([①-⑳])', a)
        if kv and len(kv.group(3)) <= 40:
            key = kv.group(1) or kv.group(2)
            val = kv.group(3).strip(' :：-–—')
            keyed[key] = val
            seq.append(val)
        else:
            seq.append(re.sub(r'^[①-⑳\d.)\s]+', '', a).strip())
        if circ:
            keyed.setdefault(circ.group(1), seq[-1])

    def rep(mm):
        key = mm.group(1).strip()
        return '(%s)' % keyed[key] if key in keyed else mm.group(0)
    body = re.sub(r'\(\s*(%s)\s*\)' % _KEY, rep, body)
    # 이름 없는 빈칸 (     ) 은 답을 차례로 넣는다
    it = iter(seq)
    body = re.sub(r'\(\s*\)', lambda mm: '(%s)' % next(it, ' '), body)
    return _clause(body)


def _answer_word(q):
    """답의 첫 항목(없으면 answer_text 첫 줄)에서 주제어를 뽑는다. 표로 된 답은 못 쓴다."""
    cands = list(q.answer_items or [])
    first = (q.answer_text or '').strip().split('\n')[0].strip()
    if first and not first.startswith('|'):
        cands.append(first)
    for a in cands:
        a = re.sub(r'^[①-⑳\d.)\s]+', '', str(a)).strip()
        a = re.sub(r'\s*[:：].*$', '', a)          # "용어 : 설명" 이면 용어만
        a = re.sub(r'[\[\]*_`]', '', a).strip()
        if a:
            return _clip(a, 48)
    return ''


def _title_from(q):
    """정리 자료가 없는 주제는 대표 문항의 발문에서 제목을 뽑는다.

    "다음에서 설명하는 것은 무엇인가"처럼 발문만으로는 주제가 안 보이는
    문항은 답(첫 항목)이 곧 주제어이므로 답을 제목으로 쓴다. 빈칸 문항은
    지문에 답을 채운 문장을 쓴다.
    """
    if q.qtype == '빈칸' or re.search(r'\(\s*%s?\s*\)' % _KEY, q.text or ''):
        filled = _fill_blanks(q)
        if filled and not re.search(r'\(\s*%s?\s*\)' % _KEY, filled):
            return filled
    t = re.sub(r'\[box\].*?\[/box\]', '', q.text or '', flags=re.S)
    t = re.sub(r'\[/?(?:eq|svg)\][^\[]*(?:\[/(?:eq|svg)\])?', '', t)
    t = t.strip().split('\n')[0].strip()
    t = re.sub(r'\s*\((?:단|다만),.*$', '', t)
    t = _DIRECTIVE.sub('', t).strip(' ,.:;?')
    t = _TAIL_VERB.sub('', t).strip(' ,.:;?')
    # 두 문장으로 이어지는 발문("…4가지를 쓰고, …하시오")은 첫 요구까지만
    t = re.split(r'\s*(?:쓰고|설명하고|서술하고|구하고|들고),?\s', t)[0].strip(' ,.:;?')
    if not t or len(t) < 6 or _GENERIC.search(t):
        a = _answer_word(q)
        if a:
            return a
    # "환경포텐셜의 종류 4가지를 쓰고" → "환경포텐셜": 발문의 머리 명사구가 주제어다.
    # 너무 짧거나 "다음…"으로 시작하면 발문 전체를 둔다.
    for pat in _HEAD_PATTERNS:
        m = pat.match(t)
        if m:
            head = m.group(1).strip(' ,')
            if re.search(r'(?:하는|되는|인|한|된)\s*것$', head):
                # "…에 의해 결정되는 것은 무엇인지" — 수수께끼형은 답이 주제어다
                a = _answer_word(q)
                if a:
                    return a
            if len(head) >= 3 and not re.match(r'^(다음|아래|위)', head):
                t = head
            break
    # 꼬리에 남은 조사("생태통로를", "종류를", "…으로")는 뗀다
    t = re.sub(r'(?<=[가-힣)\]A-Za-z0-9])\s*(?:으로|을|를|은|는|의|에)$', '', t).strip(' ,')
    # "…에 의해 결정되는 것(은 무엇인지)" — 지시어를 떼고 나면 '것'으로 끝나는
    # 수수께끼형이 남는다. 이때는 답이 주제어다
    if re.search(r'(?:하는|되는|인|한|된|라는)\s*것$', t):
        a = _answer_word(q)
        if a:
            return a
    return _clip(t)


# ------------------------------------------------------------------ 교재 조립

def build_textbook(cert):
    """분류별 주제 목록을 만든다. 무거우므로 10분 캐시."""
    qs_all = GisaEssayQuestion.objects.filter(certification=cert, source='기출')
    notes = list(GisaEssayNote.objects.filter(certification=cert))
    stamp = max([n.updated_at.timestamp() for n in notes] + [0])
    try:
        stamp = max(stamp, os.path.getmtime(_TITLES_PATH))
    except OSError:
        pass
    key = 'essay_tb:v7:%d:%d:%d' % (cert.pk, qs_all.count(), int(stamp))
    hit = cache.get(key)
    if hit:
        return hit

    # 정리 자료 → topic_key 로 이어 붙인다
    by_key = {}
    for n in notes:
        _, items = parse_note_items(cert, n)
        for it in items:
            if it['topic_key']:
                by_key.setdefault(it['topic_key'], {})[n.slug] = it

    sel = (qs_all.exclude(topic_key='')
           .filter(Q(freq_rounds__gte=2) | Q(freq_rounds=1, written_freq__gte=10)
                   | Q(qtype='계산')))
    keys = set(sel.values_list('topic_key', flat=True)) | set(by_key)
    topics = {}
    for q in qs_all.filter(topic_key__in=keys).order_by('-year', '-round', 'number'):
        topics.setdefault(q.topic_key, []).append(q)

    names = dict(GisaEssayQuestion.TOPIC_CHOICES)
    custom = _custom_titles()
    groups = {gid: [] for gid, _ in GisaEssayQuestion.TOPIC_CHOICES}
    groups[0] = []
    for tk, qlist in topics.items():
        rep = qlist[0]                       # 가장 최근 회차 문항
        freq = max(q.freq_rounds for q in qlist)
        rounds = sorted({(q.year, q.round) for q in qlist}, reverse=True)
        notes_ = by_key.get(tk, {})
        note = notes_.get('freq58')
        calc = notes_.get('calc')
        title = (custom.get('%d-%d-%d' % (rep.year, rep.round, rep.number))
                 or (note or calc or {}).get('title') or _title_from(rep))
        stars = 3 if freq >= 5 else 2 if freq >= 3 else 1 if freq >= 2 else 0
        comeback = freq <= 1 and any(q.written_freq >= 10 for q in qlist)
        is_calc = any(q.qtype == '계산' for q in qlist)
        pts = sorted({float(q.points) for q in qlist})
        pts_label = ('%g점' % pts[0]) if len(pts) == 1 else ('%g~%g점' % (pts[0], pts[-1]))
        qtypes = []
        for q in qlist:
            d = q.get_qtype_display()
            if d not in qtypes:
                qtypes.append(d)
        groups.setdefault(rep.topic_group or 0, []).append({
            'key': tk,
            'title': title,
            'group': names.get(rep.topic_group, '미분류'),
            'stars': stars,
            'freq': freq,
            'count': len(qlist),
            'rounds_str': ' '.join('%d-%d' % r for r in rounds),
            'latest': '%d-%d' % rounds[0],
            'latest_year': rounds[0][0],
            'latest_round': rounds[0][1],
            'pts': pts_label,
            'qtypes': ' · '.join(qtypes[:3]),
            'comeback': comeback,
            'calc': is_calc,
            'warned': bool(note and note.get('warned')),
            'has_note': bool(note),
            'blocks': (calc or {}).get('blocks', []),
            'html': (note or {}).get('html', ''),
            'rep_pk': rep.pk,
            'q_html': str(qtext(rep.text)),
            'ans_items': [str(qtext(a)) for a in (rep.answer_items or [])],
            'ans_html': str(qtext(rep.answer_text)) if rep.answer_text else '',
        })

    out = []
    for gid, _name in GisaEssayQuestion.TOPIC_CHOICES + [(0, '미분류')]:
        lst = groups.get(gid) or []
        if not lst:
            continue
        lst.sort(key=lambda t: (-t['stars'], -t['freq'], -t['latest_year'], -t['latest_round']))
        out.append({
            'id': gid, 'name': _name, 'count': len(lst),
            'star3': sum(1 for t in lst if t['stars'] == 3),
            'topics': lst,
        })
    result = {
        'groups': out,
        'total': sum(g['count'] for g in out),
        'n_star3': sum(g['star3'] for g in out),
        'n_calc': sum(1 for g in out for t in g['topics'] if t['calc']),
        'n_comeback': sum(1 for g in out for t in g['topics'] if t['comeback']),
        'n_warned': sum(1 for g in out for t in g['topics'] if t['warned']),
    }
    cache.set(key, result, CACHE_TTL)
    return result
