# -*- coding: utf-8 -*-
"""
Generate per-chapter JSON files (_fl_ch1.json through _fl_ch12.json)
from _fl_all.json using the classification logic.

Chapter Structure (숲과삶):
  1. 산림의 개념과 분류
  2. 숲의 기능과 가치
  3. 산림 생태계와 천이
  4. 수목의 생리와 환경
  5. 야생동물과 서식지
  6. 숲과 전통문화
  7. 목재와 임산물
  8. 조림과 숲 가꾸기
  9. 도시숲과 녹지
 10. 산림 휴양과 치유
 11. 기후변화와 국제 협력
 12. 산림 정책과 보호지역
"""
import json, sys, os

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, '_fl_all.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

def combined(q):
    return ' '.join([
        q.get('text',''), q.get('choice_1',''), q.get('choice_2',''),
        q.get('choice_3',''), q.get('choice_4',''), q.get('explanation','')
    ])

def classify(idx, q):
    t = q['text']  # question text only (most reliable for topic)
    c = combined(q)  # all text combined (for secondary matching)

    # ============================================================
    # TIER 1: High-specificity matches on QUESTION TEXT
    # These topics have very distinctive keywords in the question itself
    # ============================================================

    # --- Ch 10: 산림 휴양과 치유 ---
    if any(kw in t for kw in [
        '휴양림', '자연휴양림',
        '숲치유', '산림치유', '산림요양', '테르펜', '피톤치드',
        '숲해설', '환경수용력',
        '치유의 숲', '정유를 활용',
        '식물치유', '기후치유', '식이치유',
        '숲치유의 6대', '치유의 6대',
    ]):
        return 10
    # Extra: combined check for therapy
    if any(kw in c for kw in ['아로마테라피', '산림레크리에이션']):
        return 10
    # '건강을 증진' + 숲 = 산림치유
    if '건강을 증진' in t and '숲' in c:
        return 10

    # --- Ch 6: 숲과 전통문화 ---
    # Check BEFORE Ch 3/Ch 12 to avoid false matches on 생태계서비스/백두대간 in choices
    if any(kw in t for kw in [
        '마을숲', '마을 숲',
        '전통문화', '숲과 전통',
        '십장생', '비단벌레', '금관총', '옥충',
        '숲의 중요성',
        '임수제도', '봉산',
    ]):
        return 6
    # 소나무/두루미 in 전통문화 context (special pattern)
    if '소나무를 비롯한 해' in t:
        return 6
    if '신라' in t and ('금관총' in c or '비단벌레' in c or '마구 장식' in c):
        return 6
    # 나무와 인간 설명
    if '나무와 인간' in t:
        return 6

    # --- Ch 1: 산림의 개념과 분류 ---
    # Check BEFORE Ch 7 to prevent 경제림/목재자원 false positives
    if any(kw in t for kw in [
        '숲의 종류', '숲의 구분', '임상별',
        '난대림', '수림대', '경제림',
        '숲에 대한 용어',
        '해외의 숲', '산림 현황',
        '보안림',
    ]):
        return 1
    if '기후분포에 따라 숲' in t or '기후분포 수림대' in t:
        return 1
    if any(kw in t for kw in ['산림면적', '산림비율', '산림의 소유', '소유자별', '소유별']):
        return 1
    if any(kw in t for kw in ['산림의 25%', '지구산림', '지구 산림', '국토대비', '목재자원']):
        return 1
    if '대륙' in t and ('산림' in t or '분포' in t or '점유' in t):
        return 1
    if '임목축적' in t and ('대륙' in t or '높은' in t):
        return 1
    if any(kw in t for kw in ['침엽수림에 해당', '침엽수림', '숲에 관한 설명']):
        return 1
    if '산림자원의 조성' in t or '숲의 기능을 구분' in t:
        return 1
    if '숲의 피복상태' in t or '피복상태' in t:
        return 1

    # ============================================================
    # TIER 2: Policy & Protected Areas
    # ============================================================

    # --- Ch 12: 산림 정책과 보호지역 ---
    # Use question text to avoid false matches from choices mentioning 백두대간 etc.
    if any(kw in t for kw in [
        '자연보호지역', '자연공원', '용도지구',
        '특별보호구', '백두대간', '국립공원',
        '산림보호법', '보호구역',
    ]):
        return 12
    # IUCN in question or combined (very specific)
    if 'IUCN' in t or 'iucn' in t:
        return 12

    # --- Ch 11: 기후변화와 국제 협력 ---
    if any(kw in t for kw in [
        'CITES', 'cites', '멸종위기에 처한',
        '교토의정서', '교토 의정서', '기후변화협약',
        '탄소배출권', '배출권거래', '공동이행제도', '청정개발',
    ]):
        return 11
    if any(kw in c for kw in [
        'CBD', 'IPBES', 'ipbes',
        '람사', '나고야',
        '생물권보전지역', '양허성',
        '생물다양성협약', '생물다양성 협약',
        '신규조림',
        'OECD', 'oecd',
    ]):
        return 11
    # 온실가스/온난화 (question text)
    if any(kw in t for kw in [
        '온실가스', '온난화', '이산화탄소',
        '지구온난화', '지구 온난화',
    ]):
        return 11
    # 기후변화 (text)
    if '기후변화' in t:
        return 11
    # 생물다양성 협약이행 (text)
    if '생물다양성' in t and '협약' in c:
        return 11

    # ============================================================
    # TIER 3: Urban/Recreation infrastructure
    # ============================================================

    # --- Ch 9: 도시숲과 녹지 ---
    if any(kw in t for kw in [
        '가로수', '학교숲', '수목원',
        '도시공원', '어린이공원', '근린공원', '소공원', '주제공원',
        '생활권공원', '생활권 공원',
        '시설녹지', '완충녹지', '경관녹지', '연결녹지',
        '녹지활용계약', '녹지활용',
        '공개공지', '개발제한구역',
        '내셔널 트러스트', '내셔널트러스트',
    ]):
        return 9
    # 녹지 관리/조성
    if '녹지' in t and ('관리' in t or '조성' in t or '보전' in t):
        return 9

    # --- Ch 8: 조림과 숲 가꾸기 ---
    if any(kw in t for kw in [
        '숲길', '등산로', '탐방로',
        '노면침식', 'U자', 'V자',
        '답압', '숲길 훼손', '숲길 복원',
        '숲길관리', '숲길 관리',
        '지형복원',
        '숲 가꾸기', '숲가꾸기', '솎아베기', '풀베기', '덩굴',
        '가지치기', '어린나무', '조림후', '조림 후', '조림을 하고',
        '조림한', '시민참여',
        '미래목', '형질불량목', '작업공정',
    ]):
        return 8
    # Combined: specific forestry terms
    if any(kw in c for kw in ['조밀하게 심', '인공림의 숲']):
        return 8
    # 보행에 의한 피해 → 숲길 답압
    if '보행' in t and ('딱딱' in c or '다져' in c):
        return 8

    # ============================================================
    # TIER 4: Resources and Products
    # ============================================================

    # --- Ch 7: 목재와 임산물 ---
    if any(kw in t for kw in [
        '종이에 관한', '제지 기술', '제지기술',
        '버섯', '표고', '영지',
        '바이오매스', '바이오에너지',
        '임목축적', '산림자산', '재적',
    ]):
        return 7
    if any(kw in c for kw in ['파피루스', '목재펄프', '목질 펠릿', '우드칩', '목재폐재']):
        return 7
    if any(kw in t for kw in ['생활도구', '나무로 만들']):
        return 7
    if any(kw in c for kw in ['칫솔대', '젓가락']):
        return 7
    # 석탄/석유 대체 에너지원 from wood
    if '에너지' in t and ('목재' in t or '줄기' in t or '수목' in t):
        return 7
    # 원목으로 사용하여 → 임산물
    if '원목' in t and ('버섯' in c or '재배' in c):
        return 7

    # ============================================================
    # TIER 5: Ecology and Biology
    # ============================================================

    # --- Ch 4: 수목의 생리와 환경 ---
    if any(kw in t for kw in [
        '광합성', '광보상점', '광포화점', '광주기', '광한계점',
        '수목한계선', '수목 한계선',
    ]):
        return 4
    if '고산지역' in t and '식물' in t:
        return 4
    if '고산지대' in t and ('교목' in t or '수목' in t or '요인' in t or '요소' in t):
        return 4
    if any(kw in t for kw in [
        '이산화황', '이산화질소', '대기오염',
        '산림쇠퇴', '쇠퇴 현상', '쇠퇴현상',
        '수목에 대한 설명', '수목의 명칭',
        '후진국형',
    ]):
        return 4
    if any(kw in c for kw in ['토양을 구성', '토양 입자', '입자의 크기']):
        return 4
    if '척박한' in t and '토양' in c:
        return 4
    # 나무 식별/종류
    if any(kw in t for kw in ['은행나무', '느티나무', '용문사', '마의태자', '진기한 나무', '참나무']):
        return 4
    # 수목의 대기정화 (SO2/NO2 흡수) → Ch 4 (not Ch 2)
    if '수목의 대기정화' in t or '대기정화에 대한' in t:
        return 4
    # SO2/NO2 흡수량 임상별
    if '흡수량' in t and ('이산화황' in c or '이산화질소' in c):
        return 4
    # 원형질, 환경요인 → 생리
    if '원형질' in t:
        return 4

    # --- Ch 2: 숲의 기능과 가치 ---
    if any(kw in t for kw in [
        '녹색댐', '수원함양', '토사유출',
        '대기정화', '대기흡착', '대기 흡착',
    ]):
        return 2
    if any(kw in c for kw in [
        '빗물 침투', '빗물이 침투',
        '홍수조절', '갈수완화', '표면유출',
    ]):
        return 2
    if '숲의 기능' in t or '숲의 효과' in t or '산림의 기능' in t:
        return 2
    if '투자수익률' in c or '산림의 가치' in c or '산림공익' in c:
        return 2
    if '빗물을 머금' in c:
        return 2
    if '빗물' in t and '침투' in c:
        return 2

    # --- Ch 3: 산림 생태계와 천이 ---
    if any(kw in t for kw in [
        '천이', '극상림', '극상', '개척자', '선구종',
        '분해자', '생태계서비스', '생태계 서비스',
        '새천년 생태계', '생태형', '생육형',
        '생물다양성',
    ]):
        return 3
    # Combined fallback for ecology
    if any(kw in c for kw in ['천이', '극상']):
        return 3

    # --- Ch 5: 야생동물과 서식지 ---
    if any(kw in t for kw in [
        '야생동물', '야생조류', '필드 마크', '필드마크',
        '새를 관찰', '반려동물', '포호', '매사냥',
        '나무구멍', '나무 구멍',
        '서식지', '습원', '비무장지대',
    ]):
        return 5
    # 둥지 in question text
    if '둥지' in t:
        return 5
    # 조류 in question text (birds, not tides)
    if '조류' in t and ('새' in c or '둥지' in c or '새를' in c or '야생' in c):
        return 5
    if any(kw in c for kw in ['DMZ', '고위평탄면', '정주공간']):
        return 5
    if '하천' in c and ('생물' in c or '통로' in c or '유입' in c):
        return 5
    # wildlife
    if 'wildlife' in c:
        return 5
    # 야생동물 관련 (combined fallback)
    if '야생동물' in c:
        return 5

    # ============================================================
    # TIER 6: Fallback checks using choices/explanation
    # For questions where the topic keyword only appears in choices
    # ============================================================

    # Choices text (without explanation to reduce noise)
    choices = ' '.join([q.get('choice_1',''), q.get('choice_2',''),
                        q.get('choice_3',''), q.get('choice_4','')])

    # 쇠퇴현상 in choices → Ch 4
    if '쇠퇴' in choices and ('숲' in t or '활력' in t):
        return 4

    # 봉산 in choices (조선시대 산림제도) → Ch 6
    if '봉산' in choices and ('조선' in t or '천연림' in t or '제도' in t):
        return 6

    # 멸종위기 / CITES context (부속서) → Ch 11
    if '부속서' in t or ('멸종' in t and '국제' in t):
        return 11

    # 내셔널트러스트 in choices → Ch 9
    if '내셔널트러스트' in choices or '내셔널 트러스트' in choices:
        return 9

    # 생태형 in choices → Ch 3
    if '생태형' in choices and ('적응' in t or '환경' in t):
        return 3

    # 참나무/도토리 in choices → Ch 4 (tree identification)
    if ('참나무' in choices or '은행나무' in choices) and '나무' in t:
        return 4

    # 국립공원 in choices → Ch 12
    if '국립공원' in choices and ('지정' in t or '환경부' in t or '자연생태계' in t):
        return 12

    # 근린공원/어린이공원 in choices → Ch 9
    if any(kw in choices for kw in ['근린공원', '어린이공원', '소공원', '역사공원']):
        if '공원' in t or '거주자' in t:
            return 9

    # ============================================================
    # LAST RESORT: remaining Ch 1 patterns from combined text
    # ============================================================
    if any(kw in c for kw in [
        '온대림', '한대림', '냉온대', '난온대', '열대우림',
        '활엽수림', '혼효림', '혼합림',
    ]):
        return 1

    # ============================================================
    # Fallback
    # ============================================================
    return 0


