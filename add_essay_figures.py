# -*- coding: utf-8 -*-
"""정리 자료(freq58)와 몇몇 문항 해설에 자작 SVG 도해를 넣는다 (작게, 폭 360px 안팎).

- 노트 항목: 지정한 절(### …)의 끝에 <div class="q-svg"> 블록을 붙인다.
- 문항 해설(reference): [svg]…[/svg] 블록을 끝에 붙인다.
data-fig 로 표시해 두어 두 번 돌려도 다시 넣지 않는다.
"""
import django, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from gisa.models import GisaEssayNote, GisaEssayQuestion

F = "font-family=\"'Malgun Gothic','Apple SD Gothic Neo',sans-serif\" font-size=\"11\""
G, G2, OR, GR = '#1b4332', '#2d6a4f', '#a1651a', '#8b968f'

def svg(w, h, body):
    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg" %s>'
            '<rect width="%d" height="%d" fill="#fff"/>%s</svg>' % (w, h, w, h, F, w, h, body))

def arrow(x1, y1, x2, y2, color, dash='', width=2):
    return ('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" %s marker-end="url(#ah-%s)"/>'
            % (x1, y1, x2, y2, color, width, ('stroke-dasharray="%s"' % dash) if dash else '', color.strip('#')))

def defs(*colors):
    return '<defs>' + ''.join(
        '<marker id="ah-%s" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="%s"/></marker>' % (c.strip('#'), c) for c in colors) + '</defs>'

FIG = {}

# 1. Bradshaw 도식 — 구조(x)·기능(y) 좌표에서 훼손 → 복원/복구/대체
FIG['bradshaw'] = svg(360, 210, defs(G, G2, OR) +
    '<line x1="50" y1="180" x2="335" y2="180" stroke="#333" stroke-width="1.3"/><polygon points="335,180 327,176 327,184" fill="#333"/>'
    '<line x1="50" y1="180" x2="50" y2="25" stroke="#333" stroke-width="1.3"/><polygon points="50,25 46,33 54,33" fill="#333"/>'
    '<text x="195" y="200" text-anchor="middle" fill="#333">생태계의 구조 (종 구성·다양성·층위) →</text>'
    '<text x="14" y="100" text-anchor="middle" fill="#333" transform="rotate(-90 14 100)">기능 (생물량·물질순환) →</text>'
    '<circle cx="75" cy="160" r="5" fill="#c62828"/><text x="80" y="176" fill="#c62828">훼손된 생태계</text>'
    '<circle cx="300" cy="45" r="5" fill="%s"/><text x="300" y="36" text-anchor="middle" fill="%s" font-weight="700">원생태계(목표)</text>'
    % (G, G) +
    arrow(80, 156, 292, 50, G) + '<text x="168" y="70" fill="%s" font-weight="700">복원 (구조·기능 모두 회복)</text>' % G +
    arrow(80, 158, 232, 100, G2, '5 3') + '<text x="236" y="112" fill="%s" font-weight="700">복구 (원래에 근접, 미달)</text>' % G2 +
    arrow(78, 155, 138, 62, OR, '2 3') + '<text x="60" y="52" fill="%s" font-weight="700">대체 (구조는 다르나 기능 회복)</text>' % OR)

# 2. 생물권보전지역 동심원
FIG['mab'] = svg(360, 180, ''
    '<circle cx="110" cy="92" r="78" fill="#eef4ef" stroke="%s"/>'
    '<circle cx="110" cy="92" r="54" fill="#cfe1d5" stroke="%s"/>'
    '<circle cx="110" cy="92" r="30" fill="%s"/>'
    '<text x="110" y="96" text-anchor="middle" fill="#fff" font-weight="700">핵심</text>'
    '<text x="110" y="52" text-anchor="middle" fill="%s" font-weight="700">완충</text>'
    '<text x="110" y="28" text-anchor="middle" fill="%s" font-weight="700">전이(협력)</text>'
    '<text x="205" y="60" fill="%s" font-weight="700">핵심구역</text><text x="205" y="74" fill="#444">엄격 보호 · 조사 이외 행위 제한</text>'
    '<text x="205" y="100" fill="%s" font-weight="700">완충구역</text><text x="205" y="114" fill="#444">핵심을 감싸 충격 흡수 · 교육·연구</text>'
    '<text x="205" y="140" fill="%s" font-weight="700">전이(협력)구역</text><text x="205" y="154" fill="#444">주민 거주 · 지속가능한 이용</text>'
    % (G2, G2, G, G, G2, G, G2, GR))

