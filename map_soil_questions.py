"""
토양학 360문제를 11개 장에 매핑하고, StudyNote.content에 관련 문제 참조를 삽입하는 스크립트.
"""
import os
import re
import sys
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from exam.models import Question, StudyNote
from main.models import Subject

subject = Subject.objects.get(name="토양학")
questions = list(
    Question.objects.filter(subject=subject).order_by("year", "number")
)
notes = list(StudyNote.objects.filter(subject=subject).order_by("order"))

print(f"총 {len(questions)}문제, {len(notes)}장")

# ─── 장별 키워드 (핵심 용어 기반) ───
CHAPTER_KEYWORDS = {
    1: [  # 토양의 생성과 분류
        "풍화", "모암", "모재", "잔적토", "충적토", "붕적토", "풍적토", "화산회토",
        "토양생성인자", "토양단면", "층위", "O층", "A층", "B층", "C층", "R층",
        "용탈", "집적", "반토", "클라이모시퀀스", "토포시퀀스", "리소시퀀스",
        "생물풍화", "화학풍화", "물리풍화", "기계풍화", "가수분해",
        "토양목", "토양분류", "분류체계",
        "지각", "1차광물", "2차광물", "1차 광물", "2차 광물",
    ],
    2: [  # 토양의 물리적 성질
        "토성", "사토", "양토", "식토", "미사", "사양토", "식양토",
        "토양구조", "입단", "단립", "괴상", "주상", "판상",
        "용적밀도", "입자밀도", "공극률", "공극", "진비중", "가비중",
        "토양삼상", "3상", "삼상", "고상", "액상", "기상",
        "토양색", "먼셀", "토색첩",
        "점토", "입자크기", "모래", "경반층",
        "산화철", "적색", "회청색",
    ],
    3: [  # 토양의 물
        "토양수", "중력수", "모관수", "흡습수", "결합수", "모세관",
        "포장용수량", "위조점", "영구위조점", "유효수분", "최대용수량",
        "수분포텐셜", "매트릭포텐셜", "삼투포텐셜", "수분장력", "pF",
        "투수", "투수성", "투수계수", "침투", "수리전도도",
        "토양공기", "통기", "통기성", "산소확산", "환원",
        "수분함량", "수분당량", "용적수분",
        "응집력", "부착력", "수분보유", "물분자",
    ],
    4: [  # 토양 교질과 이온교환
        "교질", "콜로이드", "점토광물", "카올리나이트", "몬모릴로나이트",
        "일라이트", "버미큘라이트", "1:1형", "2:1형", "동형치환",
        "양이온교환용량", "CEC", "음이온교환용량", "AEC",
        "염기포화도", "교환성", "이온교환", "양이온보유력",
        "교환성양이온", "교환성칼슘", "교환성마그네슘",
        "교환침입력", "교환침출력", "침출력", "침입력",
    ],
    5: [  # 산성 토양과 개량
        "산성토양", "토양산성", "산성화", "활성산도", "잠재산도",
        "석회소요량", "석회", "알칼리토양", "염류토양",
        "완충능", "완충용량", "pH", "산도",
        "알루미늄독성", "알루미늄", "교환산도", "수소이온",
        "산성에서", "양분 유효도", "유효도",
    ],
    6: [  # 토양 생물과 유기물
        "미생물", "세균", "방선균", "사상균", "곰팡이", "조류",
        "질소순환", "질소고정", "질화작용", "탈질", "질산화", "암모니아화",
        "유기물", "부식", "부식산", "풀빅산", "휴민", "휴믹산",
        "탄질률", "C/N율", "C/N비", "탄소율", "탄질율",
        "유효화", "부동화", "무기화", "광물화",
        "퇴비", "녹비", "유기물분해",
        "근권미생물", "균근", "근류균", "리조비움",
        "질소기아", "자급영양", "독립영양",
        "질산태질소", "암모니아동화", "질산화작용", "탈질작용",
    ],
    7: [  # 토양오염
        "토양오염", "오염", "중금속", "카드뮴", "납", "비소", "수은", "크롬",
        "유류오염", "농약오염",
        "대기오염", "산성비", "온실가스", "이산화탄소",
        "복원", "정화", "생물정화", "세정", "고정화",
        "유해물질", "발암물질", "옐로우보이",
        "바이오연료",
    ],
    8: [  # 토양보전
        "토양침식", "침식", "수식", "풍식",
        "USLE", "범용토양유실", "유실공식", "토양유실",
        "보전", "등고선", "단구", "초생대",
        "경작침식", "빗방울침식", "면상침식", "세류침식", "협곡침식",
        "지속가능", "보전경운",
    ],
    9: [  # 토양조사, 분류 및 흙토람
        "토양조사", "흙토람", "토양환경정보", "토양도",
        "토양통", "토양계열", "토양형",
        "토양분류체계", "미국분류", "USDA",
        "인셉티졸", "안디졸", "아리디졸", "엔티졸", "얼티졸", "옥시졸",
        "몰리졸", "알피졸", "스포도졸", "젤리졸", "히스토졸", "버티졸",
        "12개의 목", "토양 목", "토양목",
    ],
    10: [  # 식물영양과 필수원소
        "필수원소", "필수영양소", "다량원소", "미량원소",
        "질소결핍", "인결핍", "칼륨결핍", "결핍증상", "과잉증상",
        "양분흡수", "능동수송", "수동흡수", "능동적수송", "수동적수송", "능동적 수송", "수동적 수송",
        "킬레이트", "엽면흡수",
        "철결핍", "아연결핍", "망간결핍", "붕소결핍", "구리결핍", "몰리브덴결핍",
        "길항작용", "상승작용", "리비히", "최소양분",
        "증산류", "카스파리대", "카스피리대", "아포플라스트", "심플라스트",
        "셀룰로오스", "엽록소", "핵산", "단백질", "아미노산", "아미드",
        "글루타민", "글루탐산", "시스테인", "메티오닌", "라이신",
        "기공", "팁번", "tip burn",
        "구성원소", "유기성분",
        "농도구배", "확산", "촉진확산", "단순확산",
    ],
    11: [  # 비료와 시비
        "비료", "시비", "화학비료", "유기질비료",
        "질소비료", "요소", "황산암모늄", "질산암모늄", "염화암모늄",
        "인산비료", "과인산석회", "용과린", "용성인비", "인광석",
        "칼리비료", "염화칼리", "황산칼리",
        "복합비료", "혼합비료", "배합비료",
        "석회질비료", "규산질비료",
        "완효성비료", "완효성", "피복비료",
        "엽면시비",
        "시비량", "비효", "비료배합",
        "생석회", "소석회", "탄산석회",
        "휘산", "암모니아 휘산", "실바이트",
        "암모늄이온", "NH₄",
    ],
}

