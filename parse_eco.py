# -*- coding: utf-8 -*-
"""자연생태복원기사 comcbt PDF 파서

사용법:
    python parse_eco.py                      # data/comcbt/자연생태복원기사*.pdf 전체
    python parse_eco.py 2012-1               # 특정 회차만
    python parse_eco.py 2012-1 --json        # JSON 출력만 (DB 저장 안 함)
"""
import os, re, sys, json, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "comcbt")

# 과목: 문항번호 범위로 판정 (과목당 20문항)
SUBJECTS = [
    (1, 20, "환경생태학개론"),
    (21, 40, "환경계획학"),
    (41, 60, "생태복원공학"),
    (61, 80, "경관생태학"),
    (81, 100, "자연환경관계법규"),
]

CIRCLED = "①②③④"
CIRCLE_NUM = {c: i + 1 for i, c in enumerate(CIRCLED)}


def subject_of(num):
    for lo, hi, name in SUBJECTS:
        if lo <= num <= hi:
            return name
    return None


def clean(s):
    """공백/제어문자 정리"""
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


# 마지막 페이지 하단 CBT 홍보 문구 시작을 알리는 표지
# (이 줄부터 뒤는 전부 광고이므로 통째로 잘라낸다)
AD_START = (
    "종이 문제집",
    "실제 시험에서 사용하는",
    "PC 버전",
)


def _is_ad(line):
    """광고 블록 시작 줄인지"""
    return any(k in line for k in AD_START)


def extract_pages(path):
    doc = fitz.open(path)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    doc.close()
    return pages


# ---------------------------------------------------------------- 이미지 추출

COL_SPLIT = 290.0  # 2단 레이아웃 좌/우 경계 x


def _col(x):
    return 0 if x < COL_SPLIT else 1


def extract_images(path, out_dir, prefix):
    """수식·그림 이미지를 문항번호에 매칭해 잘라 저장.

    반환: {문항번호: [저장파일명, ...]}  (해당 문항 영역 안에 있는 이미지들)
    """
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(path)
    result = {}
    pending = []
    prev_last_num = None   # 직전 페이지의 마지막 문항번호 (페이지 넘김 처리)

    for pno in range(doc.page_count):
        pg = doc[pno]

        # 이 페이지의 문항 시작점 (번호, 컬럼, y)
        anchors = []
        for blk in pg.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln.get("spans", []):
                    m = re.match(r"^\s*(\d{1,3})\.\s", sp["text"])
                    if m:
                        n = int(m.group(1))
                        if 1 <= n <= 100:
                            x0, y0 = sp["bbox"][0], sp["bbox"][1]
                            anchors.append((n, _col(x0), y0))
        if not anchors:
            continue
        anchors.sort(key=lambda a: (a[1], a[2]))

        # 컬럼별 마지막 문항 (컬럼/페이지 넘김 처리에 사용)
        last_of_col = {}
        for n, c, y in anchors:
            if c not in last_of_col or y > last_of_col[c][1]:
                last_of_col[c] = (n, y)

        # 이미지 객체
        for img in pg.get_images(full=True):
            xref = img[0]
            rects = pg.get_image_rects(xref)
            if not rects:
                continue
            r = rects[0]
            col = _col(r.x0)
            # 같은 컬럼에서 이미지 위쪽에 있는 가장 가까운 문항번호
            cand = [a for a in anchors if a[1] == col and a[2] <= r.y0 + 2]
            if cand:
                num = max(cand, key=lambda a: a[2])[0]
            elif col == 1 and 0 in last_of_col:
                # 우측 단 상단에 있는데 그 위에 문항이 없음
                # → 좌측 단 마지막 문항이 이어진 것 (컬럼 넘김)
                num = last_of_col[0][0]
            elif col == 0 and prev_last_num is not None:
                # 좌측 단 상단인데 위에 문항이 없음 → 이전 페이지 마지막 문항이 이어짐
                num = prev_last_num
            else:
                continue

            # 저장은 나중에 (읽는 순서대로 정렬 후)
            pending.append((num, pno, col, r.y0, r.x0, r))

        # 이 페이지의 마지막 문항번호 기록 (다음 페이지 넘김 처리용)
        prev_last_num = max(a[0] for a in anchors)

    # 문항별로 읽는 순서대로 정렬해 저장.
    # 보기가 2×2 격자로 배치되는 경우가 있어 y만으로 정렬하면 ①②가 뒤바뀐다.
    # 같은 행(y가 서로 ROW_TOL 이내)은 한 행으로 묶고, 행 안에서는 x 순으로 읽는다.
    ROW_TOL = 15.0

    ordered = []
    # (문항, 페이지, 컬럼) 그룹별로 행 클러스터링
    groups = {}
    for t in pending:
        groups.setdefault((t[0], t[1], t[2]), []).append(t)

    for key in sorted(groups):
        items = sorted(groups[key], key=lambda t: t[3])   # y 오름차순
        row, row_y = [], None
        rows = []
        for it in items:
            if row_y is None or abs(it[3] - row_y) <= ROW_TOL:
                row.append(it)
                row_y = it[3] if row_y is None else row_y
            else:
                rows.append(row)
                row, row_y = [it], it[3]
        if row:
            rows.append(row)
        for rw in rows:
            ordered.extend(sorted(rw, key=lambda t: t[4]))  # 행 안에서 x 오름차순

    for num, pno, col, _y, _x, r in ordered:
        pg = doc[pno]
        clip = fitz.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        pix = pg.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip)
        seq = len(result.get(num, [])) + 1
        fname = "%s_q%03d_%d.png" % (prefix, num, seq)
        pix.save(os.path.join(out_dir, fname))
        result.setdefault(num, []).append(fname)

    doc.close()
    return result