# Chapter titles
chapter_titles = {
    1: '산림의 개념과 분류',
    2: '숲의 기능과 가치',
    3: '산림 생태계와 천이',
    4: '수목의 생리와 환경',
    5: '야생동물과 서식지',
    6: '숲과 전통문화',
    7: '목재와 임산물',
    8: '조림과 숲 가꾸기',
    9: '도시숲과 녹지',
    10: '산림 휴양과 치유',
    11: '기후변화와 국제 협력',
    12: '산림 정책과 보호지역',
}

# Classify all questions
chapters = {ch: [] for ch in range(1, 13)}
unclassified = []

for i, q in enumerate(data):
    ch = classify(i, q)
    if ch == 0:
        unclassified.append(i)
    else:
        chapters[ch].append(q)

# Report
print(f'Total questions: {len(data)}')
print(f'Unclassified: {len(unclassified)}')
if unclassified:
    for i in unclassified:
        q = data[i]
        print(f'  [{i}] {q["year"]}-{q["number"]}: {q["text"][:100]}')
        print(f'    C1: {q["choice_1"][:60]}')
        print(f'    C2: {q["choice_2"][:60]}')
        print(f'    C3: {q["choice_3"][:60]}')
        print(f'    C4: {q["choice_4"][:60]}')
        print(f'    Exp: {q.get("explanation","")[:120]}')
        print()