# ─── 수동 매핑 (키워드로 매칭 안되는 문제) ───
MANUAL_MAPPING = {
    # (year, number): [chapter_numbers]
    (2024, 3): [9],   # 토양구분 몇 개의 목
    (2024, 13): [9],  # 우리나라에 존재하지 않는 토양
    (2024, 32): [9],  # 토양구분 몇 개의 목 (중복)
    (2024, 42): [9],  # 우리나라에 존재하지 않는 토양 (중복)
    (2024, 60): [5],  # 물과 반응하여 토양을 산성으로
    (2024, 69): [9],  # 세계토양 12목
    # 도시농업 관련 (토양학 범위 밖이지만 Chapter 8 지속가능 농업에 배치)
    (2015, 18): [8],  # 식품사막
    (2016, 23): [8],  # 얼랏먼트 도시농업
    (2019, 17): [8],  # 파머스 마켓
    (2019, 18): [8],  # 도시 환경개선형
    # 단편적 문제 (보기 없음)
    (2025, 55): [1],  # 가장 함량이 큰 것 → 지각 성분
    (2025, 111): [1], # 가장 함량이 큰 것 → 지각 성분 (중복)
}

# ─── 문제별 매핑 ───
question_chapters = {}  # {q.pk: [chapter_numbers]}

for q in questions:
    # 수동 매핑 우선
    manual = MANUAL_MAPPING.get((q.year, q.number))
    if manual:
        question_chapters[q.pk] = manual
        continue

    text = f"{q.text} {q.choice_1} {q.choice_2} {q.choice_3} {q.choice_4}"
    if q.explanation:
        text += f" {q.explanation}"
    text_lower = text.lower()

    scores = {}
    for ch, keywords in CHAPTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 1
        if score > 0:
            scores[ch] = score

    if scores:
        max_score = max(scores.values())
        # 최고 점수 장만 선택 (단, 50% 이상 점수면 복수 매핑)
        threshold = max(1, max_score * 0.5)
        matched = [ch for ch, s in scores.items() if s >= threshold]
        question_chapters[q.pk] = matched
    else:
        question_chapters[q.pk] = []

# 매핑 통계
mapped_count = sum(1 for chs in question_chapters.values() if chs)
unmapped = [(q.year, q.number, q.text[:50]) for q in questions if not question_chapters.get(q.pk)]

