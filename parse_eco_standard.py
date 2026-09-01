# -*- coding: utf-8 -*-
"""자연생태복원기사 출제기준 PDF(Q-net, 2025.01.01~2027.12.31) → 구조화 JSON/Markdown

사용: python parse_eco_standard.py [pdf경로]
출력: _eco_exam_standard_2025.json, _eco_exam_standard_2025.md
"""
import sys, re, json
import fitz

sys.stdout.reconfigure(encoding='utf-8')
PDF = sys.argv[1] if len(sys.argv) > 1 else 'data/comcbt/자연생태복원기사_출제기준_2025-2027.pdf'


_HANGUL = re.compile(r'[가-힣]')


def cell(c):
    """셀 텍스트. 한글-한글 사이의 줄바꿈은 단어가 끊긴 것이므로 붙이고, 그 외는 공백."""
    s = c or ''
    out = []
    for i, ch in enumerate(s):
        if ch == '\n':
            prev = s[i - 1] if i > 0 else ''
            nxt = s[i + 1] if i + 1 < len(s) else ''
            out.append('' if (_HANGUL.match(prev) and _HANGUL.match(nxt)) else ' ')
        else:
            out.append(ch)
    return ''.join(out).strip()


def join_lines(s):
    """셀 안 줄바꿈으로 끊긴 한글 단어를 이어 붙인다."""
    return re.sub(r'\s+', ' ', (s or '')).strip()


def split_items(text):
    """'1. ... 2. ... 3. ...' 형태의 세세항목을 번호 단위로 분리."""
    text = join_lines(text)
    parts = re.split(r'(?:(?<=\s)|^)(\d{1,2})\.\s*', text)
    items = []
    # parts: ['', '1', 'xxx', '2', 'yyy', ...]
    i = 1
    while i < len(parts) - 1:
        items.append({'no': int(parts[i]), 'text': parts[i + 1].strip()})
        i += 2
    if not items and text:
        items.append({'no': None, 'text': text})
    return items


def parse(pages, ncols, pdf):
    """표를 행 단위로 읽어 주요항목→세부항목→세세항목 트리로 누적."""
    tree = []          # [{subject, count, majors:[{name, subs:[{name, items:[]}]}]}]
    cur_subj = cur_major = cur_sub = None
    pending_detail = []

    def flush():
        nonlocal pending_detail
        if cur_sub is not None and pending_detail:
            cur_sub['_raw'] = (cur_sub.get('_raw', '') + ' ' + ' '.join(pending_detail)).strip()
        pending_detail = []

    for pi in pages:
        p = pdf[pi]
        for t in p.find_tables().tables:
            if t.col_count != ncols:      # 상단 헤더 표(직무분야·검정방법)는 건너뜀
                continue
            for row in t.extract():
                row = [cell(c) for c in row]
                if len(row) < ncols:
                    row += [''] * (ncols - len(row))
                if ncols == 5:
                    subj, cnt, major, sub, detail = row[:5]
                else:
                    subj, major, sub, detail = row[:4]
                    cnt = ''
                if subj in ('필기과목명', '실기과목명') or major == '주요항목':
                    continue
                if subj and (cur_subj is None or subj != cur_subj['subject']):
                    flush()
                    cur_subj = {'subject': subj, 'count': cnt or None, 'majors': []}
                    tree.append(cur_subj)
                    cur_major = cur_sub = None
                if major and (cur_major is None or major != cur_major['name']):
                    flush()
                    cur_major = {'name': major, 'subs': []}
                    cur_subj['majors'].append(cur_major)
                    cur_sub = None
                if sub and (cur_sub is None or sub != cur_sub['name']):
                    flush()
                    cur_sub = {'name': sub, 'items': []}
                    cur_major['subs'].append(cur_sub)
                if detail:
                    pending_detail.append(detail)
    flush()
    for s in tree:
        for m in s['majors']:
            m['name'] = join_lines(m['name'])
            for sb in m['subs']:
                sb['name'] = join_lines(sb['name'])
                sb['items'] = split_items(sb.pop('_raw', ''))
    return tree


def main():
    pdf = fitz.open(PDF)
    # 실기 시작 페이지 찾기
    start = next(i for i in range(pdf.page_count) if '출 제 기 준 ( 실 기 )' in pdf[i].get_text())
    header = pdf[start].get_text()
    m = re.search(r'시험시간\s*(.+?)실기과목명', header, re.S)
    exam_time = join_lines(m.group(1)) if m else ''
    criteria = re.findall(r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|검정방법)', header.split('수행준거')[1], re.S | re.M)

    written = parse(range(0, start), 5, pdf)
    practical = parse(range(start, pdf.page_count), 4, pdf)

    period = re.search(r'적용기간\s*(\S+)\s*(~\S+)', pdf[0].get_text())
    out = {
        'source': PDF,
        'period': (period.group(1) + period.group(2)) if period else '',
        'practical_exam_time': exam_time,
        'practical_criteria': [join_lines(c[1]) for c in criteria],
        'written': written,
        'practical': practical,
    }
    with open('_eco_exam_standard_2025.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    lines = [f"# 자연생태복원기사 출제기준 ({out['period']})", '',
             f"- 실기 검정방법: 복합형, 시험시간: {exam_time}", '',
             '## 실기 수행준거', '']
    lines += [f"{i+1}. {c}" for i, c in enumerate(out['practical_criteria'])]
    for title, tree in (('실기 (생태복원 전문실무)', practical), ('필기', written)):
        lines += ['', f'## {title}', '']
        for s in tree:
            lines.append(f"### {s['subject']}" + (f" ({s['count']}문항)" if s['count'] else ''))
            for m in s['majors']:
                lines.append(f"- **{m['name']}**")
                for sb in m['subs']:
                    lines.append(f"  - {sb['name']}")
                    for it in sb['items']:
                        no = f"{it['no']}. " if it['no'] else ''
                        lines.append(f"    - {no}{it['text']}")
            lines.append('')
    with open('_eco_exam_standard_2025.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 요약 출력
    print('적용기간:', out['period'], '| 실기 시험시간:', exam_time)
    for title, tree in (('실기', practical), ('필기', written)):
        for s in tree:
            nm = sum(len(m['subs']) for m in s['majors'])
            ni = sum(len(sb['items']) for m in s['majors'] for sb in m['subs'])
            print(f"[{title}] {s['subject']}: 주요항목 {len(s['majors'])} / 세부항목 {nm} / 세세항목 {ni}")


if __name__ == '__main__':
    main()