print('\n=== Chapter Distribution ===')
total_assigned = 0
for ch in range(1, 13):
    count = len(chapters[ch])
    total_assigned += count
    print(f'  Ch {ch:2d}: {count:3d}문제 - {chapter_titles[ch]}')
print(f'\nTotal assigned: {total_assigned}/{len(data)}')

# Spot-check: show first 3 questions from each chapter
print('\n=== Spot Check (first 3 questions per chapter) ===')
for ch in range(1, 13):
    print(f'\n--- Ch {ch}: {chapter_titles[ch]} ({len(chapters[ch])}문제) ---')
    for q in chapters[ch][:3]:
        print(f'  {q["year"]}-{q["number"]}: {q["text"][:80]}')

# Write chapter JSON files
for ch in range(1, 13):
    output = {
        'chapter': ch,
        'title': chapter_titles[ch],
        'questions': chapters[ch],
    }
    filename = f'_fl_ch{ch}.json'
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'Written: {filename} ({len(chapters[ch])}문제)')

# Final verification
print('\n=== Verification ===')
all_q = []
for ch in range(1, 13):
    all_q.extend(chapters[ch])
orig_keys = set((q['year'], q['number'], q['text'][:30]) for q in data)
ch_keys = set((q['year'], q['number'], q['text'][:30]) for q in all_q)
missing = orig_keys - ch_keys
extra = ch_keys - orig_keys
print(f'Original: {len(orig_keys)} unique, Chapters: {len(ch_keys)} unique')
print(f'Missing: {len(missing)}, Extra: {len(extra)}')
if len(missing) == 0 and len(extra) == 0 and total_assigned == len(data):
    print('VERIFICATION PASSED: All questions assigned correctly.')
else:
    print('VERIFICATION FAILED!')
    if missing:
        for m in sorted(missing):
            print(f'  Missing: {m}')

print('\nDone!')
