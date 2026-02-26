"""
기출문제 텍스트 파일의 문제번호 셔플, 보기순서 셔플, 조사 미세 수정을 수행하는 스크립트.
원본 파일을 읽어서 _1.txt 파일로 변환한다.
"""
import re
import random
import sys
import os

random.seed(42)  # 재현 가능하도록 시드 고정

# 조사 미세 수정 규칙 (원본 → 변환)
JOSA_REPLACEMENTS = [
    ('거리가 먼 것은?', '거리가 먼 것은 무엇인가?'),
    ('틀린 것은?', '옳지 않은 것은?'),
    ('올은 것은?', '바른 것은?'),
    ('옳은 것은?', '바른 것은?'),
    ('맞는 것은?', '올바른 것은?'),
    ('아닌 것은?', '해당하지 않는 것은?'),
    ('잘못된 것은?', '올바르지 않은 것은?'),
    ('해당되는 것은?', '속하는 것은?'),
    ('해당되지 않은 것은?', '포함되지 않는 것은?'),
    ('알맞게 설명한 것은?', '올바르게 설명한 것은?'),
    ('잘못 연결한 것은?', '잘못 짝지은 것은?'),
    ('잘못 연결된 것은?', '잘못 짝지어진 것은?'),
    ('설명한 것은?', '기술한 것은?'),
    ('가장 적당한 방법은?', '가장 알맞은 방법은?'),
    ('어느 것인가?', '무엇인가?'),
    ('어디인가?', '어느 곳인가?'),
    ('가장 큰 것은?', '가장 큰 것으로 올바른 것은?'),
    ('가장 낮은 것은?', '가장 낮은 작물은?'),
    ('어떤 색인가?', '무슨 색인가?'),
    ('형성하는가?', '형성하는 것인가?'),
    ('무엇인가?', '어느 것인가?'),
    # 문두 조사 변환
    ('다음 중 ', '다음 보기 중에서 '),
    ('다음의 ', '아래 '),
    ('다음 설명 중 ', '아래 설명 중에서 '),
    ('에 관한 설명 중 ', '에 대한 설명으로 '),
    ('에 대한 설명으로 ', '와 관련된 설명 중 '),
    ('을 의미하는 것은?', '을 뜻하는 것은?'),
    ('를 의미하는 것은?', '를 뜻하는 것은?'),
    ('에 미치는 ', '에 끼치는 '),
    ('에 영향을 ', '에 작용하는 '),
]


def apply_josa_change(text):
    """문제 텍스트에 조사 미세 수정 1~2개 적용"""
    modified = text
    applied = 0
    for old, new in JOSA_REPLACEMENTS:
        if old in modified and applied < 2:
            modified = modified.replace(old, new, 1)
            applied += 1
    return modified


