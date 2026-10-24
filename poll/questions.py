"""AI 모임 사전 설문 문항 — 대표님 승인본(문구 그대로). 화면·검증·통계·CSV 가 모두 이 표를 쓴다.

type
  text    주관식(한 줄 또는 여러 줄: rows)
  single  하나 고르기. other=True 면 마지막 보기가 '기타' 이고 글 칸이 붙는다
  multi   여러 개 고르기. max 가 있으면 최대 개수
  scale   여러 줄(items) × 같은 보기(choices) — 9번(맞다/아니다/모르겠다), 10번(용어)
답 저장 키: 'q2', 'q3', 'q3_other', 'q5'(목록), 'q9_1'…, 'q10_1'… (scale 은 qN_항목번호)
"""

PARTS = [
    {"title": "1부 기본 정보", "note": ""},
    {"title": "2부 AI 경험", "note": ""},
    {"title": "3부 AI 이해도", "note": "정답을 맞히는 시험이 아니라 어디서부터 설명할지 보려는 문항입니다."},
    {"title": "4부 목표와 걱정", "note": ""},
    {"title": "5부 수업 방식", "note": ""},
]

QUESTIONS = [
    {"id": "q1", "num": "1", "part": 0, "type": "text", "title": "이름", "required": True},
    {"id": "q2", "num": "2", "part": 0, "type": "single", "title": "연령대", "required": True,
     "choices": ["30대 이하", "40대", "50대", "60대", "70대 이상"]},
    {"id": "q3", "num": "3", "part": 0, "type": "single", "title": "하시는 일", "required": False, "other": True,
     "choices": ["회사원", "자영업·사업", "전문직", "공무원·교직", "주부", "은퇴", "학생", "기타"]},
    {"id": "q4", "num": "4", "part": 0, "type": "single", "title": "컴퓨터·스마트폰을 얼마나 편하게 쓰시나요?", "required": True,
     "choices": ["전화·카톡 정도만 쓴다", "검색, 사진, 유튜브는 익숙하다", "문서 작성(한글·워드·엑셀)도 한다",
                 "프로그램 설치, 파일 정리 등 웬만한 건 혼자 한다"]},

    {"id": "q5", "num": "5", "part": 1, "type": "multi", "title": "써 본 AI를 모두 골라 주세요", "required": False, "other": True,
     "choices": ["ChatGPT", "Claude", "Gemini", "네이버 클로바X / 하이퍼클로바", "뤼튼", "코파일럿",
                 "이름은 들어 봤지만 써 본 적 없음", "기타"]},
    {"id": "q6", "num": "6", "part": 1, "type": "single", "title": "AI를 얼마나 자주 쓰시나요?", "required": True,
     "choices": ["써 본 적 없다", "몇 번 해 봤다", "한 달에 몇 번", "일주일에 몇 번", "거의 매일"]},
    {"id": "q7", "num": "7", "part": 1, "type": "multi", "title": "지금 AI를 어디에 쓰시나요?", "required": False, "other": True,
     "choices": ["궁금한 것 물어보기", "글쓰기·문장 다듬기", "번역", "요약(문서·기사·영상)", "공부·자격증 준비",
                 "업무 문서·보고서", "사진·그림 만들기", "아직 안 쓴다", "기타"]},
    {"id": "q8", "num": "8", "part": 1, "type": "single", "title": "유료 AI를 쓰고 계신가요?", "required": False,
     "choices": ["무료만 쓴다", "유료를 쓰고 있다", "잘 모르겠다"],
     "other_on": 1, "other_label": "어떤 것"},

    {"id": "q9", "num": "9", "part": 2, "type": "scale", "title": "다음 말이 맞을까요?", "required": False,
     "choices": ["맞다", "아니다", "모르겠다"],
     "items": [
         {"num": "9-1", "text": "AI는 가끔 그럴듯하게 틀린 답을 한다.", "answer": "맞다"},
         {"num": "9-2", "text": "AI에게 질문을 자세히 할수록 답이 좋아진다.", "answer": "맞다"},
         {"num": "9-3", "text": "AI는 내가 대화창에 입력한 내용을 기억해 다음 대화에도 쓸 수 있다.", "answer": "아니다",
          "note": "설정에 따라 다름 — 대화 기억(메모리)은 서비스·설정에 따라 켜져 있기도 하다"},
         {"num": "9-4", "text": "AI로 그림, 음성, 영상도 만들 수 있다.", "answer": "맞다"},
     ]},
    {"id": "q10", "num": "10", "part": 2, "type": "scale", "title": "다음 말을 들어 보거나 아시나요?", "required": False,
     "choices": ["처음 들음", "들어 봄", "설명할 수 있음"],
     "items": [{"num": "", "text": "프롬프트"}, {"num": "", "text": "생성형 AI"},
               {"num": "", "text": "할루시네이션"}, {"num": "", "text": "AI 에이전트"}]},

    {"id": "q11", "num": "11", "part": 3, "type": "multi", "title": "이 모임에서 가장 배우고 싶은 것", "required": True,
     "max": 3, "other": True,
     "choices": ["AI에게 질문 잘하는 법", "글쓰기·보고서·제안서", "문서 요약·정리", "엑셀·자료 분석", "사진·그림 만들기",
                 "영상·음성 만들기", "공부·자격증에 활용", "업무 자동화", "블로그·SNS·홍보", "나만의 앱·웹사이트 만들기", "기타"]},
    {"id": "q12", "num": "12", "part": 3, "type": "text", "rows": 3,
     "title": "AI를 배워 꼭 해 보고 싶은 일이 있다면 구체적으로 적어 주세요", "required": False,
     "hint": "예: \"가게 홍보 글을 쉽게 쓰고 싶다\", \"회의록을 자동으로 정리하고 싶다\""},
    {"id": "q13", "num": "13", "part": 3, "type": "multi", "title": "AI를 쓸 때 걱정되거나 어려운 점", "required": False, "other": True,
     "choices": ["무엇을 물어야 할지 모르겠다", "틀린 정보일까 걱정", "개인정보 유출", "비용", "영어나 용어가 어렵다",
                 "따라가기 벅찰 것 같다", "특별히 없다", "기타"]},

    {"id": "q14", "num": "14", "part": 4, "type": "single", "title": "수업 때 쓰실 기기", "required": True,
     "choices": ["노트북", "태블릿", "스마트폰만", "아직 모르겠다"]},
    {"id": "q15", "num": "15", "part": 4, "type": "single", "title": "원하는 수업 방식", "required": True,
     "choices": ["설명 위주로 천천히", "설명 반, 실습 반", "실습 위주로 직접 해 보며", "과제를 받아 혼자 해 오고 모여서 점검"]},
    {"id": "q16", "num": "16", "part": 4, "type": "text", "rows": 3, "title": "강사에게 바라는 점이나 하고 싶은 말", "required": False},
]