# 3. 미티게이션 회피·저감·대체
def _panel(x, label, sub, road, core_alpha='1', extra=''):
    return ('<rect x="%d" y="18" width="100" height="88" rx="6" fill="#e3efe6" stroke="%s"/>'
            '<circle cx="%d" cy="60" r="20" fill="%s" opacity="%s"/>%s%s'
            '<text x="%d" y="124" text-anchor="middle" fill="#333" font-weight="700">%s</text>'
            '<text x="%d" y="137" text-anchor="middle" fill="#666" font-size="9">%s</text>'
            % (x, G2, x + 50, G, core_alpha, road, extra, x + 50, label, x + 50, sub))
FIG['mitigation'] = svg(360, 146, ''
    + _panel(10, '회피', '노선을 돌려 훼손을 피함', '<path d="M10 95 Q60 95 60 45 Q60 22 110 22" fill="none" stroke="#555" stroke-width="4"/>')
    + _panel(130, '저감(최소화)', '다리·터널·생태통로로 통과', '<line x1="130" y1="60" x2="230" y2="60" stroke="#555" stroke-width="4" stroke-dasharray="8 5"/>'
             '<text x="180" y="92" text-anchor="middle" fill="%s" font-size="9" font-weight="700">생태통로</text>' % G)
    + _panel(250, '대체', '다른 곳에 대체서식지 조성', '<line x1="250" y1="60" x2="350" y2="60" stroke="#555" stroke-width="4"/>', '0.35',
             '<circle cx="322" cy="36" r="12" fill="%s"/><text x="322" y="22" text-anchor="middle" fill="%s" font-size="9" font-weight="700">대체서식지</text>' % (OR, OR)))

# 4. 생태네트워크 모식도
FIG['econet'] = svg(360, 170, ''
    '<path d="M70 90 Q180 60 290 95" fill="none" stroke="#9fcfae" stroke-width="16" stroke-linecap="round"/>'
    '<path d="M70 90 Q180 60 290 95" fill="none" stroke="%s" stroke-width="3" stroke-dasharray="6 5"/>'
    '<circle cx="70" cy="90" r="42" fill="#cfe1d5" stroke="%s"/><circle cx="70" cy="90" r="24" fill="%s"/>'
    '<circle cx="290" cy="95" r="42" fill="#cfe1d5" stroke="%s"/><circle cx="290" cy="95" r="24" fill="%s"/>'
    '<circle cx="180" cy="72" r="11" fill="%s"/>'
    '<text x="70" y="94" text-anchor="middle" fill="#fff" font-weight="700">핵심</text>'
    '<text x="290" y="99" text-anchor="middle" fill="#fff" font-weight="700">핵심</text>'
    '<text x="70" y="146" text-anchor="middle" fill="%s">완충지역(둘레)</text>'
    '<text x="290" y="151" text-anchor="middle" fill="%s">완충지역(둘레)</text>'
    '<text x="180" y="52" text-anchor="middle" fill="%s" font-weight="700">거점(징검다리)</text>'
    '<text x="180" y="118" text-anchor="middle" fill="%s" font-weight="700">코리더(생태통로)로 연결</text>'
    % (G2, G2, G, G2, G, OR, G2, G2, OR, G2))