print(f"\n매핑 완료: {mapped_count}/{len(questions)}")
if unmapped:
    print(f"미매핑: {len(unmapped)}문제")
    for y, n, t in unmapped[:10]:
        print(f"  {y}-{n}: {t}")

# 장별 매핑 문제 수
print("\n장별 매핑 문제 수:")
for ch in range(1, 12):
    ch_questions = [q for q in questions if ch in question_chapters.get(q.pk, [])]
    print(f"  제{ch}장: {len(ch_questions)}문제")

# ─── StudyNote.content에 관련 문제 참조 삽입 ───
print("\n=== StudyNote 업데이트 ===")

for note in notes:
    ch_num = note.order
    ch_questions = [q for q in questions if ch_num in question_chapters.get(q.pk, [])]

    if not ch_questions:
        print(f"  제{ch_num}장: 매핑 문제 없음 → 건너뜀")
        continue

    # 기존 관련 문제 참조 제거
    content = re.sub(r'\n\*\*관련 문제\*\*:.*', '', note.content)

    # 각 ### 섹션 찾기
    lines = content.split('\n')
    sections = []  # [(line_idx, section_title)]
    for i, line in enumerate(lines):
        if line.startswith('### '):
            sections.append((i, line[4:].strip()))

    if not sections:
        # 섹션이 없으면 장 끝에 전체 관련 문제 추가
        refs = [f"({q.year}-{q.number})" for q in ch_questions]
        content += f"\n\n**관련 문제**: {', '.join(refs)}"
    else:
        # 각 섹션의 키워드로 문제 세분화 매핑
        section_questions = {}  # {section_idx: [questions]}

        for si, (line_idx, section_title) in enumerate(sections):
            # 섹션 내용 범위 추출
            start = line_idx
            end = sections[si + 1][0] if si + 1 < len(sections) else len(lines)
            section_text = ' '.join(lines[start:end])

            section_qs = []
            for q in ch_questions:
                q_text = f"{q.text} {q.choice_1} {q.choice_2} {q.choice_3} {q.choice_4}"
                # 섹션 키워드와 문제 키워드 매칭
                section_words = set(re.findall(r'[가-힣]{2,}', section_text))
                q_words = set(re.findall(r'[가-힣]{2,}', q_text))
                overlap = section_words & q_words
                # 의미있는 겹침 (일반적인 단어 제외)
                common_words = {"토양", "다음", "것은", "대한", "설명", "옳은", "맞는", "문제",
                               "않은", "관한", "중에서", "대하여", "해당", "보기", "다음의",
                               "어느", "적절", "올바른", "아닌", "맞는", "틀린", "가장",
                               "관계", "원소", "비료", "식물", "작용", "성분", "물질",
                               "양분", "영양", "토양의", "토양에"}
                meaningful_overlap = overlap - common_words
                if len(meaningful_overlap) >= 2:
                    section_qs.append(q)

            section_questions[si] = section_qs

        # 할당되지 않은 문제는 가장 관련성 높은 섹션에 할당
        assigned_pks = set()
        for qs in section_questions.values():
            for q in qs:
                assigned_pks.add(q.pk)

        unassigned = [q for q in ch_questions if q.pk not in assigned_pks]
        if unassigned and sections:
            # 마지막 섹션(키워드 요약 등)이 아닌 첫 번째 섹션에 배치
            section_questions[0] = section_questions.get(0, []) + unassigned

        # 내용에 관련 문제 삽입 (섹션 끝에)
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)

            # 이 줄이 다음 섹션 시작 직전이면 이전 섹션의 관련 문제 삽입
            for si, (line_idx, _) in enumerate(sections):
                next_start = sections[si + 1][0] if si + 1 < len(sections) else len(lines)
                if i == next_start - 1 and section_questions.get(si):
                    qs = section_questions[si]
                    refs = [f"({q.year}-{q.number})" for q in sorted(qs, key=lambda x: (x.year, x.number))]
                    new_lines.append(f"\n**관련 문제**: {', '.join(refs)}")
                    new_lines.append("")

        # 마지막 섹션의 관련 문제
        if sections:
            last_si = len(sections) - 1
            if section_questions.get(last_si):
                qs = section_questions[last_si]
                refs = [f"({q.year}-{q.number})" for q in sorted(qs, key=lambda x: (x.year, x.number))]
                new_lines.append(f"\n**관련 문제**: {', '.join(refs)}")

        content = '\n'.join(new_lines)

    # 연속 빈 줄 정리
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    note.content = content
    note.save()
    print(f"  제{ch_num}장: {len(ch_questions)}문제 매핑 완료")

print("\n완료!")
