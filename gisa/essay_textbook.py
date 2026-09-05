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
import re

import markdown as md
from django.core.cache import cache
from django.db.models import Q

from .models import GisaEssayNote, GisaEssayQuestion
from .templatetags.gisa_filters import frac_span, qtext

CACHE_TTL = 600


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

        # 출제 줄의 첫 회차 + 빈출 수로 대표 문항을 찾는다. 같은 회차에 같은
        # 빈출 수 주제가 여럿이면 제목 낱말이 가장 많이 겹치는 것을 고른다
        # (calc 문서는 계산 유형으로 한정).
        rep = None
        rm = re.search(r'(\d{4})-(\d)', rounds)
        if rm:
            cand = GisaEssayQuestion.objects.filter(
                certification=cert, source='기출',
                year=int(rm.group(1)), round=int(rm.group(2)),
                freq_rounds=int(freq))
            if note.slug == 'calc':
                cand = cand.filter(qtype='계산')
            pool = list(cand)
            if len(pool) > 1:
                key = set(re.findall(r'[가-힣A-Za-z]{2,}', title))
                pool.sort(key=lambda q: len(
                    key & set(re.findall(r'[가-힣A-Za-z]{2,}',
                                         (q.text or '') + ' ' +
                                         ' '.join(q.answer_items or [])))),
                    reverse=True)
            if pool:
                rep = pool[0]

        # 「공식 / 대입 / 함정」처럼 라벨이 붙은 문단은 따로 떼어 낸다 —
        # 한 덩어리로 렌더링하면 줄바꿈만으로 구분돼 빽빽해 보인다.
        body_rest = re.sub(r'^\*\*출제\*\*.*$', '', body, flags=re.M)
        body_rest = re.sub(r'^\s*---\s*$', '', body_rest, flags=re.M)
        blocks = []
        for lab in ('공식', '대입', '함정', '유형', '주의'):
            bm = re.search(r'^\*\*%s\*\*\s*(.+)$' % lab, body_rest, flags=re.M)
            if not bm:
                continue
            raw = bm.group(1).strip()
            raw = re.sub(r'\^\{([^}]{1,12})\}', r'<sup>\1</sup>', raw)
            raw = re.sub(r'\^\(([^)]{1,12})\)', r'<sup>\1</sup>', raw)
            raw = re.sub(r'\^(-?\d+(?:\.\d+)?|[A-Za-z]\d?)(?![\w.])',
                         r'<sup>\1</sup>', raw)
            raw = re.sub(r'_\{([^}]{1,12})\}', r'<sub>\1</sub>', raw)
            if lab in ('공식', '대입'):
                # A ÷ B 를 세로 분수로. 항은 기호식 덩어리(2C, (A+B), ln1.5)와
                # ×·로 이어진 곱까지만 잡는다. 한글 공식은 [frac]분자|분모[/frac]
                # 로 적어 두면 그대로 그린다.
                sym = (r"(?:\([^()]*\)|(?:ln|log)\s?[\d.,A-Za-z]*"
                       r"|[A-Za-z0-9.,₀-₉]+)")
                chain = r"%s(?:\s*[×·]\s*%s)*" % (sym, sym)
                raw = re.sub(
                    r"(?<![가-힣])(%s)\s*÷\s*(%s)" % (chain, chain),
                    lambda m2: frac_span(m2.group(1), m2.group(2)), raw)
                raw = re.sub(
                    r"\[frac\]([^|\[\]]+)\|([^|\[\]]+)\[/frac\]",
                    lambda m2: frac_span(m2.group(1).strip(),
                                         m2.group(2).strip()), raw)
            blocks.append({
                'label': lab,
                'html': md.markdown(raw, extensions=['tables']),
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
            'html': md.markdown(body_rest, extensions=['tables', 'nl2br']),
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
_GENERIC = re.compile(r'설명하는 것|해당하는 것|무엇인가|무엇이라|알맞은|빈칸|괄호|\(\s*\)|^다음(?:은|의|에서)?\s*$')
_TAIL_VERB = re.compile(r'\s*(?:나누어|비교하여|구분하여|정리하여|이용하여|들어|찾아|골라|각각)$')


def _clip(t, n=60):
    return (t[:n - 2] + '…') if len(t) > n else t


def _title_from(q):
    """정리 자료가 없는 주제는 대표 문항의 발문에서 제목을 뽑는다.

    "다음에서 설명하는 것은 무엇인가"처럼 발문만으로는 주제가 안 보이는
    문항은 답(첫 항목)이 곧 주제어이므로 답을 제목으로 쓴다.
    """
    t = re.sub(r'\[box\].*?\[/box\]', '', q.text or '', flags=re.S)
    t = re.sub(r'\[/?(?:eq|svg)\][^\[]*(?:\[/(?:eq|svg)\])?', '', t)
    t = t.strip().split('\n')[0].strip()
    t = re.sub(r'\s*\((?:단|다만),.*$', '', t)
    t = _DIRECTIVE.sub('', t).strip(' ,.:;?')
    t = _TAIL_VERB.sub('', t).strip(' ,.:;?')
    if not t or len(t) < 6 or _GENERIC.search(t):
        # 답의 첫 항목(없으면 answer_text 첫 줄)이 곧 주제어다. 표로 된 답은 못 쓴다
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
    return _clip(t)


# ------------------------------------------------------------------ 교재 조립

def build_textbook(cert):
    """분류별 주제 목록을 만든다. 무거우므로 10분 캐시."""
    qs_all = GisaEssayQuestion.objects.filter(certification=cert, source='기출')
    notes = list(GisaEssayNote.objects.filter(certification=cert))
    stamp = max([n.updated_at.timestamp() for n in notes] + [0])
    key = 'essay_tb:v1:%d:%d:%d' % (cert.pk, qs_all.count(), int(stamp))
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
    groups = {gid: [] for gid, _ in GisaEssayQuestion.TOPIC_CHOICES}
    groups[0] = []
    for tk, qlist in topics.items():
        rep = qlist[0]                       # 가장 최근 회차 문항
        freq = max(q.freq_rounds for q in qlist)
        rounds = sorted({(q.year, q.round) for q in qlist}, reverse=True)
        notes_ = by_key.get(tk, {})
        note = notes_.get('freq58')
        calc = notes_.get('calc')
        title = (note or calc or {}).get('title') or _title_from(rep)
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
