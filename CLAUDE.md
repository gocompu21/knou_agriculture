# CLAUDE.md

This file provides guidance when working with code in this repository.

## 호칭

사용자를 **대표님**이라고 부른다(사장님 아님).

대표님은 Claude 를 **안부장**이라고 부른다(앤트로픽의 '안' + 부장, 2026-09-29 대표님이 지어 줌). "안부장"은 Claude 를 가리킨다.

## 경험은 이 문서에 남긴다 (2026-10, 대표님과 나눈 이야기)

안부장(Claude)은 **대화하며 배우지 않는다.** 한 세션에서 고친 경험은 세션이 끝나면 사라지고,
다른 사용자의 Claude 에게도 전해지지 않는다(대화가 훗날 모델 학습에 쓰일지는 계정의
개인정보 설정에 달렸고, 쓰이더라도 곧바로 반영되지 않는다). **이 프로젝트에서 경험이 이어지는
길은 이 문서(와 여기서 가리키는 `docs/`)뿐이다** — 다음 세션의 안부장은 이 문서를 읽고 시작한다. 그래서:

- **이 문서는 세션마다 통째로 읽힌다 — 짧게 지킨다**(2026-10, 대표님과 하네스 이야기 끝에 나눔: 380KB 였다).
  한 기능의 상세가 길어지면 `docs/<주제>.md` 로 빼고 여기에는 **가리키는 줄과 꼭 지킬 것 몇 줄만** 남긴다.
  CAD(`docs/CAD.md`) · 실기 필답(`docs/실기필답.md`) · 영상(`docs/도면영상.md`) · 이미지 모델(`docs/GPT이미지.md`)이
  그렇게 나갔다. 그 기능을 고칠 때는 그 문서를 먼저 읽고, 경험도 그 문서에 적는다

- 기능을 고칠 때마다 **무엇을 왜 그렇게 했는지**와 **겪은 함정**을 해당 절에 적는다.
  결과만 적지 말고 "처음엔 이렇게 했다가 이래서 바꿨다"를 남긴다 — 그래야 같은 길을 다시 안 간다
- 이 CAD 는 일반 CAD 가 아니라 **실제 제도판을 화면으로 옮긴 것**이라 교과서에 없는 기준이 대부분이다.
  그 기준은 대표님의 실물 사진과 지적에서 나온다 — 사진은 눈대중 말고 화소를 세어 옮긴다
- **대표님 화면 그대로 재현해 확인한다.** 확대한 상태에서만 시험하면 놓친다 — 템플릿 귀 긋기는
  확대해서는 됐는데, 맞춤 배율(귀가 화면 3px)에서 곧은 변부터 대고 돌면 안 그어졌다. 아래쪽 가장자리
  띠는 svg 사각형 그대로 두었더니 상태줄에 가려 커서가 닿지 않았다
- 고치면 묻지 않고 커밋 → main → 서버 배포까지 한다

## 프로젝트 개요

한국방송통신대학교 농학과 학습동아리 **한울회 스터디 그룹**을 위한 웹 학습 시스템 프로젝트.
가칭은 **한울회 A+ 학습시스템**이다.

- 학과 사이트: https://agri.knou.ac.kr/agri/index.do
- 스터디 그룹: https://cafe.daum.net/hwhstudy

## 핵심 목표

기출문제를 반복적으로 풀고, 오답을 체계적으로 관리하여 시험 대비 성과를 높인다.

- 각 교과목은 학년별로 구분해서 운영한다.
- 기출문제 데이터는 2013~2019년 범위, 40개 과목 보유.
- 기출문제는 연도별 25~35문항으로 구성 (과목에 따라 다름).
- 학습 흐름은 `기출 풀이 -> 채점 -> 오답 저장 -> 오답 재풀이`로 설계한다.

## 기술 방향

- 프레임워크: Django
- 초기 구조: `03_1_model` 프로젝트의 폴더 패턴(`config`, `main`, `templates`)을 참조
- 메인 랜딩 페이지에서 시스템 목적, 학년/과목 구조, 기출 운영 방식, 학습 루프를 명확히 안내

## 데이터베이스 (PostgreSQL)

- DB: `knou_agriculture`
- User: `knou_user` / Password: `knou1234`

```sql
CREATE DATABASE knou_agriculture;
CREATE USER knou_user WITH PASSWORD 'knou1234';
ALTER ROLE knou_user SET client_encoding TO 'utf8';
ALTER ROLE knou_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE knou_user SET timezone TO 'Asia/Seoul';
GRANT ALL PRIVILEGES ON DATABASE knou_agriculture TO knou_user;
```

## 실행 명령

```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
```

## 데이터 현황

총 **8,940문제** (40개 과목, 2013~2019년 기말시험), 전체 AI 해설 생성 완료

### 과목 목록 (40개)

| 학년 | 과목 |
|------|------|
| 1학년 | 글쓰기, 농학원론, 생물과학, 생활과건강, 세계의역사, 숲과삶, 심리학에게묻다, 원예학, 인간과과학, 인간과교육, 재배학원론, 축산학, 컴퓨터의이해 |
| 2학년 | 농업생물화학, 농업유전학, 동서양고전의이해, 생활속의경제, 세상읽기와논술, 재배식물생리학, 철학의이해, 취미와예술, 한국사의이해 |
| 3학년 | 글쓰기, 농축산환경학, 동물사료학, 생물통계학, 생활원예, 세상읽기와논술, 식물의학, 식용작물학1, 원예작물학1, 인간과교육, 자원식물학, 재배식물육종학, 토양학, 푸드마케팅, 환경친화형농업 |
| 4학년 | 농업경영학, 농축산식품이용학, 생활과건강, 시설원예학, 식물분류학, 식용작물학2, 원예작물학2, 푸드마케팅 |

- 동명 과목 주의: 글쓰기(1·3학년), 생활과건강(1·4학년), 세상읽기와논술(2·3학년), 인간과교육(1·3학년), 푸드마케팅(3·4학년)

### 정답 구조

- `Question.answer`: CharField(max_length=10) — 문자열로 저장
- 단일 정답: `'1'`, `'2'`, `'3'`, `'4'`
- 복수 정답 (A~K): `'1,2'`, `'1,3'`, `'1,4'`, `'2,3'`, `'2,4'`, `'3,4'`, `'1,2,3'`, `'1,2,4'`, `'1,3,4'`, `'2,3,4'`, `'1,2,3,4'`
- 미확인: `'0'`
- 복수 정답은 올에이클래스 답안표에 A~K 코드로 명시된 경우만 해당 (101건, 전체의 약 1.1%)
- 정답 미확인(0) 문제: 0건 (전체 확인 완료)

## 기출문제 데이터 import

`data/` 디렉토리에 과목별 엑셀 파일(`.xlsx`)을 넣고 management command로 import한다.

```bash
# 특정 과목 파일만
python manage.py import_questions 토양학.xlsx

# data/ 디렉토리 전체
python manage.py import_questions
```

### 엑셀 파일 형식

| 컬럼명 | 설명 | 매핑 대상 |
|--------|------|-----------|
| 학년도 | 출제연도 (예: 2019) | Exam.year, Question.year |
| 시험종류 | 기말시험, 중간시험, 계절학기 | Exam.exam_type |
| 과목명 | 교과목 이름 | Subject.name |
| 학년 | 학년 (1~4) | Subject.grade |
| 문제번호 | 문항번호 | Question.number |
| 문제 | 문제 텍스트 | Question.text |
| 1항~4항 | 보기 ①~④ | Question.choice_1~4 |
| 답안 | 정답 (1~4 단일, A~K 복수) | Question.answer |

- `data/` 디렉토리는 `.gitignore`에 포함되어 git에 올라가지 않는다.
- `openpyxl` 패키지 필요: `pip install openpyxl`
- 답안의 A~K 코드는 import 시 자동으로 `"1,2"` 등 쉼표 구분 형식으로 변환

## 화학식·단위 자동 변환

import 시 `convert_formulas()` 함수가 텍스트의 화학식·단위를 유니코드 상·하첨자로 자동 변환한다.

| 원본 | 변환 | 규칙 |
|------|------|------|
| H2O | H₂O | 원소 뒤 아래첨자 |
| Ca2+ | Ca²⁺ | 2글자 원소 이온 전하 |
| PO43- | PO₄³⁻ | 다가 이온 (아래첨자+위첨자) |
| NO3- | NO₃⁻ | 아래첨자 + 전하 부호 |
| cm3 | cm³ | 단위 지수 |
| (OH)2 | (OH)₂ | 괄호 뒤 아래첨자 |

- 변환 로직: `exam/management/commands/import_questions.py` 내 `convert_formulas()`
- 재변환이 필요하면 `import_questions`를 다시 실행 (`update_or_create`로 기존 데이터 갱신)

## 웹 스크래핑으로 기출문제 추출

**올에이클래스**(allaclass.tistory.com)에서 과목별 기출문제를 스크래핑하여 엑셀로 생성할 수 있다.

### 일괄 스크래핑

```bash
# 전체 40개 과목 일괄 스크래핑 → data/*.xlsx 생성
python scrape_all.py
```

- `scrape_all.py`에 전체 과목의 URL이 정의되어 있음
- 과목 추가 시 `ALL_SUBJECTS` 리스트에 항목 추가

### 개별 스크래핑

`scrape_exam.py` 파일 상단의 변수와 `PAGES` 리스트를 수정한 뒤 실행한다.

```python
# scrape_exam.py 상단 수정
SUBJECT = '시설원예학'
EXAM_TYPE = '기말시험'

PAGES = [
    (2019, 4, 'https://allaclass.tistory.com/1239'),
    (2018, 4, 'https://allaclass.tistory.com/1238'),
    # ... (year, grade, url) 형태
]
```

```bash
python scrape_exam.py
python manage.py import_questions 시설원예학.xlsx
```

### 파싱 구조 (올에이클래스 HTML)

| 요소 | CSS 클래스 | 내용 |
|------|-----------|------|
| 문제 텍스트 | `allaQuestionTr` | `<td>` 안에 "번호+문제" 결합 |
| 보기 | `allaAnswerTr` | 문제당 5개 (4개 보기 + "모름") |
| 정답 | `allaAnswerTableDiv` 내 `<td>` | 문제번호-정답 쌍으로 파싱 |

- 문제번호가 36~70으로 시작하는 경우 오프셋 적용하여 1~35로 변환
- 정답 추출은 반드시 `allaAnswerTableDiv` 내에서만 수행 (HTML 앞부분의 "중복답안 가이드" 범례 테이블 제외)
- 범례 테이블에는 A~K 코드 설명이 있지만 이것은 정답 데이터가 아님

### 다른 과목 추출 절차

1. allaclass.tistory.com에서 과목 태그 페이지 찾기
   - 예: `https://allaclass.tistory.com/tag/토양학 기말시험`
2. 각 연도별 게시글 URL 확인
3. `scrape_all.py`의 `ALL_SUBJECTS`에 항목 추가
4. 실행: `python scrape_all.py`
5. import: `python manage.py import_questions`

## AI 해설 생성 (Gemini API)

Gemini API를 사용하여 기출문제에 대한 해설을 자동 생성한다.

### 사전 준비

1. `.env` 파일에 `GEMINI_API_KEY` 설정
2. 패키지 설치: `pip install google-genai python-dotenv`

### 사용법

```bash
# 전체 문제 해설 생성 (해설 없는 문제만)
python manage.py generate_explanations

# 과목/학년/연도 필터
python manage.py generate_explanations --subject 토양학 --grade 3 --year 2019

# 기존 해설 덮어쓰기
python manage.py generate_explanations --force

# 대상 문제 미리보기
python manage.py generate_explanations --dry-run

# 모델 변경
python manage.py generate_explanations --model gemini-3.8-flash
```

### 병렬 해설 생성

```bash
# 전과목 동시 병렬 실행 (45개 프로세스)
python generate_all.py
```

- `generate_all.py`: 과목별 subprocess로 `generate_explanations`를 병렬 실행
- `WORKERS` 변수로 동시 실행 수 조절 (기본 45)
- `DELAY` 변수로 API 호출 간격 조절 (기본 1.0초)
- 동명 과목은 `--grade`로 자동 구분
- Windows 환경에서 CP949 인코딩 에러 방지를 위해 UTF-8 출력 설정 포함
- 8,940문제 전체 해설 생성 완료 (당시 gemini-2.5-flash 사용)
- **기본 모델은 `settings.GEMINI_EXPLAIN_MODEL`**(`gemini-3.8-flash`). `--model` 로 덮어쓴다

### 저장 방식

| Gemini 응답 | DB 필드 | 설명 |
|-------------|---------|------|
| 정답설명 | `explanation` | 정답에 대한 종합 설명 |
| 보기① 해설 | `choice_1_exp` | 선지별 해설 |
| 보기② 해설 | `choice_2_exp` | 선지별 해설 |
| 보기③ 해설 | `choice_3_exp` | 선지별 해설 |
| 보기④ 해설 | `choice_4_exp` | 선지별 해설 |

- 정답 선지의 `choice_X_exp`에는 정답설명이 저장된다 (복수 정답이면 해당 선지 모두)

## 관리 페이지 구성

관리 메뉴(`/manage/subjects/`)에서 탭 네비게이션으로 접근한다. (스태프 전용)

| 페이지 | URL | 설명 |
|--------|-----|------|
| 교과목 관리 | `/manage/subjects/` | CRUD |
| 시험 관리 | `/exam/manage/` | CRUD |
| 문제 관리 | `/exam/manage/questions/` | 교과목 → 시험 선택 → 문제 조회 |
| 채점관리 | `/gisa/manage/grading/` | 실기 필답 채점 세션 목록(자격증·모드·이름 검색) → 줄을 누르면 그 회원의 채점 결과. 스태프는 남의 세션도 열 수 있고(`_result_session`), 그때는 점수 입력칸이 잠긴다(`admin_view`) |

## 페이지 구성

### 메인/시험 앱 (방송대 기출)
- `templates/main/index.html`: 한울회 A+ 학습시스템 홈페이지
- `templates/base.html`: 공통 레이아웃 (favicon, PWA manifest, apple-touch-icon 포함)
- `templates/main/subject_detail.html`: 과목 상세 (탭: 쪽집게노트/기출학습/기출풀기/모의고사/오답/시험이력/최신기출)
- `templates/exam/study_mode.html`: 학습모드 (기출 풀이 + 채점, `from_tab` 파라미터로 기출학습/최신기출 구분)
- `templates/exam/exam_take.html`: 풀이모드 (OMR 카드 포함)
- `templates/exam/mock_exam_take.html`: 모의고사 (랜덤 25문제)
- `templates/exam/wrong_answers.html`: 오답노트 (세션별/전체)
- `templates/exam/exam_result.html`: 채점 결과
- `main/views.py`, `main/urls.py`: 홈 라우팅, 최신기출 CRUD, API
- `exam/views.py`, `exam/urls.py`: 시험/문제 관련 뷰

### 기사시험 앱 (자격증 기출)
- `templates/gisa/certification_list.html`: 자격증 목록
- `templates/gisa/certification_detail.html`: 자격증 상세 (탭: 쪽집게노트/기출학습/기출고사/모의고사/오답노트/시험이력)
- `templates/gisa/study_mode.html`: 학습모드 (교재 학습 겸용)
- `templates/gisa/exam_take.html`: 풀이모드 (OMR 카드 포함)
- `templates/gisa/mock_exam_take.html`: 모의고사 (과목별 20문제)
- `templates/gisa/wrong_answers.html`: 오답노트
- `templates/gisa/exam_result.html`: 채점 결과
- `gisa/views.py`, `gisa/urls.py`: 기사시험 관련 뷰

## PWA / 홈 화면 바로가기

- `static/manifest.json`: 웹 앱 매니페스트 (홈 화면 추가 시 앱 아이콘/이름 설정)
- `static/images/knou_favicon.png`: 파비콘 및 홈 화면 아이콘
- `base.html`에 favicon, apple-touch-icon, manifest, theme-color 메타태그 설정 완료
- 모바일 브라우저에서 "홈 화면에 추가" → "한울회 A+" 이름의 바로가기 생성

## 최신기출 탭 (subject_detail.html)

과목 상세 페이지의 "최신기출" 탭 (year >= 2020)에서 문제를 등록하고 관리한다.

### 서브탭 구조

- **신규 등록** (기본): 직접 문제/보기/정답/해설을 입력하여 등록
- **기존 기출 출제**: 기존 기출 DB(2013~2019)에서 문제를 선택하여 최신기출로 복사 등록
  - 출제연도 선택 → 문항 선택 → 미리보기 → 등록

### 관련 뷰/API

| URL | 뷰 | 설명 |
|-----|-----|------|
| `subjects/<pk>/latest/create/` | `latest_question_create` | 신규 문제 등록 (POST) |
| `subjects/<pk>/latest/clone/` | `latest_question_clone` | 기존 문제 복사 등록 (POST) |
| `subjects/<pk>/api/years/` | `api_existing_years` | 해당 과목의 기존 기출 연도 목록 (JSON) |
| `subjects/<pk>/api/questions/<year>/` | `api_existing_questions` | 해당 연도 문항 목록 (JSON) |

### 동작 규칙

- 연도 기본값: 현재 연도 (`new Date().getFullYear()`)
- 등록 후 연도 유지: 리다이렉트 시 `last_year` 파라미터로 이전 연도 전달
- 기존 기출 출제 등록 후 서브탭 유지: `sub=existing` 파라미터로 서브탭 상태 복원
- 입력란은 항상 표시 (토글 없음)

## 최신기출 데이터 EC2 배포

로컬에서 추출한 최신기출을 EC2에 배포하는 방법:

```bash
# 1. 로컬: JSON 추출 (pk 없이 natural key 기반)
python -c "
import os, django, json, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
sys.stdout.reconfigure(encoding='utf-8')
from exam.models import Question
qs = Question.objects.filter(subject__name='식물의학', year__in=[2024, 2025])
data = []
for q in qs:
    data.append({
        'subject_name': q.subject.name, 'year': q.year, 'number': q.number,
        'text': q.text, 'choice_1': q.choice_1, 'choice_2': q.choice_2,
        'choice_3': q.choice_3, 'choice_4': q.choice_4, 'answer': q.answer,
        'explanation': q.explanation, 'choice_1_exp': q.choice_1_exp,
        'choice_2_exp': q.choice_2_exp, 'choice_3_exp': q.choice_3_exp,
        'choice_4_exp': q.choice_4_exp,
    })
with open('식물의학_latest.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

# 2. git push 후 EC2에서:
git pull
python load_latest.py 식물의학_latest.json
```

- `load_latest.py`: `update_or_create` 기반 import 스크립트 (중복 pk 충돌 없음)
- `loaddata`는 pk 충돌 시 실패하므로 `load_latest.py` 사용 권장
- `(subject, year, number)` 기준: 있으면 업데이트, 없으면 신규 생성

## 모바일 UI 최적화

### 풀이모드/모의고사 (exam_take.html, mock_exam_take.html)

- `<form>` 태그에 `class="exam-form"` 사용 (inline style 금지)
- 데스크톱: `display: flex` (좌: 문제, 우: OMR)
- 모바일 (768px 이하): `display: block`, OMR 숨김, 모바일 헤더 표시

### 과목 상세 (subject_detail.html)

- 헤더: 다크그린 그래디언트 hero 스타일, 흰색 텍스트
- 탭 네비게이션: 가로 스크롤, 스크롤바 숨김, 활성 탭 자동 스크롤
- 오답 요약: 세로 레이아웃, 중앙 정렬
- 세션 카드: CSS Grid 2행 컴팩트 레이아웃
- 최신기출: 풀 너비 입력란, 녹색 포커스 스타일

### 오답노트 (wrong_answers.html)

- 문제 텍스트: hanging indent (`padding-left: 1.3em`, `text-indent: -1.3em`)
- 보기: flex 레이아웃 (`.wq-choice` flex + `.wq-choice-text` wrapper)
- 정답: 원번호 반전 (`.q-mark.correct-mark`, `background: #333; color: #fff`)
- 선택한 답: `← 내 답` 빨간 라벨 (`.my-pick`)
- 해설: `→` 화살표, 정답 해설 노란 하이라이트
- 문제 간 간격 최소화 (`padding: 4px 20px 0`)

## 기사시험 앱 (gisa)

국가기술자격 기사시험 기출문제 학습 시스템. URL prefix: `/gisa/`

### 모델 구조 (gisa/models.py)

| 모델 | 설명 | 주요 필드 |
|------|------|-----------|
| `Certification` | 자격증 | name, category(기사/산업기사/기능사/기능장/기술사) |
| `GisaExam` | 시험회차 | certification(FK), year, round, exam_type(필기/실기) |
| `GisaSubject` | 과목 | certification(FK), name, order |
| `GisaQuestion` | 기출문제 | exam(FK), subject(FK), number, text, choice_1~4, answer, explanation, choice_X_exp |
| `GisaTextbook` | 쪽집게 노트 | certification(FK), subject(FK), content(마크다운), updated_at |
| `GisaAttempt` | 풀이기록 | user(FK), question(FK), selected, is_correct, mode(exam/mock/wrong_retry), session_id |

- `GisaQuestion.answer`: CharField — `'1'`~`'4'` 단일 정답, `'0'` 미확인
- unique_together: `(exam, number)` → 회차별 문항번호 고유

### 기출문제 데이터 import

텍스트 파일 기반 import. 데이터 원본: `kisa_exam/` 디렉토리 (프로젝트 형제 폴더)

```bash
python manage.py import_gisa_questions 식물보호기사20111002.txt
```

- 텍스트 파일 형식: 1행에 메타정보 (`식물보호기사 2011년 10월 02일 필기 기출문제`)
- 과목 구분: `===...N과목 : 과목명...===` 패턴
- 문제: `번호. 문제텍스트 ① ② ③ ④` 형식
- 정답표: `정답표` 섹션 아래 `번호: ①` 형태
- `update_or_create`로 중복 시 갱신

### AI 해설 생성 (Gemini API)

```bash
python manage.py generate_gisa_explanations
python manage.py generate_gisa_explanations --cert 식물보호 --subject 식물병리학
python manage.py generate_gisa_explanations --year 2011 --force
python manage.py generate_gisa_explanations --dry-run
```

- 식물보호기사 660문제 전체 해설 생성 완료
- 식물보호산업기사 2,880문제 전체 해설 생성 완료
- Pydantic 모델(`QuestionExplanation`)로 구조화 응답
- 정답 선지의 `choice_X_exp`에 정답설명 저장

### 페이지 구성

| URL | 뷰 | 템플릿 | 설명 |
|-----|-----|--------|------|
| `/gisa/` | `certification_list` | `certification_list.html` | 자격증 목록 |
| `/gisa/<id>/` | `certification_detail` | `certification_detail.html` | 자격증 상세 (탭 UI) |
| `/gisa/<id>/study/<exam>/<subj>/` | `study_mode` | `study_mode.html` | 학습모드 |
| `/gisa/<id>/take/<exam>/` | `exam_take` | `exam_take.html` | 풀이모드 |
| `/gisa/<id>/mock/` | `mock_exam_take` | `mock_exam_take.html` | 모의고사 (과목별 20문제) |
| `/gisa/<id>/wrong/` | `wrong_answers` | `wrong_answers.html` | 오답노트 |
| `/gisa/<id>/textbook/study/` | `textbook_study` | `study_mode.html` (재사용) | 교재 관련 문제 학습 |
| `/gisa/manage/` | `gisa_question_manage` | `gisa_question_manage.html` | 기사문제 관리 (파싱/등록/수정) |
| `/gisa/manage/question/<pk>/update/` | `gisa_question_update` | — (JSON API) | 문제 수정 (staff only) |
| `/gisa/manage/question/<pk>/generate-exp/` | `gisa_question_generate_exp` | — (JSON API) | Gemini 해설 생성 (staff only) |

### certification_detail 탭 구조

탭 순서: **쪽집게 노트** → 기출학습 → 기출고사 → 모의고사 → 오답노트 → 시험이력

- 기본 활성 탭: `textbook` (쪽집게 노트)
- URL 파라미터: `?tab=textbook`, `?tab=study`, `?tab=exam`, `?tab=mock`, `?tab=wrong`, `?tab=history`

### 쪽집게 노트 탭 (textbook)

핵심정리 마크다운을 DB(`GisaTextbook`)에서 로드하여 아코디언 UI로 표시하고, 관련 기출문제를 학습할 수 있다.

**데이터 소스**: `GisaTextbook` 모델 (DB 저장, 과목별 1건)

**현재 완성된 교재** (5과목 전체 완성, 교재형 서술 스타일):
- 식물병리학 (14장 + 부록, 660문제 100% 커버리지)
- 농림해충학 (13장 + 부록 8개 표, 660문제 100% 커버리지, 3430줄)
- 재배학원론 (12장 + 부록, 660문제 100% 커버리지, 3735줄)
- 농약학 (10장 + 부록, 660문제 100% 커버리지, 3334줄)
- 잡초방제학 (10장 + 부록, 680문제 100% 커버리지, 2200줄)

**마크다운 파서** (`gisa/views.py` → `parse_study_guide()`):
- `## 제N장.` → 장(chapter)
- `### N.M` → 절(section)
- `#### N.M.K` → 항(subsection)
- `**관련 문제**: (YYYY-R-N)` → 관련 기출문제 참조
- 문제 참조 형식: `YYYY-R-N` (연도-회차-문항번호)
- bullet(`-`) → `<li>`, 마크다운 테이블 → `<table class='tb-summary'>`
- 일반 텍스트(paragraph) → `<p>` (서술형 교재 스타일 지원)
- 볼드(`**...**`) → `<strong>`, 이탤릭(`*...*`) → `<em>`
- 소제목 형식: `[ **소제목** ]` — `#####` 대신 볼드+대괄호 형태로 시각적 구분 (파서가 `#####`를 별도 계층으로 처리하지 않으므로)

**UI 구성**:
```
[식물병리학] [농림해충학] [재배학원론] [농약학] [잡초방제학]  ← 과목 버튼
▼ 제1장. 식물병의 기초 개념                                  ← 아코디언 헤더
  ├ 1.1 병의 정의와 병 삼각형                                ← 절 (클릭→내용 펼침)
  │   • 핵심정리 내용...
  │   관련문제: (2011-1-5) (2012-2-2) ...                   ← 배지, 클릭→학습모드
```

- 과목 버튼: pill 스타일, 선택 시 `#1b4332` 배경, 5과목 전체 활성화
- URL: `?tab=textbook&subject=식물병리학`
- 관련문제 배지 클릭 → `textbook_study` 뷰로 이동 (GET/POST로 `ref` 파라미터 전달)
- `textbook_study` 뷰: `YYYY-R-N` refs를 `(exam__year, exam__round, number)` 조건으로 DB 조회
- 내용 영역: `.content-box`로 박싱 (연한 녹색 배경 `#f9fbf9`, 테두리 `#dce8dc`, 둥근 모서리)
- **모바일(480px 이하)에서는 박싱 제거** — 공간 절약을 위해 배경/테두리/패딩 모두 none

### 주요 파일 구조 (gisa 앱)

```
gisa/
├── models.py           # Certification, GisaExam, GisaSubject, GisaQuestion, GisaTextbook, GisaAttempt
├── views.py            # parse_study_guide(), certification_list/detail, study/exam/mock/wrong 뷰
├── urls.py             # app_name='gisa', 13개 URL 패턴
├── admin.py            # 5개 모델 Admin 등록
└── management/commands/
    ├── import_gisa_questions.py       # 텍스트 파일 → DB import
    ├── import_eco_questions.py        # 자연생태복원기사 파싱결과 → DB import
    └── generate_gisa_explanations.py  # Gemini 해설 생성

templates/gisa/
├── certification_list.html    # 자격증 목록
├── certification_detail.html  # 자격증 상세 (교재/학습/풀이/모의/오답/이력 탭)
├── gisa_question_manage.html  # 기사문제 관리 (파싱/등록/수정)
├── study_mode.html            # 학습모드 (교재 학습 겸용, 관리자 인라인 편집)
├── exam_take.html             # 풀이모드
├── mock_exam_take.html        # 모의고사
├── exam_result.html           # 채점 결과
└── wrong_answers.html         # 오답노트

data/
├── 식물병리학_핵심정리.md     # 교재 데이터 (gitignore)
├── 농림해충학_핵심정리.md     # 교재 데이터 (gitignore)
└── entomology_questions.json  # 농림해충학 660문제 JSON (장별 분류용)
```

## 주요 파일 구조

```
knou_agriculture/
├── config/             # Django 설정
├── main/               # 메인 앱 (Subject 모델, 홈)
│   ├── views.py        # subject_detail, 최신기출 CRUD, API 뷰
│   └── urls.py         # URL 라우팅
├── exam/               # 시험 앱
│   ├── models.py       # Exam, Question, Attempt 모델
│   ├── views.py        # 학습모드, 오답노트, 관리 뷰
│   └── management/commands/
│       ├── import_questions.py       # 엑셀 → DB import
│       └── generate_explanations.py  # Gemini 해설 생성
├── gisa/               # 기사시험 앱
│   ├── models.py       # Certification, GisaExam, GisaSubject, GisaQuestion, GisaTextbook, GisaAttempt
│   ├── views.py        # parse_study_guide(), 학습/풀이/모의/오답/교재 뷰
│   └── management/commands/
│       ├── import_gisa_questions.py       # 텍스트 → DB import
│       ├── import_eco_questions.py        # 자연생태복원기사 → DB import
│       └── generate_gisa_explanations.py  # Gemini 해설 생성
├── accounts/           # 회원 관리 앱
├── templates/          # HTML 템플릿
├── static/
│   ├── images/         # 로고, 파비콘
│   └── manifest.json   # PWA 매니페스트
├── scrape_exam.py      # 개별 과목 스크래핑
├── scrape_all.py       # 전체 과목 일괄 스크래핑
├── generate_all.py     # 전체 과목 병렬 해설 생성 (방송대)
├── generate_sanup_explanations.py  # 식물보호산업기사 병렬 해설 생성
├── load_latest.py      # 최신기출 JSON → DB import (update_or_create)
├── parse_eco.py        # 자연생태복원기사 PDF 파서 (텍스트+이미지 자동 추출)
├── generate_eco_explanations.py    # 자연생태복원기사 병렬 해설 생성
├── deploy_eco.py       # 자연생태복원기사 문항·해설·이미지 export/load
├── load_eco_textbook.py            # 쪽집게 노트 병합+검증+저장 (로컬)
├── load_eco_textbook_deploy.py     # 쪽집게 노트 서버 적재
└── data/               # 엑셀 파일 + 핵심정리 마크다운 (gitignore)
    └── comcbt/         # 식물보호산업기사·조경기사·자연생태복원기사 PDF (comcbt.com 원본)
```

## 알려진 주의사항

### 방송대 기출 (exam 앱)
- 올에이클래스 HTML에는 "중복답안 가이드" 범례 테이블이 답안표 앞에 존재함. 정답 파싱 시 반드시 `allaAnswerTableDiv` 영역 내에서만 추출해야 함 (범례의 A~K 코드가 정답으로 오인될 수 있음)
- 동명 과목(글쓰기 등)이 여러 학년에 존재하므로 `--grade` 옵션으로 구분 필요
- `Question.answer`는 CharField이며 `'1,2'` 형태의 문자열로 복수 정답을 표현함 (IntegerField 아님)
- 학습모드 JS에서 정답 비교 시 `split(',')` + `indexOf`로 처리 (parseInt 사용 금지)

### 개발 서버 — `--noreload` 면 템플릿 수정이 반영되지 않는다

Django 는 DEBUG 와 무관하게 템플릿 로더를 `cached.Loader` 로 감싸고, **autoreload 훅이
캐시를 비운다.** `runserver --noreload` 로 띄우면 그 훅이 없어 템플릿을 고쳐도 **첫 요청
때 읽은 것이 계속 나온다**(파이썬 코드도 물론 그대로다). 고친 화면을 확인하려면 서버를
다시 띄워야 한다 — CSS 를 고쳤는데 화면이 그대로여서 한참 헤맨 적이 있다.

Windows 에서는 `pkill` 이 듣지 않는다. 이렇게 지운다:

```bash
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | Where-Object { \$_.CommandLine -like '*runserver 8099*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"
```

죽이지 않고 새로 띄우면 **옛 프로세스가 포트를 물고 있어 옛 코드가 응답한다**(실제로
같은 포트에 네 벌이 떠 있었다).

### text-indent 는 상속된다 — 블록 박스마다 0 으로 되돌릴 것

실기 화면은 문제번호 정렬로 `padding-left:20px; text-indent:-20px`(매달린 들여쓰기)를
쓴다. `text-indent` 는 **상속되는 속성**이라 그 안에 들어가는 블록의 **첫 줄만** 왼쪽으로
20px 끌려 나간다. 세 번 겪었다 — `q-box`(상자), `.pt::before`(채점 포인트 ✓),
`q-eq`·`q-calc`·`.ans`(답 영역)·`q-svg`(그림 래퍼). 새 블록을 만들면 `text-indent:0` 을 함께 둔다.

증상이 헷갈린다: 박스 안 **둘째 줄부터가 들여쓰기된 것처럼** 보이고, 답 영역의
'계산)'·'답)' 첫 글자가 왼쪽 띠에 가려 잘려 보인다. 그림은 왼쪽으로 밀린 만큼
오른쪽에 빈 스크롤 영역이 생겨, 폭 300px 짜리 SVG 인데도 가로 스크롤바가 그려진다.

### Django 템플릿 주의사항
- **Django 템플릿 태그(`{% %}`, `{{ }}`)는 절대 여러 줄에 걸쳐 분리하지 말 것.** Django의 템플릿 렉서는 `re.DOTALL` 없이 토큰을 파싱하므로, `{%`와 `%}` 또는 `{{`와 `}}`가 서로 다른 줄에 있으면 인식하지 못한다. 예: `{{ q.exam.round }}`를 두 줄로 나누면 변수가 렌더링되지 않고 그대로 출력됨, `{% endif %}`를 두 줄로 나누면 `TemplateSyntaxError` 발생.
- HTML 포매터(Prettier 등)가 자동으로 줄바꿈할 수 있으므로 템플릿 태그가 포함된 라인은 주의 필요

### 기사시험 (gisa 앱)
- 기출문제 텍스트 파일은 `kisa_exam/` 디렉토리에 위치 (프로젝트 형제 폴더, `../kisa_exam/`)
- `GisaQuestion.answer`는 단일 정답만 (`'1'`~`'4'`), 복수 정답 없음
- 핵심정리 마크다운의 문제 참조 형식: `YYYY-R-N` (연도-회차-문항번호), 예: `2011-1-5`
- `parse_study_guide()`는 `certification_detail` 뷰에서 `tab=textbook`일 때만 호출
- 쪽집게 노트 데이터는 `GisaTextbook` 모델(DB)에서 로드 (파일 기반에서 DB 기반으로 전환 완료)
- `parse_study_guide()`는 파일 경로 또는 콘텐츠 문자열 모두 지원 (하위 호환)
- 과목 전환 시 DB에 해당 과목의 `GisaTextbook` 레코드가 없으면 빈 목록 표시
- 5과목 전체 핵심정리 완성: 식물병리학·농림해충학·재배학원론·농약학·잡초방제학 (각 660/680문제 100%)
- 핵심정리 생성 작업 패턴: DB에서 문제 JSON 추출 → 장 단위 병렬 에이전트로 초안 생성 → 통합 → 커버리지 검증 → 누락 보완 → 100% 달성 → UI pill 활성화

## 최신기출 데이터 관리 및 카페 크롤링 연동

