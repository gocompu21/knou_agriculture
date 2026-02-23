# CLAUDE.md

This file provides guidance when working with code in this repository.

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
python manage.py generate_explanations --model gemini-3-flash-preview
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
- 8,940문제 전체 해설 생성 완료 (gemini-2.5-flash 사용, 현재 기본 모델: gemini-3-flash-preview)

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

### 대상 자격증

- **식물보호기사** (pk=1, category='기사')
- 데이터: 2011~2022년 필기 기출문제, 총 660문제 (33개 회차 × 20문항)
- 과목: 식물병리학, 농림해충학, 재배학원론, 농약학, 잡초방제학 (5과목)

- **식물보호산업기사** (pk=2, category='산업기사')
- 데이터: 2002~2020년 필기 기출문제, 총 2,880문제 (36개 회차 × 80문항)
- 과목: 식물병리학(pk=6), 해충학(pk=7), 농약학(pk=8), 잡초방제학(pk=9) (4과목)
- 문제 번호: 1~80 통번호 (과목1: 1~20, 과목2: 21~40, 과목3: 41~60, 과목4: 61~80)
- 데이터 원본: comcbt.com에서 다운로드한 PDF (`data/comcbt/식물보호산업기사YYYY-R.pdf`)
- PDF 파싱: LLM 에이전트 6배치 병렬로 직접 읽어서 파싱 (파싱 스크립트 없음)
- AI 해설: 2,880문제 전체 Gemini 해설 생성 완료 (gemini-2.5-flash)

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

### 산업기사 병렬 해설 생성

```bash
# 식물보호산업기사 전체 (36회차 × 4과목 = 144단위, 100개 병렬)
python generate_sanup_explanations.py
```

- `generate_sanup_explanations.py`: 회차×과목 단위 subprocess로 `generate_gisa_explanations`를 병렬 실행
- `WORKERS=100`, `DELAY=0.3`, `MODEL=gemini-2.5-flash`
- `--cert 식물보호산업기사`로 자격증명 필터링
- 주의: 100개 동시 실행 시 PostgreSQL 커넥션 풀 한도 초과로 일부 실패 가능 (재실행으로 해결)

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

### 핵심정리 마크다운 구조 (식물병리학_핵심정리.md)

```markdown
# 식물병리학 핵심정리
## 제1장. 식물병의 기초 개념
### 1.1 병의 정의와 병 삼각형
- 핵심 내용...
**관련 문제**: (2011-1-5), (2012-2-2)
### 1.2 병징과 표징
#### 1.2.1 병징
...
### 핵심 키워드 요약     ← 각 장 끝에 키워드 요약 테이블
| 키워드 | 핵심 포인트 |
|--------|------------|
| 병 삼각형 | 기주, 병원체, 환경 |
---
## 제2장. ...
```

- 총 14장 + 부록 (병원체-병명 대조표, 파이토플라스마 병, 방제법 비교)
- 660/660 문제 커버리지 100% (2011~2022년 전 회차)
- 각 장 끝에 `### 핵심 키워드 요약` 테이블 포함

### 핵심정리 마크다운 구조 (농림해충학_핵심정리.md)

- 총 13장 + 부록 8개 표 (3689줄)
- 1~3장: 곤충 외부형태, 내부구조, 발육/변태 (기초)
- 4~6장: 분류, 생태, 방제총론
- 7~9장: 벼/밭작물/채소 해충
- 10~13장: 과수/산림/저장/응애 해충
- 부록: 곤충목별 해충 일람, 매개충-병해 대조, 월동태, 변태유형, 세대수, 천적, 비래해충, 외래해충 표
- 660/660 문제 커버리지 100% (2011~2022년 전 회차)
- 식물병리학과 동일한 마크다운 형식 (`## 제N장.` → `### N.M` → `#### N.M.K`)
- 소제목: `[ **소제목** ]` 형태 (볼드+대괄호, `#####` 사용 안 함)
- 생성 과정: 장 단위 병렬 에이전트(4배치) → 통합 → 커버리지 보완(3배치) → 100% 달성

### 주요 파일 구조 (gisa 앱)

```
gisa/
├── models.py           # Certification, GisaExam, GisaSubject, GisaQuestion, GisaTextbook, GisaAttempt
├── views.py            # parse_study_guide(), certification_list/detail, study/exam/mock/wrong 뷰
├── urls.py             # app_name='gisa', 13개 URL 패턴
├── admin.py            # 5개 모델 Admin 등록
└── management/commands/
    ├── import_gisa_questions.py       # 텍스트 파일 → DB import
    └── generate_gisa_explanations.py  # Gemini 해설 생성

templates/gisa/
├── certification_list.html    # 자격증 목록
├── certification_detail.html  # 자격증 상세 (교재/학습/풀이/모의/오답/이력 탭)
├── study_mode.html            # 학습모드 (교재 학습 겸용)
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
└── data/               # 엑셀 파일 + 핵심정리 마크다운 (gitignore)
    └── comcbt/         # 식물보호산업기사 PDF/HWP (36회차, comcbt.com 원본)
```

## 알려진 주의사항

### 방송대 기출 (exam 앱)
- 올에이클래스 HTML에는 "중복답안 가이드" 범례 테이블이 답안표 앞에 존재함. 정답 파싱 시 반드시 `allaAnswerTableDiv` 영역 내에서만 추출해야 함 (범례의 A~K 코드가 정답으로 오인될 수 있음)
- 동명 과목(글쓰기 등)이 여러 학년에 존재하므로 `--grade` 옵션으로 구분 필요
- `Question.answer`는 CharField이며 `'1,2'` 형태의 문자열로 복수 정답을 표현함 (IntegerField 아님)
- 학습모드 JS에서 정답 비교 시 `split(',')` + `indexOf`로 처리 (parseInt 사용 금지)

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

- O 마크 위치: `top: 0.8em; left: 50%` (line-height 1.6의 중앙)
- X 마크 위치: `top: 0.55em; left: 30%` (시각적 보정)
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