# 5. 하천차수도 (Strahler)
FIG['stream'] = svg(360, 170, ''
    '<g stroke="%s" stroke-linecap="round" fill="none">'
    '<path d="M40 30 L90 70" stroke-width="2"/><path d="M120 22 L90 70" stroke-width="2"/>'
    '<path d="M90 70 L140 110" stroke-width="3.5"/><path d="M175 60 L140 110" stroke-width="2"/>'
    '<path d="M140 110 L190 140" stroke-width="3.5"/>'
    '<path d="M260 40 L235 75" stroke-width="2"/><path d="M215 42 L235 75" stroke-width="2"/>'
    '<path d="M235 75 L210 115" stroke-width="3.5"/><path d="M210 115 L190 140" stroke-width="3.5"/>'
    '<path d="M190 140 L200 165" stroke-width="5.5"/></g>'
    '<g fill="#fff" stroke="%s"><circle cx="60" cy="42" r="8"/><circle cx="110" cy="38" r="8"/><circle cx="160" cy="78" r="8"/>'
    '<circle cx="250" cy="52" r="8"/><circle cx="222" cy="52" r="8"/><circle cx="118" cy="92" r="8"/><circle cx="226" cy="98" r="8"/>'
    '<circle cx="168" cy="130" r="8"/><circle cx="210" cy="158" r="8"/></g>'
    '<g fill="%s" font-size="10" font-weight="700" text-anchor="middle">'
    '<text x="60" y="46">1</text><text x="110" y="42">1</text><text x="160" y="82">1</text><text x="250" y="56">1</text><text x="222" y="56">1</text>'
    '<text x="118" y="96">2</text><text x="226" y="102">2</text><text x="168" y="134">2</text><text x="210" y="162">3</text></g>'
    '<text x="262" y="120" fill="#444">1차 + 1차 → 2차</text><text x="262" y="136" fill="#444">2차 + 1차 → 2차</text>'
    '<text x="262" y="152" fill="#444" font-weight="700">2차 + 2차 → 3차</text>'
    % (G2, G2, G))

# 6. 클레멘츠 천이계열 순서
_stages = ['나지', '지의류·선태류', '초원', '관목림', '양수림', '혼합림', '음수림(극상)']
_x, parts = 6, []
for i, s in enumerate(_stages):
    w = 30 + 8 * len(s)
    last = i == len(_stages) - 1
    parts.append('<rect x="%d" y="14" width="%d" height="26" rx="6" fill="%s" stroke="%s"/>'
                 '<text x="%d" y="31" text-anchor="middle" fill="%s" font-size="10" font-weight="700">%s</text>'
                 % (_x, w, G if last else '#eef4ef', G2, _x + w / 2, '#fff' if last else G, s))
    _x += w
    if not last:
        parts.append('<text x="%d" y="31" text-anchor="middle" fill="%s" font-size="12">→</text>' % (_x + 7, OR)); _x += 14
FIG['clements'] = svg(_x + 6, 54, ''.join(parts))

# 7. 환경수용력 로지스틱 곡선
FIG['carrying'] = svg(360, 170, ''
    '<line x1="45" y1="140" x2="335" y2="140" stroke="#333" stroke-width="1.3"/><polygon points="335,140 327,136 327,144" fill="#333"/>'
    '<line x1="45" y1="140" x2="45" y2="20" stroke="#333" stroke-width="1.3"/><polygon points="45,20 41,28 49,28" fill="#333"/>'
    '<text x="190" y="160" text-anchor="middle" fill="#333">시간 →</text>'
    '<text x="14" y="85" text-anchor="middle" fill="#333" transform="rotate(-90 14 85)">개체수 →</text>'
    '<line x1="45" y1="45" x2="335" y2="45" stroke="%s" stroke-width="1.5" stroke-dasharray="6 4"/>'
    '<text x="330" y="39" text-anchor="end" fill="%s" font-weight="700">K = 환경수용력 (부양 가능한 최대 개체수)</text>'
    '<path d="M50 135 C 130 132, 150 60, 210 50 S 300 45, 330 45" fill="none" stroke="%s" stroke-width="3"/>'
    '<text x="120" y="122" fill="%s">지수 성장</text>'
    '<text x="190" y="100" fill="%s">환경저항 증가 → 성장 둔화</text>'
    '<text x="240" y="68" fill="%s">K 근처에서 평형</text>'
    % (OR, OR, G, G2, G2, G2))