웹 스크래핑 외에 네이버 카페(스터디 그룹) 게시판의 비정형 데이터를 Gemini API로 분석하여 최신기출 문제로 구축하는 파이프라인.

### 카페글 추출 (카페글_엑셀변환.py)
- 비정형 텍스트(카페글_결과.txt)를 Gemini 2.5 Flash 모델로 순회 분석
- 추출 내역을 구조화(과목, 일자, 문제번호, 문제, 보기, 답)하여 `카페글_시험문제.json` / `.xlsx` 로 저장
- 과목명 불일치 데이터(인간과 과학 → 인간과과학 등) 자동 매핑 및 필터링 수행

### JSON → 최신기출 DB 마이그레이션
- 연도(`year`)를 자동 인식하여 2024/2025 등 최신기출로 분류
- 텍스트 덩어리인 '보기'를 `choice_1 ~ choice_4` 필드로 분할
- 추출된 '답' 문자열은 정답 유추의 불확실성을 고려하여 `explanation`(해설) 필드에 먼저 보존 (`answer`는 '0'으로 초기화)
- 2020년 이후 전체 최신기출은 2,500+ 문항 확보 중, 과목·연도별 현황 통계(엑셀) 추출 파이프라인 구축됨

## 교재형 서술 스타일 전환

### 개요

핵심정리 마크다운의 콘텐츠 형식을 **나열형 불렛** → **교재형 서술문**으로 전환하는 작업.

### 변환 규칙

1. `**핵심 정리**` 라벨 제거
2. 불렛 나열 → 자연스러운 문장으로 서술. 교재를 읽듯 흐름이 이어져야 함
3. 불렛(`- `)은 열거가 필요한 곳(분류 항목, 비교 리스트)에서만 사용
4. 내용이 충분한 절에는 `#### N.M.K 소제목`으로 하위 구조화
5. 핵심 용어는 `**볼드**`로 강조 유지
6. 기존 내용 100% 포함 + 자연스러운 흐름을 위해 부연 설명 추가 가능
7. `**관련 문제**: (YYYY-R-N), ...` 줄은 절대 변경 금지
8. 마크다운 테이블, 키워드 요약 테이블은 그대로 유지

### 전환 현황

| 과목 | 상태 | 비고 |
|------|------|------|
| 식물병리학 | 완료 | 2,460줄, 684개 문제 참조 100% 보존 |
| 농림해충학 | 미전환 | 나열형 |
| 재배학원론 | 미전환 | 나열형 |
| 농약학 | 미전환 | 나열형 |
| 잡초방제학 | 미전환 | 나열형 |

### 파서 지원

`parse_study_guide()`에 단락(paragraph) 텍스트 지원 추가 완료:
- `- `로 시작하지 않는 일반 텍스트 줄 → `<p>` 태그로 변환
- 연속된 텍스트 줄은 하나의 `<p>`로 결합
- `.content-box p` CSS: `font-size: 0.88rem`, `line-height: 1.75`, `text-align: justify`, `color: #333`
- `.content-box p strong` CSS: `color: #1b4332` (진한 녹색 강조)

## 기사시험 기출고사 페이지 (exam_take.html)

`templates/gisa/exam_take.html`은 독립 HTML (base.html 미상속)로 구성.

- mock_exam_take.html과 동일한 구조: OMR 버블 마킹, 타이머, 과목 구분선
- 색상: 남색 계열(`#1a237e`, `#7986cb`) — 모의고사(주황/녹색)와 구분
- `selectAnswer()`, `selectBubble()`, `highlightQuestionChoice()` JS 함수

## 시험이력 탭 (API 기반 무한 스크롤)

### history_api 뷰

- URL: `/gisa/<cert_id>/api/history/`
- 세션별 집계 쿼리 + 과목별 점수 산정
- 페이지네이션: `?page=N` (기본 20건)

### 과목별 점수 산정

- 기출고사/모의고사: 과목별 100점 (정답수/20 × 100)
- 평균 점수 표시
- 합격 조건: 평균 60점 이상 **AND** 모든 과목 40점 이상
- 색상: 60점 이상 녹색, 40~59점 노랑, 40점 미만 회색

## 정답/오답 표시 UI 규칙

전 페이지에서 통일된 표시 방식을 따른다. gisa/exam 앱 모두 동일한 규칙 적용.

### 채점 결과 O/X 마크 (exam_result)

문제번호에 직접 O/X를 표시한다 (별도 `grade-mark` div가 아닌 `::after` 가상요소 방식).

| 요소 | 스타일 | 설명 |
|------|--------|------|
| 정답 O | `.q-number.q-correct::after` — 파란 손그림 동그라미 (`border: 2.5px solid #1565c0`, 비대칭 border-radius) | 문제번호 위에 표시 |
| 오답 X | `.q-number.q-wrong::after` — 빨간 볼드 ✕ (`color: #c62828`, `font-size: 1.6em`) | 문제번호 위에 표시 |
| 미응답 | 오답과 동일하게 X 표시 (skipped도 틀린 문제로 처리) | |

- O 마크 위치: `top: 0.8em; left: 35%` (line-height 1.6의 중앙)
- X 마크 위치: `top: 0.55em; left: 30%` (시각적 보정)
- X 마크가 문제번호를 가리지 않도록 z-index 레이어링: `::after { z-index: 0 }`, `.q-number.q-wrong { z-index: 1 }`, X 색상 반투명 `rgba(198, 40, 40, 0.7)`
- 오답 재풀이(`is_wrong_retry`)에서는 O/X 마크 미표시
- gisa/exam_result.html, exam/exam_result.html 모두 동일 적용

### 선지 원번호 표시 (5곳 통일)

| 상황 | 스타일 | CSS 클래스 |
|------|--------|-----------|
| 정답 문제 - 정답 선지 | 검은색 반전 | `.correct-mark` (`background: #333; color: #fff`) |
| 오답 문제 - 내가 선택한 선지 | 검은색 반전 | `.wrong-mark` (`background: #333; color: #fff`) |
| 오답 문제 - 정답 선지 | 빨간색 반전 | `.wrong-q-correct` (`background: #d93025; color: #fff`) |

적용 페이지 (5곳):
- `gisa/exam_result.html` — 오답 문제에만 조건부 적용 (`{% if not r.is_correct %} wrong-q-correct{% endif %}`)
- `gisa/wrong_answers.html` — 전체 문제가 오답이므로 무조건 적용
- `gisa/certification_detail.html` (오답 탭) — 전체 문제가 오답이므로 무조건 적용
- `exam/exam_result.html` — 오답 문제에만 조건부 적용
- `exam/wrong_answers.html` — 전체 문제가 오답이므로 무조건 적용

### 기타 표시 요소

| 요소 | 스타일 | 적용 페이지 |
|------|--------|------------|
| 정답 표시 | 빨간 동그라미 (`.choice-num.correct::before`, `border: 3px solid #d93025`) | study_mode |
| 선택한 답 | 원번호 반전 (`.choice-num.picked`, `background: #333; color: #fff`) | study_mode |
| 선택한 답 | `← 내 답` 빨간 라벨 (`.my-pick`, `color: #d93025`) | wrong tab, wrong_answers, exam_result |
| 노트 제외 | "노트 X" 형태 (텍스트 먼저, X 아이콘 뒤) | wrong tab |

### 문제 간 간격

- **study_mode (gisa)**: 카드 박스 없음 (`border: none; box-shadow: none`), 간격 최소화 (`padding: 4px 20px 0`)
- **wrong_answers (gisa)**: 간격 최소화 (`padding: 4px 20px 0`)
- **wrong tab (certification_detail)**: 인라인 오답 표시, 과목별 필터링 (전체/5과목)

### 오답노트 탭 (certification_detail ?tab=wrong)

- 오답 내용이 탭 내에 인라인으로 표시됨 (별도 페이지 아님)
- 과목 필터: 전체/식물병리학/농림해충학/재배학원론/농약학/잡초방제학 pill 버튼
- "다시 도전" 버튼: 선택된 과목 필터를 `?subject=` 파라미터로 전달
- 오답 재풀이 헤더: `{과목명} 오답 재풀이 {N}문항` 형식

### 방송대 기출 (exam 앱)

- study_mode: 체크마크 이미지(`check_mark_black.png`) + 빨간 동그라미(정답) 방식 유지
- 원번호: Unicode ①②③④ (`&#9312;`~`&#9315;`) 사용

### UI

- 무한 스크롤: 내부 컨테이너(`max-height:60vh; overflow-y:auto`)의 scroll 이벤트 감지
- 삭제: 쓰레기통 SVG 아이콘 (배경 없음)
- 일시: 상대 시간 표시 (`timeAgo()` 함수 — 분/시간/일/개월/년 전)
- 모의고사 배지: 녹색 톤, 기출고사 배지: 남색 톤
- 전체 기록 삭제 버튼: 하단 배치

## 시험이력 탭 테이블 디자인 (history-table)

시험이력 탭을 카드 대신 **테이블** 형태로 렌더링.

### 컬럼 구성

| 컬럼 | 너비 | 내용 |
|------|------|------|
| 모드 | 70px | 기출고사/모의고사/오답재풀이 배지 (`.session-mode.mode-{exam|mock|wrong_retry}`) |
| 평균 | 70px | 큰 점수 숫자 (합격 시 녹색 `#1b5e20`) |
| 과목별 점수 | auto | pill 형태(`.ht-subj`)로 과목명 + 점수 표시. 60↑ 녹색, 40~59 주황, <40 빨강 |
| 합격 | 60px | `.ht-pass.pass`(녹색 배경) / `.ht-pass.fail`(회색 테두리) |
| 일시 | 100px | 날짜 + 상대시간 |
| 액션 | 120px | 오답 버튼 + 삭제 아이콘 |

### 스타일 규칙

- 헤더: `background: #1b4332; color: #fff; position: sticky; top: 0`
- 행: `border-bottom: 1px solid #eee`, hover 시 `background: #fafafa`
- 모바일: `.history-table { min-width: 600px }`로 가로 스크롤 대응

### 세션 삭제 후 탭 유지

- `session_delete`, `session_delete_all` 모두 `?tab=history`로 리다이렉트
- 기존에는 `?tab=wrong`으로 이동하던 문제 수정

## 모의고사 학습모드 (mock_exam_take)

모의고사 페이지 상단 우측에 **학습모드 토글** 체크박스.

### 동작

| 상태 | 선지 선택 시 |
|------|------------|
| **OFF** (기본) | OMR 마킹만. 스크롤 이동 |
| **ON** (학습모드) | 즉시 채점 + 해설 표시, OMR 스크롤 안 함 |

### 학습모드 채점 UI (exam_result와 동일)

- 문제 번호에 **O/X 마크**: 정답=파란 손그림 동그라미, 오답=빨간 ✕
- 문제 텍스트 뒤에 **`(YYYY-NN)` 배지** 표시 (`.q-exam-badge`, 채점 후에만 `display: inline`)
- 정답 선지: 원번호 검은 반전(정답 문제) / 빨간 반전(오답 문제)
- 오답 선택: 원번호 검은 반전 + `← 내 답` 라벨
- 선지 해설: `→ <span class="exp-text-inner">` 형식, 정답 해설은 노란 하이라이트(`#fff176`)
- `flex-basis: 100%`로 해설을 **다음 줄**에 표시
- **쪽집게 노트** 자동 펼침 (study_mode와 동일한 `_qNotes` + `q-note-section` 구조)

### 관련 CSS 클래스

- `.study-toggle` — 헤더 체크박스
- `.question-item.study-graded.is-correct|is-wrong` — 채점 상태
- `.choice-item.study-correct|study-picked|study-wrong` — 선지 상태
- `.choice-exp.correct-choice-exp` — 정답 선지 해설 하이라이트

## 모의고사·채점결과·오답노트 공통 UX

### qtext 필터 적용

`mock_exam_take.html`, `exam_result.html`, `wrong_answers.html` 모두 `{% load gisa_filters %}`로 `qtext` 필터 사용:
- `[box]...[/box]` → `<div class="q-box">` 테두리 박스
- `<u>` 밑줄, 위/아래첨자(`^{X}`, `_{X}`), 줄바꿈 변환
- **①~⑳ 으로 시작하는 줄은 매달린 들여쓰기 블록**으로 감싼다(inline style,
  `_HANG`). 줄이 넘어가면 번호 뒤 글자 자리에서 이어진다. 상자 첫/끝 줄도
  처리하며, 블록 앞뒤 `<br>` 을 하나씩 빼 빈 줄 수는 원문대로 남긴다.
  템플릿 쪽에서 같은 항목에 또 들여쓰기를 주면 두 번 밀리므로 주지 말 것

### 채점 결과·오답노트 하단 쪽집게 노트

- `_build_note_map()` + `_rank_notes()`로 문제별 관련 절(chapter/section) 매핑
- `q_notes_json`을 템플릿에 전달 → JS로 `.q-note-section`에 동적 렌더링
- **해설보기** 클릭 시 선지 해설 + 쪽집게 노트 동시 노출
- `q-note-section ul` 들여쓰기: `padding-left: 20px; margin-left: 20px` (문단보다 한 단계 들여쓰기)

## 기출검색 (certification_detail ?tab=study)

학습 탭 상단에 검색창 추가. 문제/보기 텍스트에서 키워드 매칭.

### API: `api_gisa_search_questions`

- 단어 분리(1글자 제외, 최대 10개) → OR 검색 + 매칭 수 정렬
- 최신기출 제외(`exclude(exam__exam_type="최신")`)
- 응답에 `explanation`, `choice_X_exp` 포함

### 검색 결과 UI

- 카드 형태 (`.sr-card`): 메타(년도/회차/과목) + 문제 + 4개 선지
- 선지 클릭 → 정답 표시(검은 반전) + 4개 선지별 해설 펼침
- 채점 없음(맞/틀 판정 X) — 정답과 해설만 제공
- `fmtQtext()` JS 함수로 `[box]`, `<u>`, 위/아래첨자 변환
- 접기/펼치기 버튼으로 선지 영역 토글

## 이미지 upload_to 경로 규칙

`GisaQuestion`의 이미지 필드는 `_gisa_question_img_path()` 함수로 동적 경로 생성:

```
gisa/questions/c{cert_id}/{year}-{round}/{filename}
예: gisa/questions/c5/2022-1/choice_1_image.png
```

**이전 방식** (파일명 충돌 위험):
```
gisa/questions/choice_1_image.png  # 모든 자격증 공유 → 식물보호기사 이미지가 조경기사 이미지를 덮어쓸 수 있음
```

조경기사 2022-1 #52, #57은 과거 충돌로 이미지가 덮어씌워졌던 사례 (c5 경로로 재업로드하여 복구).

## 문제/보기 이미지 표시 크기

PDF에서 3배 확대 추출한 이미지는 원본 폭이 660~780px이라 CSS 상한이 없으면 화면을 가득 채운다.

| 클래스 | 설정 | 비고 |
|--------|------|------|
| `.q-image` (지문 이미지) | `max-width: min(100%, 420px)` | 상한 없으면 원본 크기 그대로 표시됨 |
| `.choice-image` (보기 이미지) | `max-width: min(100%, 300px)` | |
| 모바일(768px 이하) | `max-width: 100%` | 기존 오버라이드 유지 |

**적용 위치 6곳**: `study_mode.html`, `exam_take.html`, `mock_exam_take.html`, `exam_result.html`, `wrong_answers.html`, `certification_detail.html`

> `mock_exam_take.html`만 CSS 클래스가 아니라 **인라인 `style` 속성**을 쓰므로 별도로 수정해야 한다.

## 채점 결과 모바일 헤더 (exam_result)

gisa/exam_result.html, exam/exam_result.html 모두 동일한 컴팩트 모바일 헤더 적용.

### 레이아웃

- 흰색 배경, 1행 flex 레이아웃 (`position: sticky; top: 0`)
- 좌측: 점수 (`1.5rem` 볼드) + "점" 단위 + 정답수/총문제수
- 우측: 액션 버튼 (pill 스타일, `border-radius: 14px`)

### 색상

- gisa: 남색 톤 (`#1a237e`) — 점수, 버튼 배경
- exam: 다크그린 톤 (`#1b4332`) — 점수, 버튼 배경
- 돌아가기 버튼: 회색 (`#eee` 배경, `#555` 텍스트)

### 돌아가기 링크 분기

모드에 따라 적절한 탭으로 복귀:
- 기출고사 → `?tab=solve` (gisa) / `?tab=study` (exam)
- 모의고사 → `?tab=mock`
- 오답 재풀이 → `?tab=wrong`

### HTML 구조

```html
<div class="mobile-header">
    <div class="mh-row">
        <div class="mh-score">...</div>
        <div class="mh-actions">
            <a class="mh-btn">...</a>
            <a class="mh-btn mh-btn-sub">돌아가기</a>
        </div>
    </div>
</div>
```

## 헤더 네비게이션 (base.html)

- "농학과 과목" 링크 → 마이페이지
- "식물보호(산업)기사" 링크 → `/gisa/`
- "나무의사" 링크 → `http://www.studynamu.com` (외부, `target="_blank"`)
- 스태프 전용 "관리" 링크
- 로그아웃 링크

## django.contrib.humanize

`INSTALLED_APPS`에 `django.contrib.humanize` 추가.

- `certification_list.html`, `certification_detail.html`에서 `{% load humanize %}` + `{{ count|intcomma }}`로 천자리 콤마 표시

## 쪽집게 노트 (방송대 기출 - exam 앱)

과목별 챕터 단위 학습 정리 노트. `subject_detail.html`의 "쪽집게 노트" 탭에서 아코디언 UI로 표시.

### StudyNote 모델 (exam/models.py)

| 필드 | 설명 |
|------|------|
| `subject` | FK → Subject |
| `title` | 장 제목 (예: "제1장. 세포의 구조와 기능") |
| `content` | 마크다운 내용 |
| `order` | 장 순서 (1~15) |
| `created_at` | 생성일 |
| `updated_at` | 수정일 |

- unique_together: `(subject, order)`
- 총 341개 노트 (30개 과목)