def parse_answers(pages):
    """마지막 페이지들의 정답표 파싱 → {문항번호: 정답}

    형식: 번호 10개가 줄줄이 나온 뒤 정답(①~④) 10개가 이어짐 (반복)
    """
    answers = {}
    # 뒤쪽 페이지부터 정답 블록 탐색
    tail = "\n".join(pages[-3:])
    lines = [clean(l) for l in tail.split("\n")]
    lines = [l for l in lines if l]

    nums_buf = []
    for line in lines:
        # 숫자만 있는 줄
        if re.fullmatch(r"\d{1,3}", line):
            nums_buf.append(int(line))
            continue
        # 정답 기호만 있는 줄
        if line in CIRCLE_NUM:
            if nums_buf:
                # 버퍼 앞에서부터 하나씩 매칭
                n = nums_buf.pop(0)
                answers[n] = str(CIRCLE_NUM[line])
            continue
        # 그 외 줄은 버퍼 초기화하지 않음(헤더 등 무시)
    return answers


def parse_questions(pages):
    """본문에서 문항 파싱 → [{number, text, choices[4]}]"""
    # 헤더/푸터 제거
    body_lines = []
    ad_reached = False
    for pg in pages:
        if ad_reached:
            break
        for raw in pg.split("\n"):
            l = clean(raw)
            if not l:
                continue
            if _is_ad(l):
                # 광고 블록 시작 → 이후 본문은 모두 버림
                ad_reached = True
                break
            if "comcbt" in l or "전자문제집" in l or "기출문제" in l.replace(" ", ""):
                continue
            if re.fullmatch(r"\d+과목\s*:.*", l):
                continue
            body_lines.append(l)

    # 정답표 영역 잘라내기: 숫자/기호만 연속되는 뒷부분 제거
    cut = len(body_lines)
    run = 0
    for i, l in enumerate(body_lines):
        if re.fullmatch(r"\d{1,3}", l) or l in CIRCLE_NUM:
            run += 1
            if run >= 12 and cut == len(body_lines):
                cut = i - run + 1
        else:
            run = 0
            cut = len(body_lines)
    body_lines = body_lines[:cut]

    text = "\n".join(body_lines)

    # 문항 시작: 줄 첫머리 "N. "
    starts = []
    for m in re.finditer(r"(?m)^(\d{1,3})\.\s*", text):
        n = int(m.group(1))
        if 1 <= n <= 100:
            starts.append((n, m.start(), m.end()))

    # 번호 오름차순 보정 (중복/오탐 제거)
    filtered = []
    expect = 1
    for n, s, e in starts:
        if n == expect:
            filtered.append((n, s, e))
            expect += 1
    starts = filtered

    questions = []
    for idx, (num, s, e) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(text)
        chunk = text[e:end]

        # 보기 분리: ①②③④ 위치 기준
        positions = []
        for m in re.finditer(r"[①②③④]", chunk):
            positions.append((m.start(), m.group()))

        # 순서대로 ①→②→③→④ 만 채택
        picked = []
        want = 1
        for pos, ch in positions:
            if CIRCLE_NUM[ch] == want:
                picked.append((pos, want))
                want += 1
                if want > 4:
                    break

        if len(picked) < 4:
            # 보기 파싱 실패 → 스킵 대상으로 표시
            questions.append({
                "number": num,
                "text": clean(chunk.replace("\n", " ")),
                "choices": ["", "", "", ""],
                "incomplete": True,
            })
            continue

        qtext = chunk[: picked[0][0]]
        choices = []
        for i, (pos, _) in enumerate(picked):
            nxt = picked[i + 1][0] if i + 1 < len(picked) else len(chunk)
            c = chunk[pos + 1 : nxt]
            choices.append(clean(c.replace("\n", " ")))

        # 보기 중 빈 칸이 있으면(수식·그림 보기) 불완전으로 표시
        blank = any(not c.strip() for c in choices)

        questions.append({
            "number": num,
            "text": clean(qtext.replace("\n", " ")),
            "choices": choices,
            "incomplete": blank,
        })

    return questions