QMAP = {q["id"]: q for q in QUESTIONS}
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def other_index(q):
    """'기타' 글 칸이 붙는 보기 번호(0부터). 없으면 None."""
    if q.get("other"):
        return len(q["choices"]) - 1
    if "other_on" in q:
        return q["other_on"]
    return None


def parse_post(post):
    """POST → (이름, answers dict, errors {qid: 메시지})."""
    answers, errors = {}, {}
    for q in QUESTIONS:
        qid, t = q["id"], q["type"]
        if t == "text":
            v = (post.get(qid) or "").strip()[: 50 if qid == "q1" else 2000]
            if v:
                answers[qid] = v
            elif q["required"]:
                errors[qid] = "적어 주세요"
        elif t == "single":
            v = post.get(qid) or ""
            if v in q["choices"]:
                answers[qid] = v
                oi = other_index(q)
                if oi is not None and v == q["choices"][oi]:
                    o = (post.get(qid + "_other") or "").strip()[:200]
                    if o:
                        answers[qid + "_other"] = o
            elif q["required"]:
                errors[qid] = "하나를 골라 주세요"
        elif t == "multi":
            vs = [v for v in post.getlist(qid) if v in q["choices"]]
            vs = list(dict.fromkeys(vs))
            if q.get("max") and len(vs) > q["max"]:
                errors[qid] = f"최대 {q['max']}개까지 골라 주세요"
            if vs:
                answers[qid] = vs
                oi = other_index(q)
                if oi is not None and q["choices"][oi] in vs:
                    o = (post.get(qid + "_other") or "").strip()[:200]
                    if o:
                        answers[qid + "_other"] = o
            elif q["required"]:
                errors[qid] = "하나 이상 골라 주세요"
        elif t == "scale":
            for i, _ in enumerate(q["items"], 1):
                key = f"{qid}_{i}"
                v = post.get(key) or ""
                if v in q["choices"]:
                    answers[key] = v
    return answers.get("q1", ""), answers, errors


def csv_columns():
    """CSV 열: (머리글, 답 키)."""
    cols = []
    for q in QUESTIONS:
        if q["type"] == "scale":
            for i, it in enumerate(q["items"], 1):
                label = it["num"] or f"{q['num']}-{i}"
                cols.append((f"{label} {it['text']}", f"{q['id']}_{i}"))
        else:
            cols.append((f"{q['num']}. {q['title']}", q["id"]))
            if other_index(q) is not None:
                cols.append((f"{q['num']}. {q.get('other_label', '기타')}·내용", q["id"] + "_other"))
    return cols