# 8. 종-면적 관계
FIG['species_area'] = svg(360, 160, ''
    '<line x1="45" y1="130" x2="335" y2="130" stroke="#333" stroke-width="1.3"/><polygon points="335,130 327,126 327,134" fill="#333"/>'
    '<line x1="45" y1="130" x2="45" y2="20" stroke="#333" stroke-width="1.3"/><polygon points="45,20 41,28 49,28" fill="#333"/>'
    '<text x="300" y="150" text-anchor="middle" fill="#333">서식지 면적 A →</text>'
    '<text x="14" y="78" text-anchor="middle" fill="#333" transform="rotate(-90 14 78)">종수 S →</text>'
    '<path d="M48 128 C 80 70, 150 50, 330 32" fill="none" stroke="%s" stroke-width="3"/>'
    '<text x="60" y="40" fill="%s" font-weight="700">S = C·A<tspan baseline-shift="super" font-size="8">z</tspan>  (z ≈ 0.2~0.35)</text>'
    '<line x1="120" y1="130" x2="120" y2="70" stroke="%s" stroke-dasharray="3 3"/><line x1="230" y1="130" x2="230" y2="45" stroke="%s" stroke-dasharray="3 3"/>'
    '<text x="120" y="142" text-anchor="middle" fill="%s" font-size="10">100ha</text><text x="230" y="142" text-anchor="middle" fill="%s" font-size="10">1,000ha</text>'
    '<text x="150" y="112" fill="#444" font-size="10">면적 10배 → 종수 약 2배 (완만한 증가)</text>'
    % (G, G, OR, OR, OR, OR))

# 9. 서식지 단편화 과정 5단계
def _frag(x, label, inner):
    return ('<rect x="%d" y="16" width="60" height="50" rx="3" fill="#cfe1d5" stroke="%s"/>%s'
            '<text x="%d" y="90" text-anchor="middle" fill="#333" font-size="10" font-weight="700">%s</text>' % (x, G2, inner, x + 30, label))
FIG['fragment'] = svg(380, 100, ''
    + _frag(6, '천공', '<circle cx="36" cy="41" r="7" fill="#fff"/>')
    + _frag(82, '절단', '<line x1="82" y1="41" x2="142" y2="41" stroke="#fff" stroke-width="5"/>')
    + _frag(158, '단편화', '<line x1="158" y1="41" x2="218" y2="41" stroke="#fff" stroke-width="6"/><line x1="188" y1="16" x2="188" y2="66" stroke="#fff" stroke-width="6"/>')
    + '<rect x="234" y="16" width="60" height="50" rx="3" fill="#fff" stroke="%s"/>' % G2
    + '<rect x="240" y="22" width="18" height="14" fill="#cfe1d5"/><rect x="270" y="24" width="14" height="12" fill="#cfe1d5"/><rect x="243" y="46" width="14" height="12" fill="#cfe1d5"/><rect x="272" y="48" width="12" height="10" fill="#cfe1d5"/>'
    + '<text x="264" y="90" text-anchor="middle" fill="#333" font-size="10" font-weight="700">축소</text>'
    + '<rect x="310" y="16" width="60" height="50" rx="3" fill="#fff" stroke="%s"/><rect x="332" y="34" width="10" height="9" fill="#cfe1d5"/>' % G2
    + '<text x="340" y="90" text-anchor="middle" fill="#333" font-size="10" font-weight="700">소멸</text>'
    + ''.join('<text x="%d" y="45" text-anchor="middle" fill="%s" font-size="12">→</text>' % (x, OR) for x in (74, 150, 226, 302)))