def parse_file(filepath):
    """텍스트 파일을 파싱하여 구조화된 데이터로 반환"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 첫 줄 추출
    lines = content.split('\n')
    first_line = lines[0].strip()

    # 정답표 추출
    answer_map = {}
    answer_section = re.search(r'정답표\s*\n={5,}\s*\n([\s\S]+)$', content)
    if answer_section:
        for m in re.finditer(r'(\d+)\s*:\s*([①②③④])', answer_section.group(1)):
            num = int(m.group(1))
            circle_map = {'①': 1, '②': 2, '③': 3, '④': 4}
            answer_map[num] = circle_map[m.group(2)]

    # 과목 분리
    subject_pattern = re.compile(
        r'={5,}\s*\n(\d+과목\s*:\s*.+?)\n={5,}',
        re.MULTILINE
    )
    subject_matches = list(subject_pattern.finditer(content))

    subjects = []
    for idx, sm in enumerate(subject_matches):
        subj_header = sm.group(1).strip()
        start = sm.end()
        if idx + 1 < len(subject_matches):
            end = subject_matches[idx + 1].start()
        else:
            ans_pos = content.find('정답표', start)
            end = ans_pos if ans_pos != -1 else len(content)

        subj_text = content[start:end]

        # 문제 파싱
        q_pattern = re.compile(r'^(\d{1,3})\.\s+', re.MULTILINE)
        splits = q_pattern.split(subj_text)

        questions = []
        i = 1
        while i < len(splits) - 1:
            num = int(splits[i])
            q_content = splits[i + 1].strip()
            i += 2

            # 보기 분리
            choice_pattern = re.compile(r'[①②③④]\s*')
            parts = choice_pattern.split(q_content)

            q_text = parts[0].strip()
            choices = ['', '', '', '']
            for j in range(1, min(5, len(parts))):
                choices[j - 1] = parts[j].strip()

            answer = answer_map.get(num, 0)

            questions.append({
                'orig_num': num,
                'text': q_text,
                'choices': choices,
                'answer': answer,  # 1-based index
            })

        subjects.append({
            'header': subj_header,
            'questions': questions,
        })

    return first_line, subjects


def shuffle_and_transform(subjects):
    """과목별 문제번호 셔플, 보기순서 셔플, 조사 수정"""
    new_subjects = []

    for subj in subjects:
        questions = subj['questions'][:]
        # 문제 순서 셔플
        random.shuffle(questions)

        new_questions = []
        for q in questions:
            # 조사 미세 수정
            new_text = apply_josa_change(q['text'])

            # 보기 순서 셔플 (정답 추적)
            orig_choices = q['choices'][:]
            orig_answer = q['answer']  # 1-based

            # 인덱스 리스트를 셔플
            indices = [0, 1, 2, 3]
            random.shuffle(indices)

            new_choices = [orig_choices[i] for i in indices]

            # 새 정답 위치 찾기
            if orig_answer > 0:
                orig_answer_idx = orig_answer - 1  # 0-based
                new_answer = indices.index(orig_answer_idx) + 1  # 1-based
            else:
                new_answer = 0

            new_questions.append({
                'text': new_text,
                'choices': new_choices,
                'answer': new_answer,
            })

        new_subjects.append({
            'header': subj['header'],
            'questions': new_questions,
        })

    return new_subjects


def write_file(filepath, first_line, subjects):
    """변환된 데이터를 텍스트 파일로 출력"""
    circle = {1: '①', 2: '②', 3: '③', 4: '④'}
    lines = []
    lines.append(first_line)
    lines.append('')

    global_num = 0
    answer_map = {}

    for subj in subjects:
        lines.append('=====================================')
        lines.append(subj['header'])
        lines.append('=====================================')
        lines.append('')

        for q in subj['questions']:
            global_num += 1
            answer_map[global_num] = q['answer']

            # 문제번호 포맷
            if global_num <= 9:
                prefix = f'{global_num}. '
                indent = '   '
            else:
                prefix = f'{global_num}. '
                indent = '    '

            lines.append(f'{prefix}{q["text"]}')
            for ci in range(4):
                lines.append(f'{indent}{circle[ci+1]} {q["choices"][ci]}')
            lines.append('')

    # 정답표
    lines.append('=====================================')
    lines.append('정답표')
    lines.append('=====================================')
    lines.append('')

    for row_start in range(1, global_num + 1, 10):
        parts = []
        for n in range(row_start, min(row_start + 10, global_num + 1)):
            ans = answer_map.get(n, 0)
            ans_str = circle.get(ans, '?')
            parts.append(f'{n:>2}: {ans_str}')
        lines.append('   '.join(parts))

    lines.append('')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'kisa_exam', '식물보호기사20230305.txt'
        )

    # 출력 파일명: _1 붙이기
    base, ext = os.path.splitext(src)
    dst = base + '_1' + ext

    print(f'원본: {src}')
    print(f'출력: {dst}')

    first_line, subjects = parse_file(src)

    print(f'과목 {len(subjects)}개 파싱 완료')
    for s in subjects:
        print(f'  {s["header"]}: {len(s["questions"])}문제')

    new_subjects = shuffle_and_transform(subjects)

    write_file(dst, first_line, new_subjects)

    # 검증
    _, check = parse_file(dst)
    total = sum(len(s['questions']) for s in check)
    print(f'\n변환 완료! 총 {total}문제 → {dst}')


if __name__ == '__main__':
    main()