### 완성 현황 (30개 과목)

| 학년 | 과목 | 챕터수 |
|------|------|--------|
| 1학년 | 글쓰기(12), 농학원론(12), 생물과학(13), 생활과건강(10), 세계의역사(10), 숲과삶(12), 원예학(12), 재배학원론(11), 컴퓨터의이해(12) | 9과목 |
| 2학년 | 농업생물화학(12), 농업유전학(12), 동서양고전의이해(12), 재배식물생리학(13), 한국사의이해(9) | 5과목 |
| 3학년 | 글쓰기(8), 농축산환경학(8), 생물통계학(12), 생활원예(14), 식물의학(12), 식용작물학1(12), 원예작물학1(12), 자원식물학(12), 재배식물육종학(12), 토양학(11), 해충방제학(6), 환경친화형농업(12) | 12과목 |
| 4학년 | 생활과건강(12), 시설원예학(12), 식용작물학2(12), 원예작물학2(12) | 4과목 |

### 미완성 과목

| 학년 | 과목 |
|------|------|
| 1학년 | 심리학에게묻다, 인간과과학, 인간과교육, 축산학 |
| 2학년 | 생활속의경제, 세상읽기와논술, 철학의이해, 취미와예술 |
| 3학년 | 동물사료학, 세상읽기와논술, 인간과교육, 푸드마케팅 |
| 4학년 | 농업경영학, 농축산식품이용학, 식물분류학, 푸드마케팅 |

### 노트 생성 방식

1. DB에서 과목 문제를 JSON으로 추출 (`_PREFIX_questions.json`)
2. AI 에이전트로 챕터 분류 (`_PREFIX_chapters.json`)
3. 장별 병렬 에이전트로 노트 생성 (`_PREFIX_note_chN.md`)
4. DB에 `update_or_create`로 import

### 마크다운 형식

```markdown
## 제N장. {title}
### N.M 절제목
#### N.M.K 항제목
교재형 서술문...
**관련 문제**: (YYYY-N), (YYYY-N)
### 핵심 키워드 요약
| 키워드 | 핵심 포인트 |
```

- 교재형 서술문 스타일 (불렛은 열거 시에만 사용)
- 핵심 용어 `**볼드**` 처리
- 각 절 끝에 `**관련 문제**: (YYYY-N)` 형식 (연도-문항번호)
- 각 장 끝에 `### 핵심 키워드 요약` 테이블

### PREFIX_MAP (파일 prefix → 과목 매핑)

```python
PREFIX_MAP = {
    'abc': ('농업생물화학', 2), 'ag': ('농업유전학', 2), 'ai': ('농학원론', 1),
    'bs': ('생물과학', 1), 'cb': ('재배식물육종학', 3), 'cp': ('컴퓨터의이해', 1),
    'dg': ('동서양고전의이해', 2), 'ef': ('환경친화형농업', 3), 'fl': ('숲과삶', 1),
    'gw1': ('글쓰기', 1), 'gw3': ('글쓰기', 3), 'hc1': ('원예작물학1', 3),
    'hc2': ('원예작물학2', 4), 'ho': ('원예학', 1), 'hp': ('해충방제학', 3),
    'kh': ('한국사의이해', 2), 'nc': ('농축산환경학', 3), 'sc1': ('식용작물학1', 3),
    'sc2': ('식용작물학2', 4), 'sg1': ('생활과건강', 1), 'sg4': ('생활과건강', 4),
    'sw': ('시설원예학', 4), 'wh': ('세계의역사', 1),
}
```

### 잡초방제학(4학년, pk 51) — A+ 문제집 기반 재구축 (2026-09)

2013~2019 기출이 없는 과목이라 2023·2024년 기말 복원 문항과 인강 예제로 이뤄진
**A+ 문제집 PDF 4권**(교수 배포, 15강 구성·127문항·선지별 해설)을 Claude가 **직접 읽어**
(프로그램 파싱 금지 — 사용자 지시) 문항과 쪽집게 노트를 새로 썼다.

- 문항 원본: `_weed_questions_aplus.json`(127건, 손으로 옮김). 5~7지선다는 4지로 줄이고
  O/X·단답·서술형은 4지선다로 바꿨다. 연도 배정은 `load_weed_questions.py` 참조 —
  태그 23년→2023, 24년→2024(둘 다면 두 연도에 모두), 카페 응시기와 대조해 2025년
  출제가 확인된 22건→2025, 인강 예제 8건→2025에 `[인강]` 접두어. 합계 172건
  (2023: 73, 2024: 69, 2025: 30). 배정표 `_weed_qmap.json`. 이전 101건 스텁 백업
  `_weed_questions_backup_before_aplus.json`, 이전 8장 노트 백업 `_weed_knou_notes_backup.json`
- 노트: `_weed_notes_part1~3.md` → `load_weed_notes.py --apply`(15장, 64절, 172문항
  전부 참조). 참조 누락·없는 문항 참조를 스크립트가 검사한다
- **2020 이전 문항이 없는 과목은 기출학습·기출풀기·모의고사 탭이 전체 연도를 쓴다**
  (`subject_detail`, `mock_exam_take`). 그 밖의 과목은 종전대로 2020 미만만

### 잡초 동정 퀴즈 (방송대 subject_detail ?tab=weeds · 기사 필기 certification_detail)

**세 페이지가 같은 조각을 쓴다**(2026-09). 방송대 잡초방제학 과목 페이지와
**식물보호기사·식물보호산업기사 필기** 페이지(쪽집게 노트 바로 오른쪽 탭)에 같은
탭이 붙는다. 카드는 방송대 과목(pk 51)에 달려 있고 API 도 main 앱 것을 그대로 쓴다.

| 조각 | 넣는 자리 |
|------|-----------|
| `main/_weed_css.html` | 쓰는 쪽 `{% block extra_css %}` 의 `<style>` 안 |
| `main/_weed_tab.html` | 탭 내용 자리 (`{% if weed_count %}` 가 조각 안에 있다) |
| `main/_weed_js.html` | 쓰는 쪽 `{% block extra_js %}` 의 `<script>` 안 |

- 컨텍스트는 `main.views.weed_tab_context(request, subject, first_mode)` 하나가 만든다 —
  `weed_subject`·`weed_count`·`weed_stats`·`weed_modes`·`weed_first`. 조각의 URL 은
  `subject.pk` 가 아니라 **`weed_subject.pk`** 다(기사 페이지에는 subject 가 없다)
- **범위 버튼 차례를 서버가 정한다**(`weed_modes`). 기사 페이지는 그 자격증 필기가 맨 앞,
  '전체' 는 '오답만' 바로 왼쪽. 방송대 페이지는 종전대로 '전체' 가 맨 앞.
  탭에 들어올 때 자동으로 내는 첫 문제도 그 범위다(`_WD_FIRST`)
- **이름은 `wd-`·`wdn-` 으로 바꿔 두었다.** 기사 페이지에 이미 `.wq-`(오답 문항)와
  `.nq-`(노트 카드)가 있어 14개가 겹쳤다. 관련 문제 카드 렌더러도 `_wdnRender`·`wdnPick`
  으로 따로 둔다 — 기사 페이지의 `window.nqPick` 을 덮어쓰면 그쪽 노트 카드가 망가진다
- 잡초 카드가 없는 자격증(조경기사 등)에서는 조각을 include 하지 않는다 —
  `weed_subject` 가 없어 URL 역참조가 터진다
- **Django 의 `{# … #}` 은 한 줄짜리만 주석이다.** 여러 줄로 쓰면 그대로 출력돼 JS 가
  깨진다(실제로 한 번 당했다). 조각 머리말은 `{% comment %}` 를 쓴다


교수 배포 `02. 잡초방제학 카드(방송대).pdf`(250쪽, 잡초 122종 × 문제쪽·답쪽)를 Claude가
직접 읽어 만든 **사진 → 이름 4지선다**. 카드가 있는 과목(잡초방제학 pk 51)에만 탭이 보인다.

- 모델 `exam.WeedCard`(subject·card_no 고유; name·family·life_form·habitat·features·similar·
  control(직접 작성)·notes(슬라이드 글자 층의 교수 메모)·exam_count('N회 출제' 배지)·
  q_image(문제쪽 사진 부분)·a_image(답쪽 슬라이드 전체)·sketch_image(답쪽 손그림만)),
  `WeedQuizAttempt`(카드별 최신 기록이 틀리면 오답)
- API: `api_weed_quiz_next`(`?mode=all|freq|wrong&seen=`; 보기는 정답 + 같은 과 우선 3개,
  freq 는 exam_count 가중), `api_weed_quiz_answer`(POST card·selected → 정답·보충 정보),
  `api_weed_quiz_reset`