# 10. SLOSS
FIG['sloss'] = svg(360, 130, (
    '<rect x="30" y="18" width="84" height="84" fill="#cfe1d5" stroke="%s"/><rect x="48" y="36" width="48" height="48" fill="%s" opacity="0.85"/>'
    '<text x="72" y="118" text-anchor="middle" fill="#333" font-weight="700">Single Large</text>'
    '<text x="72" y="12" text-anchor="middle" fill="%s" font-size="10">내부(핵심) 면적이 넓다</text>' % (G2, G, G2))
    + ''.join('<rect x="%d" y="%d" width="42" height="42" fill="#cfe1d5" stroke="%s"/><rect x="%d" y="%d" width="14" height="14" fill="%s" opacity="0.85"/>'
              % (x, y, G2, x + 14, y + 14, G) for x, y in ((190, 18), (250, 18), (190, 68), (250, 68)))
    + ('<text x="241" y="122" text-anchor="middle" fill="#333" font-weight="700">Several Small</text>'
       '<text x="241" y="12" text-anchor="middle" fill="%s" font-size="10">가장자리가 많고 위험이 분산된다</text>'
       '<text x="150" y="64" text-anchor="middle" fill="#444" font-size="10">총면적</text><text x="150" y="76" text-anchor="middle" fill="#444" font-size="10">같음</text>'
       '<text x="306" y="66" fill="#444" font-size="9">■ 내부</text><text x="306" y="80" fill="#444" font-size="9">□ 가장자리</text>' % G2))

# 11. 경성/연성 경계
FIG['edge'] = svg(360, 120, ''
    '<rect x="16" y="14" width="70" height="70" fill="%s"/><rect x="86" y="14" width="70" height="70" fill="#f1e7c9"/>'
    '<line x1="86" y1="14" x2="86" y2="84" stroke="#333" stroke-width="2"/>'
    '<text x="86" y="102" text-anchor="middle" fill="#333" font-weight="700">경성 경계</text><text x="86" y="115" text-anchor="middle" fill="#666" font-size="10">직선 · 대비 큼 · 급변 (시멘트 호안)</text>'
    '<rect x="200" y="14" width="140" height="70" fill="#f1e7c9"/>'
    '<path d="M200 14 L250 14 Q262 30 250 44 Q238 58 256 70 Q266 78 250 84 L200 84 Z" fill="%s"/>'
    '<path d="M250 14 Q262 30 250 44 Q238 58 256 70 Q266 78 250 84 L268 84 Q280 74 268 62 Q256 50 274 36 Q282 26 268 14 Z" fill="%s" opacity="0.55"/>'
    '<path d="M268 14 Q282 26 274 36 Q256 50 268 62 Q280 74 268 84 L286 84 Q296 70 286 56 Q276 44 292 30 Q298 22 286 14 Z" fill="%s" opacity="0.3"/>'
    '<text x="270" y="102" text-anchor="middle" fill="#333" font-weight="700">연성 경계</text><text x="270" y="115" text-anchor="middle" fill="#666" font-size="10">곡선 · 점진적 이행 (자연 수변)</text>'
    % (G2, G2, G2, G2))

# 12. 깔때기 효과
FIG['funnel'] = svg(360, 150, defs(OR) + (
    '<path d="M20 20 L150 20 L150 55 L300 68 L300 82 L150 95 L150 130 L20 130 Z" fill="#cfe1d5" stroke="%s"/>'
    '<text x="85" y="78" text-anchor="middle" fill="%s" font-weight="700">경관 조각(patch)</text>'
    '<text x="225" y="52" text-anchor="middle" fill="%s" font-weight="700">돌출부(반도형)</text>' % (G2, G, OR))
    + arrow(60, 38, 150, 66, OR) + arrow(60, 112, 150, 84, OR) + arrow(160, 75, 295, 75, OR, '', 3)
    + '<text x="325" y="79" fill="#444" font-size="10">이동이</text><text x="325" y="91" fill="#444" font-size="10">한곳에 모임</text>')