def parse_pdf(path, img_dir=None, prefix=None):
    pages = extract_pages(path)
    answers = parse_answers(pages)
    questions = parse_questions(pages)

    imgmap = {}
    if img_dir and prefix:
        imgmap = extract_images(path, img_dir, prefix)

    for q in questions:
        q["answer"] = answers.get(q["number"], "0")
        q["subject"] = subject_of(q["number"])
        imgs = list(imgmap.get(q["number"], []))
        q["images"] = imgs
        blanks = [i for i, c in enumerate(q["choices"]) if not c.strip()]
        q["choice_images"] = ["", "", "", ""]
        q["text_image"] = ""

        if not imgs:
            pass

        elif len(imgs) >= 4:
            # 마지막 4개를 보기 ①~④로, 그 앞의 여분은 지문 그림([보기] 박스 등)
            head, tail = imgs[:-4], imgs[-4:]
            for i in range(4):
                q["choice_images"][i] = tail[i]
            if head:
                q["text_image"] = head[0]
            q["incomplete"] = False

        elif blanks and len(imgs) >= len(blanks):
            # 일부 보기만 이미지인 경우
            for i, bi in enumerate(blanks):
                q["choice_images"][bi] = imgs[i]
            q["incomplete"] = False

        else:
            # 이미지가 1~3개뿐이고 보기는 텍스트로 채워짐 → 지문 그림
            q["text_image"] = imgs[0]
    return questions


def round_from_filename(fn):
    m = re.search(r"(\d{4})-(\d)", fn)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_only = "--json" in sys.argv

    files = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.startswith("자연생태복원기사") and f.endswith(".pdf")
    )
    if args:
        files = [f for f in files if any(a in f for a in args)]

    if not files:
        print("대상 파일 없음")
        return

    img_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_eco_images")

    all_out = []
    for fn in files:
        year, rnd = round_from_filename(fn)
        prefix = "eco%d-%d" % (year, rnd)
        qs = parse_pdf(os.path.join(DATA_DIR, fn), img_dir=img_root, prefix=prefix)
        bad = [q for q in qs if q["incomplete"]]
        noans = [q for q in qs if q["answer"] == "0"]
        nimg = sum(1 for q in qs if q.get("text_image") or any(q.get("choice_images", [])))
        print("%s  → %d문항 (보기누락 %d, 정답없음 %d, 이미지문항 %d)"
              % (fn, len(qs), len(bad), len(noans), nimg))
        if bad:
            print("   보기누락 문항번호:", [q["number"] for q in bad])
        if noans:
            print("   정답없음 문항번호:", [q["number"] for q in noans])
        all_out.append({"file": fn, "year": year, "round": rnd, "questions": qs})

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_eco_parsed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_out, f, ensure_ascii=False, indent=1)
    print("\nJSON 저장:", out_path)


if __name__ == "__main__":
    main()