- 데이터: `_weed_cards.json` + `load_weed_cards.py --apply`. 이미지는 `media/weeds/s51/`
  (q###.jpg 244장, git 밖 — 서버에는 tar 로 올렸다). PDF 판독 규칙: 앞쪽 96쪽은 Q·A 가
  번갈아 오지만 97쪽부터 순서가 뒤집히고 보조 쪽(사진 출처·비교 격자)이 끼어 있어 쪽마다
  눈으로 분류했다. 출제 배지는 앞부분 48종에만 있다
- **문제 사진(q###.jpg) 자르기**: 슬라이드는 흰 여백 / 연녹색 판 / 사진 3층이다. 사진 행
  판정은 "판 색과 다른 화소가 많으면 사진"이 아니라 **"그 행이 판 색과 거의 같으면(95%↑)
  틈"** 이어야 한다 — 앞의 기준으로는 사진 사이 몇 픽셀짜리 틈을 놓쳐 두 장이 한 덩어리로
  잘리고 가운데에 연녹색 띠가 남는다(실제 31장이 그랬다). 쇠별꽃은 판 **바깥** 흰 여백에도
  사진이 하나 더 있어(PDF 이미지 객체로 확인) 따로 넣었다
- **손그림(세밀화)**: 답 슬라이드마다 교수가 손으로 그린 그림이 붙어 있다. 사진만으로는
  구별이 어려운 종이 많아, **답을 고른 뒤 문제 사진 오른쪽 아래에 겹쳐** 보여 준다
  (`.wq-sketch-ov`, 폭 34%·190px 상한, 모바일 38%·150px). 그림에 잡초 이름이 손글씨로
  적혀 있으므로 **문제를 낼 때는 감춘다**(`weedNext`·`weedGo` 에서 `hidden = true`).
  사진 모서리에 정확히 붙이려면 래퍼 `.wq-photo-in` 이 사진과 같은 크기여야 해서
  `inline-flex` 를 쓴다(`inline-block` 은 baseline 때문에 아래가 몇 px 뜬다).
  110종에 있고 12종(서양민들레·민들레·쑥·가시박·수강아지풀·개망초·마디꽃·고들빼기·
  털별꽃아재비·애기수영·괭이밥·고사리)은 슬라이드에 그림 자체가 없다
  - 추출 `cut_weed_sketches.py --write` → `media/weeds/s51/k###.jpg`. PDF 에 스케치가
    **별도 이미지 객체**로 들어 있어 좌표를 그대로 읽으면 된다(슬라이드 아래쪽 오른편;
    설명 텍스트 상자가 함께 잡히는 카드는 **더 아래에 있는 것**이 스케치다)
  - 여백 다듬기 `trim_weed_sketches.py --write`. 원본은 `k_src/` 에 남겨 두고 매번 거기서
    다시 만들므로 반복 실행해도 조금씩 깎이지 않는다. 연녹 판 제거 → 종이 영역 맞춤 →
    남은 판 줄 제거 3단계
  - DB 연결 `load_weed_sketches.py --apply`
- **교수 메모**(`.wq-notes-ov`): 답을 고르면 **문제 사진 왼쪽 아래에 흰 글씨**로 얹힌다
  (배경 상자 없음; 오른쪽 아래 손그림과 좌우로 나뉜다). 문제 사진은 위·아래 두 장이
  한 이미지라 아래쪽에 두면 두 번째 사진 위에 놓인다. 답 영역에는 두지 않는다 — 사진을
  보며 메모를 읽는 편이 자연스럽다. 83종에 있고 가장 긴 것이 9줄이다. 억새·개구리밥처럼
  **밝은 사진**이 있어 그림자만으로는 안 읽히므로, 글자에 **검은 테두리**를 두른다
  (`-webkit-text-stroke: 0.6px`, `paint-order: stroke fill` 로 테두리를 글자 뒤에 그린다).
  배경 음영을 깔면 사진이 가려져 쓰지 않는다. `::marker` 에는 text-stroke 가 먹지 않아
  불렛만 흐려지므로 `li::before` 로 직접 그린다. 긴 메모가 손그림을 침범하지 않도록
  폭은 58%, 손그림에 `z-index: 1`. **132종 전부 메모가 있다** — 교수 배포 카드에
    있던 88종 외에, 없던 44종은 식별 포인트를 읽고 사진으로 바로 확인되는 것만 골라
    손으로 썼다(`_weed_memo_new.json` + `load_weed_memo.py --apply`). 12자 안팎의
    구(句)여야 한다 — 문장을 넣으면 사진을 덮는다
- **답 슬라이드는 답 영역에 보여 주지 않는다**(2026-09). 필요한 것(손그림·메모)을 모두
  사진 위로 옮겨 중복이었다. `a_image` 필드와 파일은 원본 보관용으로 남아 있다
- **답안 수정**(스태프): 답 아래 "답안 수정" 버튼 → 식별 포인트·헷갈리는 종과 구별·
  방제·비고·교수 메모를 그 자리에서 고친다(`weedEdit`, `api_weed_card_update`).
  **Toast UI 는 마크다운 기반이라 글 색을 못 넣으므로 여기서는 쓰지 않는다** —
  `contenteditable` + `execCommand`(굵게·밑줄·기울임·글자색 6종·서식 지우기)면 충분하다.
  붙여넣기는 평문으로만 받는다(다른 곳에서 복사하면 글꼴·크기가 딸려 온다)
  - 서버가 `_clean_weed_html()` 로 **허용 태그만** 남긴다(b/strong·i/em·u·s·br·span·
    mark·ul/ol/li·div·p). `style` 은 `color`·`background-color` 의 `#hex`/`rgb()` 만
    통과시킨다 — 글꼴 크기까지 허용하면 카드마다 서식이 제각각이 된다. script·style·
    iframe 류는 **내용까지** 버리고, 그 밖의 태그는 벗기되 글은 남긴다
  - 화면은 `_wqBody()` 가 그린다. 태그가 있으면 그대로, **아직 서식을 넣지 않은 평문은
    이스케이프 후 줄바꿈만 살린다**(122종 대부분이 평문이다)
  - **저장 뒤 사진 주소는 경로끼리 견준다**(`_wqAfterEdit`). `img.src` 는 절대 주소이고
    응답의 `q_img` 는 `/media/…` 라 문자열로 견주면 글만 고쳐도 늘 '사진이 바뀐 것'이 되어
    낱장 좌표(`_wqParts`)를 잃고, 그 뒤로 사진을 눌러도 통째로만 확대됐다. 수정 응답에
    `parts` 를 늘 실어 그 자리에서 쓴다
  - **교수 메모는 서식을 받지 않는다** — 사진 위 흰 글씨라 색이 안 보인다. 줄 단위
    필드라 `_weed_notes_lines()` 가 HTML 을 줄바꿈으로 되돌리고, 편집기도 툴바 없이 보여 준다
  - Chrome 의 contenteditable 은 Enter 를 누르면 **첫 줄은 태그 없이 두고 둘째 줄부터**
    `<div>` 로 감싼다(`첫 줄<div>둘째 줄</div>`). 닫는 태그에서만 자르면 첫 줄과 둘째
    줄이 붙어 버리므로 **여는 태그에서도 잘라야 한다**. 편집기를 열 때도 `<br>` 이 아니라
    줄마다 `<div>` 로 넣는다 — `<br>` 로 넣으면 Chrome 이 편집 중 `<div>` 로 바꿔 놓아
    첫 줄만 태그가 없는 어정쩡한 상태가 된다
- **기출 배지**(`_weed_exam_refs`, `.wq-meta .wq-refs`): 답 화면의 과·생활형·발생지 배지 줄
  **오른쪽**에, 그 종명이 **문제 본문이나 선지 ①~④ 어디든** 나오는 문항을 `연도-번호` 로 붙인다.
  누르면 그 문항이 아래에 펼쳐진다(쪽집게 노트 관련 문제와 같은 `_nqRender` 카드,
  `api_note_questions?ref=YYYY-N` 재사용). 로컬 기준 123종 중 13종에 배지가 붙는다
  (올방개 4건이 최다).
  - **이름은 '정확히 그 이름' 일 때만 센다**(`_weed_name_re`, 2026-09). 앞이 한글이면
    다른 종이다 — 네가래·생이가래·가는가래는 **가래가 아니고**, 알방동사니·너도방동사니는
    방동사니가 아니다. 뒤가 한글이면 **조사·분류 접미일 때만** 인정한다(`_WEED_JOSA` =
    은는이가을를와과의에도로만며고나등류). 기사 문항 6,800건에서 종명 뒤 한 글자를 세어
    추린 목록이다: 과 47 · 의 23 · 에 12 · 와 11 · 는 10 · 를 8 · 류 7 …
    여기 없는 글자는 합성 종명이다 — 여뀌**바**늘, 별꽃**아**재비, 쑥**부**쟁이, 쑥**갓**
  - 한 글자 이름('피'·'띠')과 `_WEED_ALIAS_EXACT`('새삼'·'논피')는 **뒤 한글도 막는다** —
    '피해'·'피복'·'띠며'(동사 띠다)·'실새삼'·'나도논피'가 걸리면 안 된다
  - 이 규칙으로 건수가 줄었다: 방동사니 181 → 40, 바랭이 148 → 138, 가래 93 → 78.
    **화면 형광펜도 같은 판정을 쓴다**(payload 의 `josa`) — 세는 것과 칠하는 것이 어긋나면
    "왜 이 문항이 여기 있지" 가 된다
  **목록의 '출제' 칸에도** 횟수 뒤에 같은 배지를 붙인다(`.wq-t-refs`, 눌리지 않는다 —
  줄 클릭이 그 카드로 간다). 목록은 카드 136장을 한꺼번에 그리므로
  `_weed_exam_matcher(subject)` 가 문항을 **한 번만 읽어** 종마다 파이썬에서 대조한다
- **식물보호기사 필기 배지**(`_weed_gisa_counts`, `.ref.g` 보라색): 같은 자리에 붙되
  **낱개가 아니라 자격증별 건수**("기사 96 · 산업기사 85")다 — 방동사니 181건·바랭이
  148건처럼 수십~수백 건이 걸려 낱개 배지는 불가능하다. 누르면
  `api_weed_gisa_questions?name=&cert=&page=` 로 **10건씩** 펼치고 '더 보기'로 잇는다
  (`_nqRender` 에 `q.label` 을 두어 "기사 2024-3회 81번" 꼴 배지를 단다). 문항 6,800건의
  본문+선지는 `_weed_gisa_rows()` 가 **10분 캐시**로 들고 있다 — 요청마다 읽으면 목록이
  느리다. `[box]`·`<u>` 표식은 `_weed_gisa_plain` 으로 벗긴다(이 화면에는 qtext 필터가 없다).
  목록에도 같은 건수 배지가 붙는다.
  펼친 문항의 문제·선지에서는 **종명을 형광펜(`mark.wq-hl`)으로 칠한다**(`_wqHighlight`) —
  글자 노드만 바꿔 원번호·배지·해설 마크업은 건드리지 않고, **서버(`_weed_name_re`)와
  같은 앞뒤 규칙**을 쓴다(payload 의 `names`·`names_strict`·`josa`). 이미 칠한 곳은
  건너뛰므로 '더 보기'로 이어 붙여도 겹치지 않는다
- **이름 표기 차이는 별칭표로 잇는다**(`_WEED_ALIASES`). 문항이 카드와 다른 표기를 쓰면
  부분 문자열 대조에 안 걸린다 — '둑새풀'(뚝새풀의 이명)만으로 기사·산기 **19문항**이,
  '새삼'(카드 이름은 새삼덩굴)으로 10문항이 통째로 빠져 있었다. 이명과 원문 오기
  8종(둑새풀·독새풀·새삼·깻풀·논둑외풀·환상덩굴·너동방동사니·매꽃·불달개비)을 표에 두고
  `_weed_name_hit` 하나로 배지·건수·출제 범위(`_weed_source_weights`)·방송대 참조
  (`_weed_exam_matcher`)·형광펜(카드 payload 의 `names`)이 모두 같은 표를 쓴다
  - **근연종은 넣지 말 것.** 별꽃아재비·진득찰·참새피는 카드(털별꽃아재비·털진득찰·
    털물참새피)와 **다른 종**이라 같은 것으로 세면 안 된다
  - '새삼'처럼 짧은 별칭은 앞뒤가 한글 음절이 아닐 때만 인정한다(`_WEED_ALIAS_EXACT`) —
    그러지 않으면 실새삼·갯실새삼에 걸린다. 화면도 `names_strict` 로 같은 규칙을 쓴다
- **기사 필기에 나오는데 카드가 없는 종이 35종 있다**(2026-09 조사, 잡초방제학 문항 기준).
  메귀리 23건 · 토끼풀 10건 · 참방동사니 16건 · 까마중 · 물고랭이 · 드렁새 · 벼룩이자리 ·
  달맞이꽃 · 보풀 · 큰고추풀 · 등에풀 · 검정말 · 조뱅이 · 파대가리 … 카드를 늘릴 때 여기부터
- **출제 빈도 별**(`_wqStars`, `.wq-stars` 노란색): **필기(식보+산기) 문항 수**로 매긴다 —
  50건↑ ★★★ / 20~49 ★★ / 5~19 ★ / 1~4 ☆, 0건은 없음. 답 화면 이름 옆과 목록 표 종명
  옆에 붙고, 목록의 '출제' 칸 정렬도 이 합계(`gisa_total`)를 쓴다. 카드 123장 기준
  ★★★ 16 · ★★ 21 · ★ 37 · ☆ 21 · 없음 28로 갈린다
  - 2026-09 이전에는 `exam_count`(식물보호기사 **실기** 출제 횟수)가 기준이었다. 실기는
    이 화면에서 걷어냈다(사용자 요청) — 필드와 수정 창 입력은 남아 있지만 퀴즈 화면에
    값을 보이지 않는다
- **출제 범위 버튼**(`.wq-modes`, `api_weed_quiz_next?mode=`): 전체 / **방송대** /
  **식보-필기** / **산기-필기** / 오답만. 앞 셋은 그 출처의 문제·선지에 종명이 나온 카드만 내고
  문항 수로 가중한다(`_weed_source_weights`, 과목별 10분 캐시 — 카드 136장 × 기사 문항
  6,800건 대조). 방송대 58 · 식보 91 · 산기 84종
  - **방송대만 쪽집게 노트도 본다**(`_weed_note_chapters`·`_weed_note_hits`). 이 과목은
    2013~2019 기출이 없어 문항이 172건뿐이라 기출만 보면 13종밖에 안 남는다. 노트에서
    다루는 종이 곧 시험에 나올 종이므로 노트에 나오면 범위에 넣는다(13 → 58종).
    가중치는 기출 문항 수 + 그 종을 다룬 노트 장 수
- 화면: **탭에 들어오면 바로 '전체' 범위로 첫 문제가 나온다**(`weedAutoStart` — 진입 시와
  탭 전환 시 모두. 풀던 중이거나 목록을 보는 중이면 건드리지 않는다). 지금 범위의 버튼만
  진하고 나머지는 옅다(`.wq-modes:has(.on)`). 사진 + 보기 4개 → 고르면 **사진 위에
  교수 메모(왼쪽 아래 흰 글씨)와 손그림(오른쪽 아래)**이 뜨고, 아래에 이름(+별)·과·
  생활형·발생지·출제횟수·식별 포인트·유사종 구별·방제
  - **`display: flex`(grid·inline-flex 도) 는 `[hidden]` 을 이긴다.** `hidden` 으로
    여닫을 요소에는 `.클래스[hidden] { display: none }` 을 반드시 함께 둔다. 세 번
    걸렸다 — `.wq-actions`(답 고르기 전부터 '다음 문제'가 보임), `.wq-save`(잡초 탭에
    들어오자마자 빈 저장 창이 뜸), `.sec-qna-ask`(접혀 있어야 할 질문 입력칸이 늘 펼쳐짐).
    새 요소를 만들 때 이 조합인지 먼저 보라
- **관리자 사진 저장**: 목록 줄마다 '저장'(스태프만) → 그 카드의 사진을 늘어놓고 하나를
  골라 내려받는다(`api_weed_card_photos`). 파일 이름은 종명이다
  - 문제 사진은 여러 장이 붙은 한 장이라 서버가 **낱장 사각 좌표만** 주고 브라우저가
    canvas 로 자른다 — 서버에 파일을 새로 만들지 않는다. **세로뿐 아니라 가로로도 붙어
    있다**(강피·꽃다지는 좌우 두 장). 가로로 켜를 나눈 뒤 켜마다 세로로 다시 나눈다
  - **틈이 한 가지 색이 아니다.** 바깥 여백은 흰색인데 사진 사이는 원본 슬라이드의
    연녹색 판이 남아 있다(강피는 틈이 (225,234,207), 바깥은 (255,255,255)). '희다'로도
    '모서리 바탕색과 같다'로도 못 잡아, **밝고(min>180) 색이 옅은(max-min<45)** 화소를
    틈으로 본다 — 사진은 초록이 짙어 채도가 높다. 줄 전체의 92%가 틈이어야 자른다
    (사진 속 밝은 하늘을 틈으로 잘못 잡지 않도록). 123장 중 117장이 2장, 미국외풀 6장,
    강피·쇠별꽃·개망초·꽃다지 3장, 털진득찰만 한 덩어리로 남는다
  - **저장 위치는 브라우저만 정할 수 있고, 길이 둘이다. 섞어 말하면 오해가 난다.**
    ① 그냥 저장(`<a download>`)은 **다운로드 폴더에 아무 제약 없이** 받아진다.
    ② 폴더 지정(`showDirectoryPicker`)은 웹페이지가 폴더를 직접 열어 쓰는 것이라 권한이
    달라, Chrome 이 **다운로드·바탕화면·사진 폴더 *자체* 는 거부한다**("이 폴더를 열 수
    없음") — 그 안의 하위 폴더는 된다. 즉 "다운로드 폴더에 저장이 안 된다"가 아니라
    "다운로드 폴더를 *지정* 할 수 없다"이다. 거부(AbortError 가 아닌 오류)면 ① 로
    돌아간다. 고른 폴더 손잡이는 IndexedDB 에 담아 다음에도 쓰고(문자열이 아니라
    localStorage 에는 못 넣는다), 되살린 폴더는 권한이 사라졌을 수 있어 쓰기 직전에
    `requestPermission` 으로 다시 확인한다
- **새 카드 등록**(스태프): 목록 머리글의 "+ 등록" → 종명을 넣고 **확인·조회**를 누르면
  ① 같은 과목에 이미 있는 종인지 막고(`name__iexact`) ② 없으면 **Gemini 가 과명·생활형·
  발생지·식별 포인트·유사종·방제를 채운다**(`api_weed_name_check`). 관리자가 고친 뒤 등록
  - **교수 메모 칸은 줄마다 글머리표('· ')를 달아 보여 준다**(`_wqMemoInit`). 사진 위에서
    불릿으로 그려지는 항목이라 적을 때도 같은 모양이어야 몇 줄인지 눈에 들어온다. 칸에
    들어가면 첫 글머리표가 생기고 Enter 로 줄을 바꾸면 새 줄에도 붙는다(한글 조합 중인
    Enter 는 건드리지 않는다). 붙여넣기·포커스 아웃 때 '-'·'•' 도 '· ' 로 고른다.
    **저장할 때는 뗀다**(`_wqMemoStrip` + 서버 `_weed_memo_plain`) — 붙은 채 저장되면
    화면에서 불릿이 두 겹이 된다
  - **교수 메모는 AI 가 짧게 채운다**(`memo`). 새로 등록하는 종에는 교수 메모가
    없는데, 이 필드는 사진 위에 흰 글씨로 겹쳐 보이므로 식별 포인트를 그대로
    넣으면 사진을 다 덮는다. 프롬프트에 "사진 위에 겹쳐 놓을 쪽지, 12자 안팎의
    구(句)"라고 못 박아 "엽설 가장자리 털", "줄기에 깊은 골" 처럼 받는다
  - 여러 줄짜리 항목은 **스키마를 `list[str]` 로 받는다**. 한 문자열로 받으면 "줄바꿈으로
    나눠라"고 해도 "…보인다.잎은…" 처럼 붙여 놓는다. 받아서 `
` 으로 이어 붙인다
  - 사진은 **배열을 고르고 끌어다 놓는다**. 6가지(전체1 / 상1하1 / 상1하2 / 상2하2 /
    좌1우2 / 좌2우2)이고 `_WEED_LAYOUTS`(서버)와 `_WQ_LAYOUTS`(화면)의 칸 수·차례가
    **짝이 맞아야 한다**. 서버가 한 장으로 합성하되(`_weed_compose`) **칸 사이를 흰
    여백으로 띄운다** — 그래야 나중에 `_weed_photo_boxes` 가 다시 낱장으로 가른다
    (6가지 배열 모두 넣은 장수만큼 되갈리는 것을 확인했다)
  - `_weed_photo_boxes` 는 가로 먼저·세로 먼저 **두 순서를 다 해 보고 더 잘게 갈리는
    쪽을 쓴다**. 좌1우2 는 세로로 먼저 갈라야 3장이 나온다
  - **사진 후보를 인터넷에서 가져온다.** 종명을 확인하면 위키미디어 공용에서 찾아
    사진 목록에 자동으로 담긴다(`api_weed_web_photos`). **학명으로 찾아야 한다** —
    한국어 이름으로는 거의 안 나오고(흰명아주·올방개 0장) 학명을 주면 잘 나온다.
    그래서 AI 조회 스키마에 `sci_name` 을 넣어 두 일을 한 번에 한다
    - 실제 파일은 **칸에 놓을 때** 받는다(12장을 미리 다 받으면 느리다). 다른
      도메인이라 브라우저가 직접 못 읽어 서버가 받아 넘긴다(`api_weed_fetch_photo`).
      **아무 주소나 받으면 SSRF 통로가 되므로** 위키미디어·국립수목원 도메인만 통과시킨다
    - CC 라이선스라 **출처를 밝혀야 한다**. 따로 필드를 만들지 않고 이미 화면에 보이는
      '방제·비고' 끝에 "사진: 제목 / 저작자 / 라이선스 (위키미디어 공용)" 로 적는다
    - 썸네일도 **서버를 거쳐** 보여 준다. 위키미디어가 핫링크를 막아 브라우저에서
      바로 불러오면 일부가 안 뜬다(12장 중 3장). 서버 요청에 Referer 를 붙인다
    - **학명을 찾았으면 한국어 이름으로는 찾지 않는다.** 한국어는 딴 뜻으로 걸리는
      일이 잦다 — '가래'는 영어로 sputum(객담)이라 객담 현미경 사진이 쏟아졌다.
      학명을 끝내 못 찾은 때만 이름으로 찾고, 화면에 그 사실을 알린다
    - **그 종 사진이 없으면 옛 식물학 책 스캔이 잔뜩 걸린다**(선피막이는 12장이 모두
      표지·본문 PDF 였다). 검색어에 `filetype:bitmap` 을 붙여 PDF·DjVu 를 빼고,
      제목에 학명이 없는 것도 버린다. 그러고도 0장이면 "쓸 만한 사진이 없습니다"라고
      알린다 — 엉뚱한 사진을 채워 주는 것보다 낫다
    - 썸네일이 84px 이라 무슨 사진인지 안 보인다. **사진을 누르면 크게 본다**
      (`weedZoom`·`weedEditZoom`, 등록 창·수정 창 모두 같다). 모서리에 돋보기(⊕) 단추를
      두었다가 겨냥하기 번거로워 걷어냈다 — **클릭과 드래그는 다른 사건이라** 사진 전체에
      click 을 걸어도 끌어다 놓기는 그대로 된다
  - 등록 창은 **열자마자 배열·사진·상세를 모두 보여 준다**. 조회가 끝나야 보이게
    했더니 빈 화면을 한참 보게 됐다. 상세는 접힌 채로 두었다가 **조회하면 펼친다**
  - 사진은 단추·**끌어다 놓기**·**붙여넣기(Ctrl+V)** 셋 다 받는다. 목록 안에서 칸으로
    옮기는 드래그와 섞이지 않도록 **바깥에서 온 파일(`dataTransfer.files`)이 있을 때만**
    받는다. 붙여넣기는 등록 창이 떠 있을 때만 듣는다
  - **목록의 사진을 목록에 도로 놓으면 같은 사진이 하나 더 늘어난다** — 브라우저가
    끌려 온 `<img>` 를 파일처럼 넘기기 때문이다. `dragstart` 에서 `application/x-wq-pool`
    표식을 싣고 `_wqAdd.dragging` 을 세워, 목록 드롭에서 그 둘 중 하나라도 있으면
    받지 않는다. 이미지 자체가 끌리지 않도록 `-webkit-user-drag: none` 도 건다
  - **국립수목원 식물자원 API**(`NATURE_API_KEY`, 공공데이터포털)로 **학명·과명을
    확정한다**. `apis.data.go.kr/1400119/PlantResource`
    - **사진은 없다.** 도감 텍스트(학명·과명·형태·분포·유사식물·비고)뿐이라 사진은
      위키미디어가 맡는다. 대신 이 값이 AI 추정보다 정확하다 — AI 는 흰명아주 과명을
      호출마다 '명아주과'↔'비름과'로 달리 답했다(전통 분류 명아주과 = APG 비름과)
    - **키는 이미 URL 인코딩된 채로 발급된다. 다시 인코딩하면 403** 이라
      `urlencode` 를 쓰지 말고 그대로 붙인다
    - 검색어 파라미터는 `reqSearchWrd`, 상세는 `reqPlantPilbkNo` 다(둘 다 문서의
      "미리보기"에서만 확인된다 — 이름을 추측으로는 못 맞힌다)
    - 이름이 들어간 종이 여럿 걸리므로("바랭이" → 갯바랭이·왕바랭이…) **국명이 정확히
      같은 것**을 고르고 없으면 이명(`notRcmmGnrlNm`)까지 본다. '강피'처럼 표준 국명이
      아니면 안 걸리고, 그때는 AI 만으로 채운다(10종 중 8종 적중)
    - 도감 글은 AI 프롬프트의 바탕으로 넣되 **그대로 옮기지 말고 밭·논에서 눈으로
      구별하는 요령으로 고쳐 쓰게** 한다 — 카드는 사진 보고 이름 맞히는 데 쓴다
  - 등록 화면은 평문 textarea 라 `_clean_weed_html` 이 아니라 `_weed_plain` 을 쓴다 —
    textarea 가 보내는 `

` 을 그대로 두면 화면에 빈 줄이 생긴다
  - 낱장 미리보기는 **원본 픽셀 좌표를 쓰면 안 된다** — 화면에서 150px 로 줄어들어
    어긋난다. 상자에 `aspect-ratio: 원본폭/낱장높이`, 이미지에 `height: 원본높이÷낱장높이`
    와 `top: -윗좌표÷낱장높이` 로 **모두 낱장 높이 기준의 비율**로 센다(`%` 는 속성마다
    폭이냐 높이냐로 기준이 갈려 두 번 어긋났다)

### 쪽집게 노트 관리자 편집 (방송대 subject_detail)

스태프는 쪽집게 노트 탭에서 장(StudyNote 레코드)마다 **수정**·**이 장 삭제**·**새 장 추가**를
할 수 있다. 편집기는 **Toast UI Editor 3.2.2**(jsdelivr, 스태프에게만 로드) — WYSIWYG 로
고치고 하단 Markdown 탭으로 원문도 볼 수 있으며, 저장은 `getMarkdown()` 결과를
`note_update` 로 보낸다(제목의 "제N장"으로 `order` 갱신, 번호 충돌 시 400).
`## ` 제목 줄이 없으면 서버가 앞에 붙인다.

- 이미지: 툴바·붙여넣기·드래그 → `note_image_upload` → `media/notes/s<subject_pk>/` 저장,
  마크다운에 `![alt](url)` 로 들어간다. `parse_note_chapters` 가 이를 `<img class="note-img">` 로
  바꾼다(폭 520px 상한). **그림을 누르면 원본 크기로 크게 본다**(`noteZoom`) — 모서리에 ＋ 단추를 두었다가 겨냥하기 번거롭다는 지적에 걷어내고 그림 전체에 걸었다
- 파서가 WYSIWYG 출력을 받아들이도록 `* ` 불렛, 2~4칸 들여쓴 하위 불렛, `\~ \_ \*` 같은
  마크다운 이스케이프 제거(`\|` 는 `&#124;`)를 추가했다. 직접 쓴 마크다운 규칙은 그대로다
- 파싱 결과 캐시는 `updated_at` 최대값이 버전이라 저장하면 곧바로 새로 파싱된다
- **밑줄**: 마크다운에 문법이 없어 `<u>` 태그를 쓴다. 툴바의 U 버튼이 넣는다 — Toast UI 기본
  새니타이저가 `<u>` 를 지우므로 `customHTMLRenderer.htmlInline.u` 로 살려 두고, WYSIWYG 에서는
  `replaceSelection` 이 태그를 글자로 이스케이프하므로 표식(`⁣UOPEN⁣`)으로 감싼 뒤
  `getMarkdown()` 에서 `<u>` 로 바꿔 `setMarkdown()` 한다(선택 안의 볼드는 풀린다). 파서는 인라인
  HTML 을 그대로 통과시켜 `<u>` 가 렌더된다

## 채점 결과 보기 flex 레이아웃 (exam_result)

`exam/exam_result.html`의 보기(choice-item)가 줄바꿈 시 텍스트 시작 위치가 정렬되도록 flex 레이아웃 적용.

- `.choice-item { display: flex; align-items: flex-start; }`
- `.choice-text-wrap { flex: 1; }` — 보기 텍스트 + 해설을 감싸는 래퍼
- `.q-mark { flex-shrink: 0; margin-top: 2px; }` — 원번호 고정 너비
- `.choice-exp { margin-left: 0; }` — 해설 왼쪽 여백 제거 (flex 내부이므로)
- HTML: `<div class="choice-text-wrap">{{ c.text }}{% if c.exp %}...{% endif %}</div>`

## 오답노트 빨간 동그라미 제거 (wrong_answers)

`exam/wrong_answers.html`에서 정답 선지의 빨간 동그라미(`.q-mark.correct-mark::before`) CSS 규칙 제거.
- 정답 표시는 원번호 반전(`.correct-mark`)만으로 충분하므로 중복 표시 제거

## 학습모드 "노트 X" 버튼 (study_mode)

오답 재풀이(`is_wrong_retry`) 시 표시되는 "노트 X" 제외 버튼 관련.

- 위치: `.q-choices` 내부, 4번째 보기 다음 (선지 해설 마지막)
- CSS: `.dismiss-line { display: none; text-align: right; margin-top: 2px; }` (JS로 표시 제어)
- JS: 채점 후 `card.querySelector('.dismiss-line').style.display = 'block'`으로 표시
- HTML: `{% if is_wrong_retry %}<div class="dismiss-line"><button class="dismiss-btn">노트 <svg>X</svg></button></div>{% endif %}`

## 쪽집게 노트 아코디언 기본 동작

방송대(subject_detail.html)와 기사시험(certification_detail.html) 모두 동일한 2단계 아코디언 동작.

### 기본 상태

- 장(chapter): 기본 열림 (`open` 클래스 적용)
- 절(section): 제목만 표시 (내용은 접힘)
- subject_detail: 서버 렌더링이므로 HTML에 `open` 클래스 직접 적용
- certification_detail: AJAX 로드 방식이므로 페이지 로드 시 `autoLoadAllChapters()`로 모든 장 콘텐츠 자동 로드

### "전체 펼치기" 버튼

- 위치: 아코디언 목록 하단 (`text-align: right`)
- 동작: `.section-item`의 `open` 클래스를 토글 (장은 항상 열린 상태 유지)
- 버튼 텍스트: "전체 펼치기" ↔ "전체 접기" 토글
- subject_detail: `toggleAllNotes()` 함수, `_notesExpanded` 상태 변수
- certification_detail: `toggleAllTextbook()` 함수, `_textbookExpanded` 상태 변수

### AJAX 중복 로드 방지 (certification_detail)

- `body.dataset.loading` 가드: AJAX 요청 시작 시 `loading='1'` 설정
- `body.dataset.loaded` 체크: 로드 완료 후 `loaded='1'` 설정
- `toggleChapter()`, `autoLoadAllChapters()`, `open_ch` IIFE 모두 `loaded || loading` 체크

### 쪽집게 노트 관련 문제 — 탭 안에서 펼침 (subject_detail)

절의 "관련 문제 학습 (N)" 버튼은 페이지를 옮기지 않는다. `api_note_questions`
(`/subjects/<pk>/api/note-questions/?ref=YYYY-N&…`)로 문항을 받아 버튼 아래 `.nq-list`
에 카드로 펼친다(`toggleNoteQuestions`, 한 번 받으면 접기/펼치기만). 선지를 누르면
채점 없이 정답·해설을 보인다 — 내 선택은 검은 반전, 틀렸으면 정답을 빨간 반전, 정답
선지 해설은 노란 하이라이트(`nqPick`). 해설 문자열은 data 속성이 아니라 카드 DOM 의
`_q` 프로퍼티에 둔다(따옴표 이스케이프 회피). `notes_study` 뷰(학습모드 전체 화면)는
남아 있지만 이 탭에서는 더 쓰지 않는다.

**학명은 이탤릭으로 자동 변환한다**(`_nqSci`, 2026-09). 해설·문제·보기의 `속명 + 종소명` 을
`<i>` 로 감싼다 — `Trifolium repens L.` → *Trifolium repens* L. **명명자(L. · P. BEAUV. · Ohwi)와
계급 표기(var. · subsp. · f.)는 정자**이고, `var.` 뒤의 소명은 다시 이탤릭이다. 속명은 '대문자 +
소문자 둘 이상'이라 IUCN·LAI 같은 약어는 안 걸리지만, `Bordeaux mixture` 처럼 영어 두 낱말이
걸릴 수 있어 뒷말이 흔한 영어 명사면 건너뛴다(`_NQ_NOTSP`). **이스케이프 뒤에** 부르므로
`<i>` 를 넣어도 안전하다. 서버가 렌더하는 화면(학습모드·오답노트·채점결과)에는 아직 없다.

기사시험 필기 상세(`certification_detail ?tab=textbook`)도 같다. `_chapter_body.html` 의
"이 절의 문제 학습하기" 버튼이 `api_textbook_questions`(`/gisa/<id>/textbook/questions/?ref=YYYY-R-N&…`)
로 `_note_questions.html` 카드 HTML(qtext·이미지·vurl 적용, 최신기출 제외)을 받아 `.nq-list` 에
넣는다. 원번호를 눌러 고르며(gisa study_mode 규칙), 처음 고를 때 `study_log` 로 진도율 기록을 남긴다.
`textbook_study` 전체 화면 뷰는 남아 있다.

### 질의응답 ↔ 쪽집게 노트 절 연결 (방송대 subject_detail)

`QnaQuestion.note_sec`("7.5")·`note_sec_title` 이 대표 절이다. 절에서 바로 물으면(노트 탭
각 절 아래 **이 절에 질문**) 그 절이 들어가고 `find_note(force_sec=)` 가 그 절을 첫째 근거로
고정한다(프롬프트에 "질문자는 N.M 절을 읽다가 물었다" 명시). 질의응답 탭에서 물으면
답할 때 근거로 고른 첫 절이 자동으로 들어간다(항 7.5.1 이 잡혀도 절 7.5 로). 노트를
고쳐 번호가 밀리면 제목이 2차 키다.

- 노트 탭: 서버가 절 번호별 질문 JSON(`qna_by_sec_json`, tab=notes 일 때만)을 내려주고
  `initSecQna()` 가 각 절 아래에 상자를 끼워 넣는다 — 연결된 질문의 **제목 목록이 바로
  보이고 제목을 누르면 답이 펼쳐진다**. 제목 옆에 "질문 N" 배지. 절 번호는 절 제목의 `N.M`
- **"이 절에 질문"은 관리자만** 쓴다(노트를 보완하는 용도; 버튼도 관리자에게만, 서버도
  `is_staff` 아니면 거부). 회원은 질의응답 탭에서 묻고, 그 답이 자동 연결된 절 아래에
  나타난다. 질문도 없고 관리자도 아니면 상자 자체를 두지 않는다
- 질의응답 탭: 답 위의 📖 줄이 연결 절이 있으면 `?tab=notes&sec=N.M` 링크(그 절이 펼쳐진다)
- **답 렌더러 `qnaRender`**: AI 답이 "1. 소제목" 아래 "- 항목"이 딸리는 형태로 오는데,
  번호줄까지 불렛으로 만들면 소제목과 항목이 한 층이 되어 구조가 안 보인다.
  - 번호줄은 `<h4>` 소제목(왼쪽 초록 띠). **단 바로 뒤에 불렛이 딸려 있을 때만** —
    "1. 첫째 / 2. 둘째"처럼 번호만 나열한 것까지 소제목이 되면 어수선하다
  - `line.trim()` 으로 앞 공백을 버리면 중첩 불렛이 다 같은 층이 된다. 들여쓰기 2칸
    이상이면 한 단계 안으로 넣는다
  - 번호 목록은 `<ol>`, 불렛은 `<ul>` 로 나눠 열고, 섞여 나오면 태그를 바꿔 다시 연다
  - `*학명*` 이탤릭 처리(볼드 `**`와 겹치지 않게 앞뒤를 본다). "분류: …" 처럼 콜론 앞이
    2~24자면 라벨로 보아 굵게 — 문장 한복판의 콜론은 집지 않는다
- 기사시험 노트(GisaTextbook)에는 아직 없다

### 답 렌더러는 조각 하나다 — `main/_qna_render_{css,js}.html` (2026-09)

같은 렌더러가 다섯 벌로 복사돼 있었고, 그사이 **방송대 것만 좋아지고 실기 것은 옛날
그대로** 남아 있었다. 실기 답은 `① 소제목: 본문` 꼴로 오는데 옛 렌더러는 ①②③ 를 아예
몰라 전부 `<p>` 로 떨어뜨렸다 — 번호가 글 속에 묻혀 어디까지가 한 항목인지 안 보였다.

지금은 조각 하나를 셋이 함께 쓴다: **실기 탭**(`gisa/essay_list.html`) · **따로 보기**
(`main/qna_detail.html`) · **모두 보기**(`main/qna_list.html`). 실기 탭에서 두 화면으로
이어지므로 한쪽만 고치면 눌러 들어갔을 때 글이 도로 덩어리가 된다.

- `qnaRender(raw)` 가 ①~⑳ 로 시작하는 줄마다 `.qa-step` 을 만들고 **번호를 배지로 왼쪽에
  빼고 소제목을 세운다**. 소제목은 세 꼴을 받는다 — `① [소제목]` · `① 소제목: 본문` ·
  `① 소제목`(그 줄에 본문 없음). 문장으로 시작하면 소제목 없이 본문만 둔다
- **마지막 항목 뒤 빈 줄 다음에 오는 글은 `.qa-outro` 로 뺀다** — "본 내용은 일반
  이론에 근거한 것으로…" 같은 단서가 ⑤ 안에 들어가면 ⑤ 의 내용처럼 읽힌다
- 학명(`Rhododendron indicum`)은 이탤릭(`qnaSci`), 불렛 앞머리 라벨은 굵게(`qnaLabel`)
- 색은 `--qa-accent` 로 바꾼다(실기 초록). **필기(`certification_detail`)와 방송대
  (`subject_detail`)는 아직 제 복사본을 쓴다** — 옮길 때 이 변수만 남색으로 주면 된다
- 쓰는 쪽 `<style>`·`<script>` **안에** include 한다(`_essay_pen_*.html` 과 같은 방식)
- 화면은 로그인이 필요해 눈으로 못 본다. `_jscheck.py` 로 JS 를 파싱하고, 서버에서 뽑은
  실제 답을 로컬 DB 에 잠깐 넣어 렌더·촬영한 뒤 지우는 식으로 확인했다

### 쪽집게 노트 "내용으로" 스크롤 (subject_detail)

노트 학습 모드에서 "내용으로" 버튼 클릭 시 쪽집게 노트 탭의 해당 절로 스크롤.
- 절 탐색: DOM 요소의 텍스트 내용으로 매칭 (ID 기반이 아닌 title text 기반)
- `section-item` 순회하며 `section-header span` 텍스트가 장 제목에 포함되는지 검사
- 매칭된 절의 부모 `chapter-item`을 열고 해당 `section-item`으로 스크롤

## 최신기출 중복 방지 (gisa)

`gisa_latest_create`와 `gisa_latest_clone` 뷰에서 동일 문제 중복 등록을 차단한다.

- 중복 판정: `GisaQuestion.objects.filter(exam=exam, text=text).exists()` (문제 텍스트 기반)
- 중복 시 `django.contrib.messages.warning()`으로 경고 메시지 표시 후 리다이렉트
- `certification_detail.html`의 최신기출 탭 상단에 메시지 표시 영역 추가

## 학습모드 관리자 인라인 편집 (gisa/study_mode.html)

staff 사용자가 학습모드에서 문제/보기/정답/해설을 인라인으로 수정할 수 있다.

### 편집 기능 (기존)

- `{% if request.user.is_staff %}` 조건으로 연필 아이콘 편집 버튼 표시
- 클릭 시 해당 카드만 편집 모드 전환 (문제 → textarea, 보기 → input, 정답 → select)
- AJAX POST → `/gisa/manage/question/<pk>/update/` → DOM 텍스트 갱신

### Gemini 해설 생성 (신규)

- "설명 가져오기" 버튼 클릭 → `/gisa/manage/question/<pk>/generate-exp/` API 호출
- `gisa_question_generate_exp` 뷰: Gemini API(`settings.GEMINI_EXPLAIN_MODEL`)로 해설 자동 생성
- Pydantic 모델로 구조화 응답: explanation + choice_1_exp~choice_4_exp
- 프롬프트: `generate_gisa_explanations.py`의 `build_prompt()`와 동일
- 생성된 해설은 편집 폼의 textarea에 자동 채움 + DB 저장
- `gisa_question_update` 뷰에도 explanation 필드 저장 기능 추가

### 관련 CSS

- `.edit-gemini`: 설명 가져오기 버튼 스타일
- `.ef-exp`: 해설 textarea 스타일

## 기사문제 관리 페이지 (gisa_question_manage.html)

`/gisa/manage/` — staff 전용 기사시험 문제 파싱/등록/수정 페이지.

### 좌측 패널 레이아웃

- 상단 고정 영역 (`.panel-left-top`): 자격증/시험/과목 셀렉터, 텍스트 입력, 직접 검색
- 하단 스크롤 영역 (`.parsed-list`): 파싱된 문제 목록만 스크롤
- CSS: `.panel-left { display: flex; flex-direction: column; overflow: hidden; }`
- `.panel-left-top { flex-shrink: 0; }`, `.parsed-list { flex: 1; overflow-y: auto; }`

## 다른 자격증 (별도 문서)

각 자격증의 데이터 현황·구축 절차·주의사항은 별도 문서에 있다. 해당
자격증 작업을 할 때 열어 볼 것.

- **[docs/조경기사.md](docs/조경기사.md)** — pk=5, 3,360문항 6과목
  (2013~2022). 쪽집게 노트 6과목(합계 190만자), comcbt PDF 답안표로
  정답 검증해 146건 수정한 경위, Gemini Gems 파일 9개 목록, 교재 배포
  스크립트. **실기 필답(40점)·작업형(도면) 화면의 상세도 여기 있다** — 기출 도면
  자료(`GisaDrawingRef`)·조감도·모눈종이 SVG·단계별 작도 재생.
- **[docs/식물보호기사.md](docs/식물보호기사.md)** — 기사 pk=1(3,631문항
  5과목), 산업기사 pk=2(3,207문항 4과목). 텍스트 파일 import 형식,
  회차×과목 100개 병렬 해설 생성, 쪽집게 노트 마크다운 구조(식물병리학·
  농림해충학), 용어집 5,870개 생성 방법. **실기 필답 22회차 438문항**(2023-1~2026-2)의
  적재 절차와 회차를 더할 때의 순서도 여기 있다.
- **[docs/실기합격전략.md](docs/실기합격전략.md)** — 식물보호 실기 합격 전략(회원용 글).
  기출 438문항을 세어 얻은 재출제율·분야 비중이 근거이고, 화면에서는 `essay_pass` 가
  이 문서를 읽어 보여 준다. 회차를 더하면 이 문서의 수치부터 고칠 것.


## 동영상 분류 관리 — 목차꼴 (2026-09)

`?tab=video` 의 관리 창에서 분류를 **목차처럼** 짠다(`1` · `1.1` · `2.2.1.1`).
`03_1_model` 의 목차 관리 화면(`templates/mypage/index.html` 의 `renderChapterTree`)을
사용자가 참고로 주어 그 결을 따랐다 — 번호·이름·줄마다 `↑ ↓ ＋형제 ↳자식 ✎수정 🗑`.

- **깊이 제한을 없앴다.** 처음에는 대분류 > 중분류 두 층이었는데, 어느 줄에나
  '자식 추가'가 있는 화면에서 두 층만 되면 어색하다. 모델의 `parent` 는 본래
  self-FK 라 손댈 것이 없었고, `video_tab_context` 가 재귀로 트리를 만들고
  `_video_node.html` 이 **자기를 include** 해 내려간다. 들여쓰기는 `lv0`~`lv4` CSS
- 관리 표는 **평평한 목록**(`vid_outline`)이다. 접기는 가지를 좇지 않고 위에서
  아래로 한 번 훑으며 '나보다 깊은 줄을 감춘다'로 푼다(`vdFold`) — 접힌 가지 안에
  또 접힌 가지가 있을 때 좇는 방식은 포인터가 엉킨다
- `＋형제`·`↳자식` 은 **그 줄 밑에 입력칸을 끼워 넣는다**. 같은 단추를 다시 누르면
  닫히고, 다른 단추를 누르면 종류가 바뀐다(`box.dataset.how`) — 종류를 가리지 않고
  닫으면 자식줄을 열어 둔 채 ＋형제 를 눌렀을 때 아무 일도 없는 것처럼 보인다
- 이름 고치기는 **그 줄에서 바로**(Enter 저장 · Esc 취소). prompt 창은 어느 줄을
  고치는지 안 보인다
- 셈("영상 3 · 아래 5")은 **뷰에서 한 문장으로 만든다**(`label`). 템플릿에서
  `{% if %}` 로 이어 붙였더니 영상이 없는 줄에 가운뎃점이 앞에 남았다
- **고친 뒤 주소를 다시 부르지 않는다**(`vdGo`). `location.href` 로 들어가면 관리
  창이 닫히고 화면이 맨 위로 튀어, 분류를 여럿 손볼 때 그때마다 다시 열고 다시
  내려와야 했다. 같은 주소를 fetch 해 `#vdTree`(관리 표)·`#vdList`(아래 목록)·
  `#vdCat`(옮길 자리 셀렉트)만 갈아 끼운다 — 스크롤·관리 창·접은 가지가 그대로다.
  접은 가지는 `data-id` 를 적어 두었다가 되살리고, fetch 가 실패하면 종전처럼
  주소를 다시 부른다. 분류뿐 아니라 영상 차례·분류 옮기기·삭제도 같은 길이다
- **손댄 줄을 1.1초 동안 반전시킨다**(`vdFlash`). 그 자리에서 갈아 끼우게 되면서
  무엇이 바뀌었는지 오히려 안 보였다 — 특히 ↑↓ 는 줄이 자리를 옮기는데도 눈에
  안 띈다. 분류는 줄 전체를 짙은 녹색으로, 영상은 카드에 진한 테두리를 두른다.
  화면 밖으로 밀려났으면 끌어다 보여 주고, 접힌 가지 안이면 펴 준다
  - 글자 색은 요소마다 달라 **끝 색을 하나씩 적어야 한다** — `color: inherit` 로는
    전이가 안 된다(`vtFlashName`·`vtFlashCode`·`vtFlashCnt`)
  - 같은 줄을 연달아 누르면 클래스가 이미 붙어 있어 애니메이션이 다시 돌지 않는다.
    떼었다가 `void el.offsetWidth` 로 리플로를 한 번 일으킨 뒤 다시 붙인다
  - 새로 만든 분류를 반전시키려면 id 가 필요해 `video_category_add` 가 `id` 를 돌려준다
  - **'가져와 등록' 도 같다** — `resource_add` 가 만든 `ids` 를 돌려주고 화면이 그
    카드로 끌어다 반전시킨다. 새 영상은 목록 아래쪽('분류 없음' 이면 맨 밑)에 생겨
    등록됐다는 글만으로는 어디 붙었는지 알 수 없었다. 여러 줄을 한꺼번에 넣으면
    모두 반전시키되 **끌어다 보여 주는 것은 첫 장만** 한다(`quiet`)
- 지우기는 하위 분류가 있어도 막지 않되 확인 문구가 그 사실을 말한다(FK CASCADE).
  **영상은 어느 경우에도 남아** '분류 없음' 으로 모인다

### 그 자리에서 갈아 끼우면 **열어 둔 탭이 옛 마크업에 굳는다**

예전에는 무슨 작업이든 `location.href` 로 주소를 다시 불렀으므로, 배포하면 다음
작업 때 새 화면을 받았다. 지금은 `#vdTree`·`#vdList` 안쪽만 바꾸므로 **카드에
단추가 늘어도 옛 탭에는 영영 안 나온다.** 더 나쁜 것은 그 래퍼가 없던 시절의
페이지다 — 갈아 끼울 자리를 못 찾아 아무 일도 일어나지 않고 영영 그대로다.

`video_tab_context` 가 조각 파일들의 mtime 으로 판(`vid_ver`)을 내려주고
`#vdList[data-ver]` 에 실어 둔다. `vdGo` 가 받아 온 판이 제 것과 다르거나 래퍼가
없으면 통째로 다시 읽는다. **프로세스 시각을 쓰면 안 된다** — 워커마다 값이 달라져
요청이 오갈 때마다 새로 고침이 걸린다. 파일 시각은 git 이 받아 둔 것이라 워커
둘이 같은 값을 본다.

`.vd-tools` 는 `flex-wrap: wrap` + `select { min-width: 0 }` 이다. 카드가
`overflow: hidden` 이라, 한 줄에 안 들어가는 단추는 접혀 내려가지 않으면 통째로
사라진다 — **있는데 안 보이는 것이 가장 헤매기 쉽다.**

### 등록 실패는 성공과 다르게 보여야 한다

`resource_add` 의 결과 줄은 성공도 거절도 같은 자리에 같은 작은 초록 글씨였다 —
'이미 있음', '가져오기 실패' 가 '등록 —' 과 구분되지 않아, 눌렀는데 안 됐다는 것을
알아채기 어려웠다("왜 추가가 안 되지?"). 지금은 줄마다 ✓/✕ 를 붙이고,
화면이 결과에 따라 색을 바꾼다 — 하나도 안 들어갔으면 **빨간 상자**(`.vd-msg.bad`),
여러 줄 중 일부만 들어갔으면 **주황**(`.part`). 실패했을 때 입력칸은 비우지 않는다.

> 진단할 때 nginx 접속 로그의 **응답 본문 크기**가 단서가 된다(`body_bytes_sent`).
> 같은 엔드포인트인데 유독 짧은 응답은 거절일 가능성이 크다. 다만 본문은 남지
> 않아 무엇이라 거절했는지는 알 수 없으므로, 화면에서 알아보게 하는 편이 낫다.

### 템플릿 JS 는 서버 테스트로 안 잡힌다 — `node --check` 를 돌릴 것

문자열 하나가 끊겨도 **HTML 은 멀쩡히 200** 을 주고, 브라우저에서만 그 `<script>`
블록이 통째로 죽는다. 실제로 파이썬으로 템플릿을 고치다 `
` 이 진짜 줄바꿈으로
들어가 `var msg = '… 지울까요?` 에서 문자열이 끊겼고, 그 아래 `vdFold` 부터 전부
`undefined` 가 됐다. 서버 렌더 검사(단추가 몇 개 있는가)는 모두 통과했다.

```bash
python _jscheck.py '/gisa/5/essay/work/?tab=video'   # 렌더된 <script> 를 node 로 파싱
```

## 동영상 AI 요약 (gisa/video_summary.py, 2026-09)

동영상 탭 카드마다 스태프에게 **「AI 요약」** 단추가 있다. 누르면 20~30초 뒤
요약 3~4줄 + **타임스탬프 목차**가 붙고, 회원은 「요약 보기」로 펴 본다.
**목차의 시각을 누르면 그 대목부터 영상이 열린다**(`.vd-ts` → `vdPlay` 에
`&start=` 를 실어 다시 끼운다) — 목차만 읽고 마는 것과 값어치가 다르다.

**Gemini 에 유튜브 주소를 그대로 준다**(`file_data.file_uri`). 내려받아 올릴
필요가 없고, **자막이 아니라 화면을 본다** — 조경 작도 강의처럼 '말이 아니라
손이 내용'인 영상에서 차이가 컸다. 실측에서 "T자와 삼각자로 경계선",
"원형 템플릿으로 교목 심볼", "인출선을 묶어 정돈"을 읽어냈고 자막에는 없는 말이다.

- **비용은 초당 약 95토큰**(실측: 11분 영상 62,972토큰, 한 편 30원 남짓).
  처음에 초당 263으로 어림잡아 "영상 직접은 수백 원, 자막을 긁어 쓰자"고
  보았는데 재 보니 그럴 까닭이 없었다. `media_resolution` 을 LOW/MEDIUM 으로
  바꿔도 **유튜브 주소는 토큰 수가 같다**(62,782 로 동일) — 만지지 말 것
- **client 를 변수에 담을 것.** `genai.Client(...).models.generate_content(...)`
  로 임시 객체에 바로 부르면 호출 도중 수거되어 `Cannot send a request, as the
  client has been closed` 가 난다(당했다)
- **길이를 재서 막지 말고 `end_offset` 으로 보는 데까지만 자른다**(`MAX_SECONDS`
  90분). 두 시간짜리 통강의를 물려도 토큰이 거기서 멈춘다(실측 11분 62,724 →
  `end_offset=120s` 10,935).
  - 처음에는 watch 페이지의 `lengthSeconds` 로 길이를 재 막았는데, 그 값이
    **집에서는 읽히고 서버(데이터센터 IP)에서는 응답에 아예 없어** 늘 0이었다 —
    막으려던 바로 그 자리에서 관문이 열려 있었다. oEmbed 도 길이를 주지 않는다.
    **유튜브가 IP 에 따라 다른 HTML 을 준다**는 것은 제목 긁기에서 이미 겪은 일인데
    또 걸렸다. 유튜브 HTML 에 기대는 코드는 반드시 서버에서 확인할 것
- 공개 영상만 된다. 비공개·삭제·한도 초과는 `_friendly()` 가 관리자가 무엇을
  해야 할지 아는 말로 바꿔 준다. 퍼가기를 막은 영상(`embeddable=False`)은
  요약은 되고, 목차 시각을 누르면 유튜브 새 탭으로 넘긴다
- 요약 HTML 은 **뷰에서 한 번만 만든다**(`video_tab_context` 가 `summary_html`).
  카드마다 필터를 부르면 목록 하나에 수십 번 돈다
- 모델은 `settings.GEMINI_VIDEO_MODEL`(`gemini-3.8-flash`)

## 자연생태복원기사 실기 작업형 (2026-09)

`/gisa/3/essay/work/`(로컬 6) — 조경과 같은 화면을 쓰되 **탭이 셋**이다:
동영상 · 기출분석 · 자료실. 설계 요소는 자료(`GisaEssayNote` slug `work-elements`)가
있을 때만 뜨는데 아직 없다(조경도 없어 양쪽 다 안 보인다 — 빈 '준비 중' 탭이
자리만 먹었다).

- `EXAM_INFO['자연생태복원기사']` 를 넣어 `work_part` 로 [필답형 | 작업형] 전환이
  생겼다. 필답 45 + 작업 55 · 90분/180분 · 합계 60점(과락 없음).
  **Q-net 종목코드와 소관 부처는 확인하지 못해 비워 두었다** — 지어내면 링크가
  엉뚱한 종목으로 가므로 템플릿이 없을 때 링크를 내지 않는다
- 개요의 "필답 25점 + 작업 35점" 은 조경 수치였다. `essay_target`·`work_target`
  으로 옮겨 종목마다 다르게 권한다(자연생태복원 30+30)
- 도면과제 42건은 사용자가 준 `년도별_도면_기출.png`(연도별 출제경향 2013~2026)를
  **Claude 가 직접 읽어** 옮겼다 → `load_eco_drawings.py --apply`(멱등).
  2016-2 의 `폐도록복원` 은 원문 오타라 고쳤다. 표에서 붉게 덧쓰인 칸
  (2025-3 · 2026-1)과 회색 칸(2026-2)은 `note` 에 그대로 적어 두었다
- **다섯 유형이 돌아가며 나온다** — 옥상잠자리·벽면녹화·우수체계 10 · 조류관찰
  생태공원 9 · 적지분석·생태연못 8 · 적지분석·생태통로 8 · 폐도로복원 6.
  `(변형)` 은 제목을 나누지 말고 `note` 에 적을 것 — 나누면 빈도가 흩어진다

### 조경 기준으로 박혀 있던 것 셋을 종목별로 풀었다

| 박혀 있던 것 | 지금 |
|---|---|
| 도면 색 `DRAWING_COLORS`(번호별) | 번호가 없으면 팔레트를 차례로 돌려 쓴다 |
| 연도표 칸 `[1,2,4]`(3회 있으면 1~4) | **절반 넘는 해에 나오는 회차**를 자리로 삼고, 그 해에만 있는 회차를 덧붙인다(`round_label`) |
| "같은 **번호**면 같은 도면" | 번호가 있는 종목만 그렇게 적는다(`has_codes`) |

## 조경기사 실기 작업형(도면) 화면 (2026-09)

`/gisa/<id>/essay/work/` — 실기 페이지 머리의 **[필답형 | 작업형]** 전환으로 들어온다(`EXAM_INFO` 의
`work_part`, 조경 두 급수만). 탭은 개요 · 도면 기본기 · **기출분석** · 설계 요소. 상세·경위는
**[docs/조경기사.md](docs/조경기사.md)** 의 '실기 작업형(도면) 화면' 절.

### 기출분석 탭 — 자료가 '출제 예상 투표' 줄 안에 있다

차례는 **출제 예상 투표 → 출제 빈도 → 연도별 출제 도면**. 따로 있던 '기출 도면' 탭은 없앴다(옛 주소
`?tab=sheets` 는 기출분석으로 받는다).

- 투표 항목과 도면 자료(`GisaDrawingRef`)는 **도면 번호(없으면 이름)로 잇는다.** 자료가 붙은 줄에
  `자료 N벌` 배지가 달리고, 줄을 누르면 그 자리에서 펼쳐진다. 같은 도면이 여러 회차 투표에 나오면
  가장 최근 줄에만 단다(뷰의 `used`). 자료 한 벌의 마크업은 조각 `gisa/_drawing_pane.html`
- 줄 차례: **이미 출제된 도면은 맨 아래, '신출'은 그 위**(순위·득표는 그대로, 보이는 차례만)
- 자료 없는 줄은 눌러서 연도별 표의 그 도면만 드러낸다. 펼친 줄은 '연도별 표에서 보기' 단추로
- 도면 확대 보기 중 **브라우저 '뒤로'는 도면만 닫는다**(`pushState` + `popstate`; ✕·Esc 로 닫을 때는
  `history.back()` 으로 그 칸을 도로 뺀다)

### 도면 자료 — `_ls_drawing_refs/<번호>[_<탭 이름>]/` → `load_ls_drawing_ref.py --apply <번호>`

한 도면에 자료가 여러 벌이면 탭으로 나뉜다(`source` = 탭 이름, `order` = 차례).

| 탭 | 내용 |
|----|------|
| **성운** (19종 전부) | `문제지 그대로` + `답안 도면 읽기`(범례·시설물 수량표 **SVG**·조건 대조표·수목 수량표). 317쪽 이상은 조경실기2(`01 교재(PDF)/단면도_페이지_NNN.jpg`, 교재 쪽 = 파일 번호 + 316), 316쪽 이하는 조경실기1 PDF(텍스트 층 없음). 답안지는 `rotate(-90)` |
| **My** (401·428·444, 맨 앞) | 사용자가 직접 그린 도면. 401·444 는 워드 작도 순서를 **번호·문장·빨간 화살표 그대로** 옮긴 것 + 모눈종이 도면이고(오탈자도 고치지 않는다 — 사용자 지시), 428 은 트레이싱지 답안 사진 두 장(종합설계도·단면상세도)뿐이다 |
| **조감도** (19종 전부) | GPT 입체 조감도 + 만든 방법 + 도면 대조표 + **마지막 회차 프롬프트만** |
| 이름 없는 자료·사용자 A | 먼저 있던 작도 요령 |

- **답안이 문제 조건과 어긋나면 자료에 적는다** — 319 교목 6종(10종 요구) · 412 낙엽교목 6종(7종) ·
  345 조각물 수 · 287 눈향·조팝나무가 〈보기〉 밖 · 264 진입공간 1곳만 표기. 모범답안이라고 그대로
  옮기면 수험자가 틀린 조건을 따라 그린다. **도면에서 못 읽은 수치는 지어내지 말고 비운다**
- 탭 이름을 바꾸면 옛 자료가 DB 에 따로 남는다(키가 번호+이름+탭 이름) → `drop_drawing_ref.py <번호> <탭> --apply`
- 화면 수정은 Toast UI WYSIWYG. raw SVG 는 `⟦그림 N⟧`·`⟦기호 N⟧` 표식으로 지켰다가 되돌린다.
  SVG 도면이 든 자료는 5~6만 자라 저장 한도가 12만 자다. 코드 블록은 **들여쓰기**로 쓴다(마크다운
  확장이 `tables` 뿐이라 펜스가 안 먹는다). `pre` 는 `pre-wrap` 으로 접는다
- 조감도 탭(`.dw-pane.bv`)만 그림을 폭 가득 크게 보인다

### 조감도 만드는 법 — GPT 가 기본, 통째로 다시 그리게 한다

`gpt-image-2.5-sunburst` 의 `images.edit` 에 **그림 여러 장**을 준다(장당 약 $0.04).

1. **도면을 첫 참고 그림으로** 주고 도면을 글로 풀어 쓴 프롬프트로 1회차. 시점은 "남동 상공 45°, 북쪽이 위"
2. 2회차부터는 **도면을 다시 첫 그림으로**, 앞 회차 그림을 둘째로 주고 "나열한 것만 고치고 나머지는
   그대로". 1회차가 평면에 가까우면 시점만 바꾸는 회차를 따로 둔다
3. 회차마다 **Claude 가 도면과 대조**한다 — 부지 모양·주변, 진입구와 도로 접속, 시설 수, 없던 것이
   생겼는지, 글자 없음

- **마스크 부분 수정·그림을 손으로 자르고 돌리는 일은 하지 않는다.** 444 에서 장애인 주차칸을 옆 열에
  맞춘다고 옮기다 순환 차로를 막고, 비스듬한 조감도에서 칸만 수평으로 세워 버렸다
- 개수는 "EXACTLY N", 없앨 것은 위치를 짚는다. **작은 시설은 형태를 정의해야** 나온다("데크는
  발코니처럼 튀어나온 것" — 위치만 말하면 그 자리에 안내판만 선다). **도면에 없는 것(차단기 등)을
  모델이 덧붙이므로 "없다"고 명시**한다
- 손그림·모눈 도면보다 **좌표로 그린 깨끗한 색 배치도**(물 파랑·데크 주황…)를 기준 그림으로 주면
  1회차부터 배치가 맞는다. 부분 수정이 4~5회 쌓이면 화질이 떨어지므로, 마지막에 배치 기준(직전 그림)과
  화질 기준(1회차 그림)을 따로 주고 새로 렌더한다
- 제미나이는 질감은 낫지만 도면 해독이 약하고 **한 번에 한두 곳만** 고쳐진다(401 은 6회차). 도면을 "실선만
  진하게" 다시 그리게 하면 선 위치는 맞아도 P점 번호·눈금 숫자가 바뀐다(23→33) — 기준 도면으로 못 쓴다

### 모눈종이 도면 → SVG → 단계별 작도 재생 (401 My)

- **옮기기**: 사진을 인쇄된 눈금 틀 네 모서리로 펴 1m = 20px 로 만들고(OpenCV), 구역별로 확대해 좌표를
  m 단위로 읽어 코드로 그린다(`make_grid401_svg.py`). 그린 뒤 **편 사진에 빨갛게 겹쳐 검증**한다.
  직선 시설은 m 단위로 맞고 자유곡선은 ±1m 근사. 보조선은 연하고 가늘게(0.06, `#a3a9b3`), 실선은 0.24
- **단계 묶음**: 생성기에서 `S(n)` 뒤에 그린 것이 `<g data-step="n">` 에 들어간다. 겹치는 차례는
  `ZORDER` 로 따로 둔다. 단계 제목은 `<svg data-steps='[…]'>`
- **한 선씩 그리기**: 생성기에서 `T(i)` 뒤에 그린 것은 `<g data-sub="i">`(워드의 ①②③ 한 줄 = 한 컷)에 들어간다.
  선은 **워드의 화살표 방향대로 점을 적는다**(←P17 이면 오른쪽 → 왼쪽) — 화면이 `stroke-dashoffset` 으로 그
  차례·방향대로 긋고, 오른쪽 설명의 그 줄을 짙게 칠한다. 401 은 (1)~(7) 만 나눠 두었다 — (8) 이후는 워드에
  점 번호·방향이 없어 못 나눈다(문서를 한 선씩 적어 주면 이어 붙인다)
- **화면**(`initSteps`, `essay_work.html`): `svg[data-steps]` 면 어느 도면이든 단추(처음부터 · ◀ 이전 ·
  다음 ▶ · 전체 보기)가 붙는다. k 단계 선은 빨강, 설명은 같은 자료의 **"(k) 제목" 아래 목록을 그대로**
  가져온다. **도면은 단추 바로 아래에 고정하고 설명은 오른쪽 칸(sticky)** — 설명을 위에 두면 단계마다
  높이가 달라 도면이 위아래로 밀린다. 휴대폰에서는 단계 이름을 고정 높이의 제 줄에 둔다(단추 줄이
  한 줄/두 줄로 바뀌어도 밀린다)

## 자연생태복원기사 (로컬 pk=6, 서버 pk=3)

### 데이터 현황

- 데이터: 2012~2025년 필기 기출, 총 **3,880문항** (41회차)
- 회차당 100문항 (과목별 20문항), 2022년 이후는 80문항
- 출처가 둘이다: **2012~2022는 comcbt PDF**(텍스트 레이어 있음, 자동 파싱), **2023~2025는 문제집 스캔본**(텍스트 레이어 없음, LLM이 직접 판독)

> ⚠️ **2022년에 출제 체계가 전면 개편되어 과목명 자체가 교체되었다.** 과목이 하나 빠진 게 아니라 체계가 바뀐 것이므로, 연도별로 다른 과목표를 써야 한다. PDF 원본의 `N과목 : 과목명` 표시로 확인 가능.

| 체계 | 연도 | 과목 (번호 범위) | 문항 |
|------|------|------------------|------|
| 구 | 2012~2021 | 환경생태학개론(1~20) · 환경계획학(21~40) · 생태복원공학(41~60) · 경관생태학(61~80) · 자연환경관계법규(81~100) | 3,000 (각 600) |
| 신 | 2022~2025 | 생태환경조사분석(1~20) · 생태복원계획(21~40) · 생태복원설계·시공(41~60) · 생태복원 사후관리·평가(61~80) | 880 (각 220) |

`GisaSubject`에는 **9개 과목이 모두 등록**되어 있다(구5 + 신4). `parse_eco.py`의 `subject_of(num, year)`가 `SUBJECT_REFORM_YEAR=2022` 기준으로 표를 갈라 쓴다.

> 과거에 이 개편을 놓쳐 2022년 61~80번(법규·사후관리 문제)이 '경관생태학'으로 잘못 배정된 적이 있다. 연도별 과목표 분리로 수정 완료.
- 이미지 **340개** (수식·그래프·[보기]박스) — 306문항이 이미지 포함
- AI 해설: 전체 Gemini 해설 생성 완료 (당시 gemini-3-flash-preview)

> ⚠️ **로컬 pk=6, 서버 pk=3**으로 다릅니다. 이미지 경로는 로컬 기준 `c6/`으로 생성돼 서버에도 `c6/`로 배포됐습니다(정상 동작). 서버에서 신규 문항을 추가하면 `c3/`로 생성되지만 파일명이 `eco*`로 고유해 충돌 위험은 없습니다.

### 필기 데이터 구축 이력

2012~2025 필기 3,880문항을 만든 절차는 모두 끝났다. 상세는
**[docs/자연생태복원_필기구축.md](docs/자연생태복원_필기구축.md)** 참조 —
comcbt PDF 자동 파싱(`parse_eco.py`)과 이미지 매칭에서 지켜야 할 3가지,
2023~2025 스캔본 LLM 판독과 회차별 페이지 매핑, 정답표 오류 4건 정정 근거,
선지별 해설 보강이 필수인 이유(UI가 `explanation`을 안 쓴다), 배포 명령,
쪽집게 노트 9과목(176만자) 작성 패턴과 법 개정 병기 14항목.


## 실기 필답형 (별도 문서)

실기 필답(출제·답안·AI 채점·손글씨 판독·첨삭·시험지 인쇄)의 상세는
**[docs/실기필답.md](docs/실기필답.md)**. 채점·판독 코드를 고칠 때 먼저 읽을 것.
꼭 지킬 것만 여기 둔다:

- 답을 쓴 문항은 **모두 LLM 이 채점**한다(문자열 비교·수치만 보는 규칙 채점은 걷어냈다). 코드는 자르기와 더하기만
- 판독과 채점은 반드시 분리한다(판독 → 사용자 확인 → 채점)
- 모델 이름은 `config/settings.py` 에만 둔다. 손글씨 판독만 preview(정확도)
- 문제문은 저작권 때문에 "조사 정도만" 재서술한 것이다. 용어·수치·답 개수 지시는 건드리지 않는다


## EC2 배포

- 서버: `ubuntu@hanulstudy.kr`
- SSH 키: `C:\AWS\knou_key2.pem`
- SSH 포트: **22 + 60022** 둘 다 열려있음 (도서관 등 22 차단 환경 대응)
- 접속(기본): `ssh -o ServerAliveInterval=60 -i "C:\AWS\knou_key2.pem" ubuntu@hanulstudy.kr`
- 접속(공공 와이파이): `ssh -p 60022 -o ServerAliveInterval=60 -i "C:\AWS\knou_key2.pem" ubuntu@hanulstudy.kr`
- 프로젝트 경로: `/home/ubuntu/knou_agriculture/`
- 가상환경: `/home/ubuntu/knou_agriculture/venv/` (프로젝트 내부)
- 가상환경 자동 활성화: `~/.bashrc`에 `source $HOME/venv/bin/activate` 추가
- 배포 절차: `git push` → SSH 접속 → `cd ~/knou_agriculture && git pull && sudo systemctl restart gunicorn`

### 시스템 사양 및 자원

- **인스턴스**: vCPU 2, RAM 1.9GB (t2/t3 small급), EBS 29GB (현 사용 약 6GB, 여유 23GB+)
- **스왑**: `/swapfile` 1GB (응급용 안전망). 부팅 시 자동 활성화
- **swappiness**: 10 (메모리 압박 시에만 스왑 사용 — 평상시 0B 유지)
- **PostgreSQL 18** (DB 크기 약 67MB), nginx, gunicorn 워커 2개

평상시 CPU idle 100%, 메모리 39% 사용으로 매우 여유. 회원 200명까지 현 사양에서 무리 없음.

**스왑 재설정 절차** (인스턴스 교체·복구 시):
```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
sudo sysctl -p /etc/sysctl.d/99-swappiness.conf
```

### 네트워크별 SSH 접속 가능 여부

도서관·일부 카페·공항 등 **공공 와이파이 환경에서는 22번 포트 아웃바운드를 차단**하므로 22번 SSH 접속이 불가능하다. 웹사이트(443)는 정상 작동하지만 SSH만 막힘. AWS 보안 그룹 문제가 아니라 사용자 측 네트워크의 발신 차단이 원인.

이를 우회하기 위해 **60022 포트를 추가 개방**해두었음. 공공 와이파이는 보통 자주 쓰는 22·21·23 정도만 차단하므로 60022 같은 비표준 포트는 통과.

| 네트워크 | SSH(22) | SSH(60022) | 웹(443) |
|----------|---------|------------|---------|
| 집/회사 유선·와이파이 | ✓ | ✓ | ✓ |
| 휴대폰 테더링 | ✓ | ✓ | ✓ |
| 도서관·공공 와이파이 | ✕ | **✓** | ✓ |

**60022 추가 설정 내역** (재현·복구용):
1. AWS 보안 그룹: 사용자 지정 TCP, 60022, 0.0.0.0/0 인바운드 규칙 추가
2. EC2(Ubuntu 24.04+)는 `ssh.socket` socket-activation 방식이라 `sshd_config`의 `Port` 디렉티브가 무시됨. **반드시 `ssh.socket` override**로 추가:
   ```
   sudo mkdir -p /etc/systemd/system/ssh.socket.d
   sudo tee /etc/systemd/system/ssh.socket.d/99-alt-port.conf <<'EOF'
   [Socket]
   ListenStream=60022
   EOF
   sudo systemctl daemon-reload
   sudo systemctl restart ssh.socket
   ```
3. 확인: `sudo ss -tlnp | grep -E ':22 |:60022'` 으로 둘 다 리스닝되는지 확인

**그래도 SSH가 모두 막힌 환경에서의 우회**:
- **AWS EC2 Instance Connect**: AWS 콘솔 → EC2 → 인스턴스 → "연결" → "EC2 Instance Connect" 탭. 브라우저 안에서 셸 사용 (HTTPS로 통과)
- **AWS Systems Manager Session Manager**: 22번 포트 불필요, IAM 권한 설정 필요

Claude Code에서 SSH가 안 되는 환경이면 사용자가 Instance Connect로 명령 실행한 결과를 복붙해주는 방식으로 작업 진행.

## 공지사항 게시판 (bbs 앱)

### 모델 (bbs/models.py)

| 모델 | 설명 | 주요 필드 |
|------|------|-----------|
| `Notice` | 공지사항 | title, content(Summernote HTML), author(FK), is_pinned, view_count, created_at |
| `Comment` | 댓글 | notice(FK), author(FK), content, created_at |

- `is_pinned`: 상단 고정 여부 (BooleanField, default=False)
- `ordering`: `["-is_pinned", "-created_at"]` — 고정글 우선, 최신순

### 공지사항 이메일 발송

공지사항 등록 시 이메일 수신 동의한 전체 활성 회원에게 HTML 이메일을 발송한다.

- 발송 방식: `threading.Thread(daemon=True)`로 비동기 발송 (사용자 응답 지연 없음)
- 수신자: BCC로 일괄 발송 (수신자 간 이메일 주소 미노출)
- 발신자: `admin@hanulstudy.kr`
- 이메일 형식: HTML (`content_subtype = "html"`)
- 이미지: Summernote의 상대 경로(`/media/...`)를 절대 URL(`https://hanulstudy.kr/media/...`)로 자동 변환
- opt-out: `UserProfile.receive_email=False`인 회원은 발송 대상에서 제외

### 회원별 이메일 수신 토글

`accounts/models.py`의 `UserProfile` 모델로 회원별 이메일 수신 여부를 관리한다.

- `UserProfile.receive_email`: BooleanField (default=True)
- `/manage/members/` 회원관리 페이지에서 토글 버튼으로 ON/OFF 제어
- `member_toggle` 뷰에서 `receive_email` 필드 처리 (profile `get_or_create`)
- 관련 파일: `accounts/models.py`, `main/views.py`, `bbs/views.py`, `templates/main/member_manage.html`

### 서버 일괄 제어 (Django shell)

```bash
# 전체 회원 이메일 수신 비활성화
ssh ... ubuntu@hanulstudy.kr 'cd ~/knou_agriculture && source venv/bin/activate && python manage.py shell -c "
from accounts.models import UserProfile
from django.contrib.auth.models import User
for u in User.objects.all():
    UserProfile.objects.get_or_create(user=u)
UserProfile.objects.update(receive_email=False)
"'

# 전체 활성화: UserProfile.objects.update(receive_email=True)
```

## 강의 자막 → 워드 강의록 변환

조경기사 강의 srt 자막을 워드 문서로 만드는 작업. 상세는
**[docs/강의록변환.md](docs/강의록변환.md)** 참조 — 텍스트 단계에서 모두
처리하고 워드는 한 번만 생성하는 원칙, 한자 병기 사전(한국 조경사 35개 항목),
STT 오타 사례표, 일본어 음독 → 한자 표기 매핑(20개), docx 스타일 규칙.


## 운영 기능 (별도 문서)

이미 만들어져 돌아가는 기능들. 해당 기능을 고칠 때 열어 볼 것.
**[docs/운영기능.md](docs/운영기능.md)**

- **모의고사 세대(Round)** — `MockGeneration` 모델, 과목 단위 라운드 관리,
  답안 선택 즉시 누적하는 이유, 풀 소진 시 자동 +1, R 배지 표시 규칙
- **기출학습 진도율** — `GisaStudyLog`, 학습기록÷문항수, 오답율 배지
- **사용자 활동 분석** — 활성 판정 기준(풀이 0건이어도 PDF 열람하면 활성),
  비활성 4분류, 이중 가입 탐지, 학습모드는 정답률 0%로 잡히는 함정
- **PDF 자료실** — 다운로드 차단 4중 방어, 워터마크, 열람·인쇄 추적
- **회원 가입·승인** — 관리자 승인 후에만 인증 메일 발송, 7일 자동 삭제
- **페이지 조회 추적** — `SubjectViewLog`/`CertificationViewLog`, 조회와
  풀이의 차이


## 문항 이미지 판독·재생성

저해상도 스캔 이미지를 텍스트화하거나 Gemini 로 다시 그리는 작업. 상세는
**[docs/문항이미지.md](docs/문항이미지.md)** 참조 — 텍스트인지 그림인지 먼저
판정하는 기준(263건 중 230건이 텍스트였다), `[box]` 텍스트화 후 중복 이미지
제거, 보기 4개를 2×2 격자로 한 번에 생성해야 스타일이 통일된다는 점,
실패 사례와 대응표, `vurl` 필터로 브라우저 캐시 무력화, 장당 $0.13 비용.




## 작업형 CAD 탭 (별도 문서)

CAD(제도판 모사 — I자·삼각자·템플릿·스케일자·샤프, 지시선, 수목 군식, 수량표, 작도 재생 …)의
기능·기준·함정은 모두 **[docs/CAD.md](docs/CAD.md)** 에 있다. **CAD 를 고치기 전에 반드시 읽고,
고친 것과 겪은 함정은 그 문서에 적는다.** 꼭 지킬 것만 여기 둔다:

- **특허 출원 전까지 스태프만 쓴다** — 탭 단추·화면 코드·API(`_staff_only`)·재생 단추 세 곳
- 화면은 `templates/gisa/_cad.html` 한 파일. 고친 뒤 `<script>` 를 뽑아 `node --check` 로 문법 검사 —
  서버는 200 을 주는데 브라우저에서만 블록이 통째로 죽는다
- **대표님 화면 그대로 재현해 확인**한다(맞춤 배율, 실제 도면). Playwright + 개발 서버(`--noreload` 면 다시 띄울 것)
- 서버 도면을 직접 고칠 때는 **백업 → 판(stamp) 확인 → 고치기**, 그리고 대표님께 "저장하지 말고 새로 고침"을 알린다
- 기준은 대표님 실물 사진·지적에서 나온다 — 사진은 화소를 세어 옮긴다

## 블렌더 모형 · 도면 소개 영상 · 이미지 모델 (별도 문서)

- **[docs/도면영상.md](docs/도면영상.md)** — 블렌더로 도면 세우기(make428·401·444, anim444), 444 소개 영상에서 대표님이 정한 규칙(흐름·차 장면·힉스필드 CLI)
- **[docs/GPT이미지.md](docs/GPT이미지.md)** — GPT·Gemini 이미지 모델 화법·덧그리기·화소 검증, 인포그래픽 글자 검증