# 13. 다차원 부피모형
FIG['niche'] = svg(360, 190, ''
    '<g stroke="#333" stroke-width="1.3" fill="none"><line x1="60" y1="150" x2="290" y2="150"/><line x1="60" y1="150" x2="60" y2="30"/><line x1="60" y1="150" x2="130" y2="100"/></g>'
    '<polygon points="290,150 282,146 282,154" fill="#333"/><polygon points="60,30 56,38 64,38" fill="#333"/><polygon points="130,100 121,102 127,108" fill="#333"/>'
    '<text x="300" y="154" fill="#333">온도</text><text x="60" y="22" text-anchor="middle" fill="#333">습도</text><text x="138" y="98" fill="#333">먹이 크기</text>'
    '<ellipse cx="180" cy="92" rx="72" ry="42" fill="#cfe1d5" stroke="%s" stroke-dasharray="5 3"/>'
    '<ellipse cx="192" cy="98" rx="38" ry="24" fill="%s" opacity="0.85"/>'
    '<text x="258" y="60" fill="%s" font-weight="700">기본지위</text><text x="258" y="73" fill="#555" font-size="10">경쟁 없을 때 차지할 수 있는</text><text x="258" y="85" fill="#555" font-size="10">n차원 초부피</text>'
    '<text x="192" y="102" text-anchor="middle" fill="#fff" font-weight="700">실현지위</text>'
    '<text x="120" y="176" fill="#555" font-size="10">각 축 = 환경요인 하나 · 축이 n개면 n차원 초부피</text>'
    % (G2, G, G2))

# 14. 조류와 인간 사이의 거리
FIG['bird_dist'] = svg(360, 140, (
    '<line x1="40" y1="80" x2="330" y2="80" stroke="#bbb" stroke-width="1.2"/>'
    '<circle cx="40" cy="74" r="9" fill="%s"/><polygon points="49,74 62,70 49,80" fill="%s"/><text x="40" y="100" text-anchor="middle" fill="%s" font-weight="700">조류</text>'
    '<circle cx="330" cy="62" r="6" fill="#555"/><line x1="330" y1="68" x2="330" y2="86" stroke="#555" stroke-width="3"/><line x1="322" y1="94" x2="330" y2="86" stroke="#555" stroke-width="3"/><line x1="338" y1="94" x2="330" y2="86" stroke="#555" stroke-width="3"/>'
    '<text x="330" y="110" text-anchor="middle" fill="#555" font-weight="700">사람 접근 →</text>' % (G, G, G))
    + ''.join('<line x1="%d" y1="70" x2="%d" y2="90" stroke="%s" stroke-width="2"/><text x="%d" y="%d" text-anchor="middle" fill="%s" font-weight="700" font-size="10">%s</text><text x="%d" y="%d" text-anchor="middle" fill="#666" font-size="9">%s</text>'
              % (x, x, c, x, 58 if i % 2 == 0 else 32, c, lab, x, 68 if i % 2 == 0 else 42, sub)
              for i, (x, lab, sub, c) in enumerate((
                  (90, '도피거리', '날아 도피', '#c62828'), (160, '회피거리', '걷거나 뛰어 피함', OR),
                  (230, '경계거리', '고개 들고 경계', G2), (298, '비간섭거리', '하던 행동 계속', GR))))
    + '<text x="185" y="130" text-anchor="middle" fill="#444" font-size="10">← 조류에 가까울수록 반응이 강해진다 (비간섭 → 경계 → 회피 → 도피)</text>')

# 15. 생태통로 육교형·터널형 단면
FIG['ecoduct'] = svg(360, 130, ''
    '<rect x="10" y="80" width="160" height="14" fill="#555"/><text x="90" y="91" text-anchor="middle" fill="#fff" font-size="9">도로</text>'
    '<path d="M30 80 Q90 20 150 80" fill="none" stroke="%s" stroke-width="10"/><path d="M34 74 Q90 24 146 74" fill="none" stroke="#cfe1d5" stroke-width="5"/>'
    '<text x="90" y="112" text-anchor="middle" fill="#333" font-weight="700">육교형(Overpass)</text><text x="90" y="124" text-anchor="middle" fill="#666" font-size="9">절토부 — 도로 위로 잇는다</text>'
    '<polygon points="190,90 240,40 300,40 350,90" fill="#cfe1d5" stroke="%s"/><rect x="240" y="36" width="60" height="8" fill="#555"/><text x="270" y="30" text-anchor="middle" fill="#333" font-size="9">도로(성토부)</text>'
    '<rect x="252" y="62" width="36" height="28" fill="#fff" stroke="%s" stroke-width="2"/><text x="270" y="80" text-anchor="middle" fill="%s" font-size="9" font-weight="700">터널</text>'
    '<text x="270" y="112" text-anchor="middle" fill="#333" font-weight="700">터널형(Underpass)</text><text x="270" y="124" text-anchor="middle" fill="#666" font-size="9">성토부·평지 — 도로 아래로 지난다</text>'
    % (G2, G2, G2, G))

