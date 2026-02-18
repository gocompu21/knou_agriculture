"""기말시험 기출문제를 웹에서 스크래핑하여 엑셀로 저장하는 스크립트."""
import html as html_mod
import re
import urllib.request
import openpyxl

SUBJECT = '동서양고전의이해'
EXAM_TYPE = '기말시험'

# (year, grade, url) 형태의 리스트
PAGES = [
    (2019, 2, 'https://allaclass.tistory.com/1195'),
    (2018, 2, 'https://allaclass.tistory.com/1194'),
    (2017, 2, 'https://allaclass.tistory.com/1192'),
    (2016, 2, 'https://allaclass.tistory.com/1191'),
    (2015, 2, 'https://allaclass.tistory.com/1190'),
]


def fetch_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8', errors='replace')


def _clean(text):
    """HTML 태그 제거 후 공백 정리."""
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    # HTML 엔티티는 태그 제거 후에 디코딩 (&#60;자본&#62; → <자본>)
    text = html_mod.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_page(html):
    """HTML에서 문제와 정답을 파싱. 신/구 두 가지 형식 지원."""

    # ── 형식 감지: alla6 (구형) vs alla (신형) ──
    is_v6 = 'alla6QuestionTr' in html
    prefix = 'alla6' if is_v6 else 'alla'

    # ── 중복답안 A~K 매핑 ──
    MULTI_ANSWER_MAP = {
        'A': '1,2', 'B': '1,3', 'C': '1,4',
        'D': '2,3', 'E': '2,4', 'F': '3,4',
        'G': '1,2,3', 'H': '1,2,4', 'I': '1,3,4',
        'J': '2,3,4', 'K': '1,2,3,4',
    }

    # ── 정답 추출 ──
    # answer_map: {문제번호(int): 정답(str)} 딕셔너리로 통일
    answer_map = {}

    if is_v6:
        ans_match = re.search(r'alla6AnswerTableDiv.*?<td>(.*?)</td>', html, re.DOTALL)
        if ans_match:
            raw = ans_match.group(1).strip()
            idx = 1
            for c in raw:
                if c.isdigit():
                    answer_map[idx] = c
                    idx += 1
                elif c.upper() in MULTI_ANSWER_MAP:
                    answer_map[idx] = MULTI_ANSWER_MAP[c.upper()]
                    idx += 1
                # else: skip non-answer characters
        else:
            ans_match = re.search(r'(\d{30,})', html)
            if ans_match:
                for idx, c in enumerate(ans_match.group(1), 1):
                    answer_map[idx] = c
    else:
        # allaAnswerTableDiv 안에서만 추출 (중복답안 가이드 범례 제외)
        answer_section = re.search(r'allaAnswerTableDiv.*?</div>', html, re.DOTALL)
        if answer_section:
            rows = re.findall(
                r'<tr><td>(\d+)</td><td>([A-K1-4]?)</td>',
                answer_section.group(0),
            )
            for num_str, ans_val in rows:
                num = int(num_str)
                if ans_val.isdigit():
                    answer_map[num] = ans_val
                elif ans_val.upper() in MULTI_ANSWER_MAP:
                    answer_map[num] = MULTI_ANSWER_MAP[ans_val.upper()]
                else:
                    answer_map[num] = '0'

    # ── 문제 블록 단위로 분할 (BasicTbl 기준) ──
    tbl_id = prefix + 'BasicTbl'
    blocks = re.split(r'(?=<table[^>]*' + tbl_id + r')', html)

    questions = []
    raw_nums = []

    for block in blocks:
        # 문제 텍스트 추출
        q_match = re.search(
            r'<tr[^>]*' + prefix + r'QuestionTr[^>]*>.*?<td[^>]*>(.*?)</td>',
            block, re.DOTALL
        )
        if not q_match:
            continue

        q_inner = q_match.group(1)

        # QuestionNo span에서 번호를 먼저 추출 (숫자+텍스트 병합 방지)
        no_match = re.search(
            r'<span[^>]*' + prefix + r'QuestionNo[^>]*>(\d+)</span>',
            q_inner
        )
        if no_match:
            q_num = int(no_match.group(1))
            # span 제거 후 나머지 텍스트
            q_text = _clean(q_inner.replace(no_match.group(0), ''))
        else:
            q_raw = _clean(q_inner)
            m = re.match(r'(\d+)\s*(.*)', q_raw, re.DOTALL)
            if not m:
                continue
            q_num = int(m.group(1))
            q_text = m.group(2).strip()

        raw_nums.append(q_num)

        # 지문(ExampleTr) 추출 → 문제 텍스트에 병합
        ex_match = re.search(
            r'<tr[^>]*' + prefix + r'ExampleTr[^>]*>.*?<td[^>]*>(.*?)</td>',
            block, re.DOTALL
        )
        if ex_match:
            ex_text = _clean(ex_match.group(1))
            if ex_text:
                q_text = q_text + ' ' + ex_text

        # 보기 추출
        choice_labels = re.findall(
            r'<tr[^>]*' + prefix + r'AnswerTr[^>]*>.*?<label[^>]*>(.*?)</label>',
            block, re.DOTALL
        )
        choices = []
        for j in range(4):
            if j < len(choice_labels):
                choices.append(_clean(choice_labels[j]))
            else:
                choices.append('')

        questions.append({
            'q_num': q_num,
            'text': q_text,
            'c1': choices[0],
            'c2': choices[1],
            'c3': choices[2],
            'c4': choices[3],
        })

    # 오프셋 계산 및 정답 매핑
    offset = min(raw_nums) - 1 if raw_nums else 0
    result = []
    for q in questions:
        raw_num = q.pop('q_num')
        q['number'] = raw_num - offset
        # answer_map 키는 답안표 원본 번호(36~70 또는 1~35), raw_num으로 조회
        q['answer'] = answer_map.get(raw_num, '0')
        result.append(q)

    return result


def main():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SUBJECT

    headers = ['학년도', '시험종류', '과목명', '학년', '문제번호', '문제', '1항', '2항', '3항', '4항', '답안']
    ws.append(headers)

    total = 0
    for year, grade, url in PAGES:
        print(f'{year} {grade}학년... ', end='', flush=True)

        try:
            html = fetch_html(url)
        except Exception as e:
            print(f'FAIL ({e})')
            continue

        questions = parse_page(html)
        if not questions:
            print('0 questions')
            continue

        for q in questions:
            ws.append([
                year, EXAM_TYPE, SUBJECT, grade,
                q['number'], q['text'],
                q['c1'], q['c2'], q['c3'], q['c4'],
                q['answer'] if q['answer'] else '',
            ])

        no_answer = sum(1 for q in questions if q['answer'] == '0')
        multi = sum(1 for q in questions if ',' in str(q['answer']))
        total += len(questions)
        msg = f'{len(questions)} questions'
        if multi:
            msg += f' ({multi} multi-answer)'
        if no_answer:
            msg += f' ({no_answer} no answer)'
        print(msg)

    output = f'data/{SUBJECT}.xlsx'
    wb.save(output)
    print(f'\nDone: {total} questions -> {output}')


if __name__ == '__main__':
    main()
