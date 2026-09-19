# -*- coding: utf-8 -*-
"""방송대 기출 화면용 필터.

`sciname` — 학명(이명법)을 이탤릭으로. 쪽집게 노트 관련 문제 카드의 `_nqSci`
(templates/main/subject_detail.html)와 **같은 규칙**이다. 한쪽만 고치면 같은 해설이
화면마다 다르게 보이므로 둘을 함께 고칠 것.
"""
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# 속명 + 종소명만 이탤릭이고 **명명자(L. · P. BEAUV. · Ohwi)와 계급 표기(var. · subsp. · f.)는
# 정자**다. 속명을 '대문자 + 소문자 둘 이상'으로 잡아 IUCN·LAI 같은 약어를 걸러내고,
# 'Bordeaux mixture' 처럼 영어 두 낱말이 걸리는 것은 뒷말 불용어로 막는다.
_NOT_SP = re.compile(
    r'^(mixture|method|methods|model|models|test|tests|index|value|values|effect|effects'
    r'|law|laws|code|chart|charts|scale|cycle|curve|curves|point|points|line|lines|class'
    r'|classes|type|types|group|groups|level|levels|unit|units|table|tables|list|lists|form'
    r'|forms|rate|rates|area|areas|zone|zones|site|sites|acid|water|number|numbers|factor'
    r'|factors|system|systems|process|theory|series|phase|state|stage|score|range|ratio'
    r'|color|colour|paper|plate|filter|buffer|medium|agar|broth|and|or|of|in|on|for|with'
    r'|the|a|an)$')
_BINOM = re.compile(r'(^|[^A-Za-z<>/])([A-Z][a-z]{2,})\s+([a-z][a-z-]{2,})(?![A-Za-z])')
_RANK = re.compile(r'\b(var|subsp|ssp|f|cv)\.\s+([a-z][a-z-]{2,})(?![A-Za-z])')


def _binom(m):
    return m.group(0) if _NOT_SP.match(m.group(3)) else \
        '%s<i>%s %s</i>' % (m.group(1), m.group(2), m.group(3))


def _rank(m):
    return m.group(0) if _NOT_SP.match(m.group(2)) else '%s. <i>%s</i>' % (m.group(1), m.group(2))


@register.filter
def sciname(value):
    """학명을 <i> 로 감싼다. **이스케이프한 뒤** 태그를 넣으므로 안전하다."""
    if not value:
        return ''
    out = escape(value)
    out = _BINOM.sub(_binom, out)
    out = _RANK.sub(_rank, out)
    return mark_safe(out)