# ------------------------------------------------------------------ 삽입
NOTE_PLAN = [   # (항목 제목, 절 제목 앞부분, 그림 키)
    ('복원·복구·대체', '### 그래프(Bradshaw 도식)', 'bradshaw'),
    ('유네스코 MAB 생물권보전지역', '### 공간 3구획과 허용 행위', 'mab'),
    ('미티게이션 회피·저감·대체', '### 정의', 'mitigation'),
    ('생태네트워크 구성요소', '### 정의', 'econet'),
    ('하천차수도', '### 정의', 'stream'),
    ('클레멘츠 천이계열 순서', '### 정의', 'clements'),
    ('환경수용력(carrying capacity)', '### 정의', 'carrying'),
    ('서식지 파편화의 정의', '### 정의', 'fragment'),
    ('SLOSS 논쟁', '### 정의', 'sloss'),
    ('생태적 지위 다차원 부피모형', '### 정의', 'niche'),
    ('조류와 인간 사이의 거리', '### 정의', 'bird_dist'),
]
Q_PLAN = [      # (연도, 회차, 번호, 그림 키) — 해설(reference) 끝에
    (2012, 2, 5, 'species_area'), (2024, 2, 4, 'edge'), (2020, 3, 4, 'funnel'), (2023, 1, 7, 'ecoduct'),
]

n = GisaEssayNote.objects.get(slug='freq58')
# 같은 키의 그림이 이미 있으면 걷어내고 새로 넣는다 (다시 그려 돌릴 때)
for _, _, key in NOTE_PLAN:
    n.content = re.sub(r'\n?<div class="q-svg" data-fig="%s">.*?</div>\n?' % key, '\n', n.content, flags=re.S)
groups = '|'.join(re.escape(g) for _, g in GisaEssayQuestion.TOPIC_CHOICES)
parts = re.split(r'^(## \d+회 · (?:%s) · .+)$' % groups, n.content, flags=re.M)
done = []
for title, sec, key in NOTE_PLAN:
    block = '\n<div class="q-svg" data-fig="%s">\n%s\n</div>\n' % (key, FIG[key])
    for i in range(1, len(parts), 2):
        if parts[i].split(' · ', 2)[2].strip() != title:
            continue
        body = parts[i + 1]
        m = re.search(r'^' + re.escape(sec) + r'.*$', body, flags=re.M)
        if not m:
            done.append((title, '!! 절 없음 ' + sec)); break
        end = re.search(r'\n(?=### |---\s*$)', body[m.end():])
        pos = m.end() + (end.start() if end else len(body[m.end():]))
        parts[i + 1] = body[:pos].rstrip('\n') + '\n' + block + body[pos:]
        done.append((title, 'OK')); break
    else:
        done.append((title, '!! 항목 없음'))
new = ''.join(parts)
if new != n.content:
    n.content = new; n.save()
for t, s in done: print('  노트', s, '|', t)

for y, r, num, key in Q_PLAN:
    q = GisaEssayQuestion.objects.filter(source='기출', year=y, round=r, number=num).first()
    if not q:
        print('  문항 !! 없음', y, r, num); continue
    ref = re.sub(r'\s*\[svg\]<svg data-fig="%s".*?\[/svg\]' % key, '', q.reference or '', flags=re.S)
    q.reference = ref.rstrip() + '\n\n[svg]%s[/svg]' % FIG[key].replace('<svg ', '<svg data-fig="%s" ' % key, 1)
    q.save(update_fields=['reference'])
    print('  문항 OK %d-%d #%d (%s)' % (y, r, num, key))
print('노트 svg 수:', GisaEssayNote.objects.get(slug='freq58').content.count('<svg'))
