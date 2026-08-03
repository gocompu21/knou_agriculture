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
- 데이터: 2011~2024년 필기 기출문제, 총 3,631문제 (35회차 필기 + 최신기출)
- 과목: 식물병리학, 농림해충학, 재배학원론, 농약학, 잡초방제학 (5과목)
- 2023년 1회 필기(100문항), 2024년 1회 필기(100문항) 추가 완료

- **식물보호산업기사** (pk=2, category='산업기사')
- 데이터: 2002~2024년 필기 기출문제, 총 3,207문제 (40회차 필기 + 최신기출)
- 과목: 식물병리학(pk=6), 해충학(pk=7), 농약학(pk=8), 잡초방제학(pk=9) (4과목)
- 문제 번호: 1~80 통번호 (과목1: 1~20, 과목2: 21~40, 과목3: 41~60, 과목4: 61~80)
- 데이터 원본: comcbt.com에서 다운로드한 PDF (`data/comcbt/식물보호산업기사YYYY-R.pdf`)
- PDF 파싱: LLM 에이전트 6배치 병렬로 직접 읽어서 파싱 (파싱 스크립트 없음)
- AI 해설: 전체 Gemini 해설 생성 완료 (현재 기본 모델: gemini-3-flash-preview)
- 2023년 1회(80문항), 2024년 1회(80문항) 추가 완료 + 쪽집게 노트 보강

- **조경기사** (pk=5, category='기사') — 3,480문항, 6과목. 상세는 아래 「조경기사」 섹션 참조
- **자연생태복원기사** (로컬 pk=6 / 서버 pk=3, category='기사') — 3,160문항, 5과목. 상세는 아래 「자연생태복원기사」 섹션 참조

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
- `WORKERS=100`, `DELAY=0.3`, `MODEL=gemini-3-flash-preview`
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

## 식물보호기사 용어집 (5,870개)

식물보호기사(pk=1) 5과목 쪽집게 노트의 볼드 용어를 추출하여 `GisaGlossary`에 저장:

| 과목 | 용어 수 |
|------|---------|
| 식물병리학 | 912 |
| 농림해충학 | 1,294 |
| 재배학원론 | 1,705 |
| 농약학 | 1,141 |
| 잡초방제학 | 818 |

- 추출: `re.findall(r'\*\*(.+?)\*\*', tb.content)` (2글자 이상, "관련"/"핵심" 제외)
- 설명 생성: Gemini 3 Flash Preview, 배치 100개 단위, 총 62회 호출
- 스크립트: `_generate_glossary_desc.py`

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
- `gisa_question_generate_exp` 뷰: Gemini API(`gemini-3-flash-preview`)로 해설 자동 생성
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

## 조경기사 (pk=5, category='기사')

### 데이터 현황

- 데이터: 2013~2022년 필기 기출문제, 총 3,360문제 (28회차)
- 과목: 조경사(pk=18), 조경계획(pk=19), 조경설계(pk=20), 조경식재(pk=21), 조경시공구조학(pk=22), 조경관리론(pk=23) (6과목)
- 회차당 120문제 (과목별 20문제)
- 회차: 2013~2018년 각 1,2,4회 / 2019년 1,2,3회 / 2020년 2,3,4회 / 2021년 1,2,4회 / 2022년 1회
- 정답: 28회차 전체 PDF 답안표 기반 검증 완료 (146건 수정, 해설 재생성)
- AI 해설: 전체 Gemini 해설 생성 완료

### 쪽집게 노트 (6과목 전체 완성)

| 과목 | 장 수 | content 크기 |
|------|-------|-------------|
| 조경사 | 14장 | 219,239자 (445KB) |
| 조경계획 | 13장 | 180,739자 (380KB) |
| 조경설계 | 14장 | 178,303자 (365KB) |
| 조경식재 | 13장 | 159,893자 (320KB) |
| 조경시공구조학 | 12장 | 163,630자 (335KB) |
| 조경관리론 | 12장 | 158,707자 (330KB) |

- 6과목 전체 검증 완료 (내용 정확성 + 구조적 배치)
- 교재형 서술 스타일 (식물보호기사와 동일한 마크다운 형식)

### 기출문제 데이터 원본

- comcbt.com에서 다운로드한 PDF (`data/comcbt/조경기사YYYY-R.pdf`)
- PDF 파싱: LLM 에이전트로 직접 읽어서 파싱
- 정답 검증: PDF 답안표와 DB 정답 대조 → 146건 불일치 수정 (2013-2022 전체)

### Gemini Gems 파일

조경기사 Gemini Gems용 파일 (프로젝트 루트, `_gem_` prefix):

| 파일 | 크기 | 용도 |
|------|------|------|
| `_gem_조경기사_프롬프트.md` | 2.9KB | Gems Instructions에 붙여넣기 |
| `_gem_조경기사_기출문제.json` | 6.3MB | 3,360문제 + 정답 + 해설 |
| `_gem_조경기사_시험정보.md` | 4.7KB | 합격기준, 출제경향, 과목별 전략 |
| `_gem_조경기사_조경사.md` | 445KB | 쪽집게 노트 |
| `_gem_조경기사_조경계획.md` | 380KB | 쪽집게 노트 |
| `_gem_조경기사_조경설계.md` | 365KB | 쪽집게 노트 |
| `_gem_조경기사_조경식재.md` | 320KB | 쪽집게 노트 |
| `_gem_조경기사_조경시공구조학.md` | 335KB | 쪽집게 노트 |
| `_gem_조경기사_조경관리론.md` | 330KB | 쪽집게 노트 |

- Gems 설정: Name에 `조경기사 AI 튜터`, Instructions에 프롬프트 파일 내용, Knowledge에 나머지 8개 파일 업로드
- Gems 제한: 최대 10개 파일, 파일당 100MB (현재 9개 파일, 합계 약 8.2MB)

### 교재 배포 스크립트

| 파일 | 용도 |
|------|------|
| `_deploy_3_textbooks_fix.py` + `.json` | 조경사/조경식재/조경시공구조학 3과목 교재 서버 반영 |
| `_deploy_jogsa_ref.py` + `_deploy_jogsa_ref_fix.json` | 조경사 관련문제 수정본 서버 반영 |

## 자연생태복원기사 (로컬 pk=6, 서버 pk=3)

### 데이터 현황

- 데이터: 2012~2022년 필기 기출, 총 **3,160문항** (32회차)
- 회차당 100문항 (과목별 20문항), 2022년은 80문항

> ⚠️ **2022년에 출제 체계가 전면 개편되어 과목명 자체가 교체되었다.** 과목이 하나 빠진 게 아니라 체계가 바뀐 것이므로, 연도별로 다른 과목표를 써야 한다. PDF 원본의 `N과목 : 과목명` 표시로 확인 가능.

| 체계 | 연도 | 과목 (번호 범위) | 문항 |
|------|------|------------------|------|
| 구 | 2012~2021 | 환경생태학개론(1~20) · 환경계획학(21~40) · 생태복원공학(41~60) · 경관생태학(61~80) · 자연환경관계법규(81~100) | 3,000 |
| 신 | 2022~ | 생태환경조사분석(1~20) · 생태복원계획(21~40) · 생태복원설계·시공(41~60) · 생태복원 사후관리·평가(61~80) | 160 |

`GisaSubject`에는 **9개 과목이 모두 등록**되어 있다(구5 + 신4). `parse_eco.py`의 `subject_of(num, year)`가 `SUBJECT_REFORM_YEAR=2022` 기준으로 표를 갈라 쓴다.

> 과거에 이 개편을 놓쳐 2022년 61~80번(법규·사후관리 문제)이 '경관생태학'으로 잘못 배정된 적이 있다. 연도별 과목표 분리로 수정 완료.
- 이미지 **340개** (수식·그래프·[보기]박스) — 306문항이 이미지 포함
- AI 해설: 전체 Gemini 해설 생성 완료 (gemini-3-flash-preview)

> ⚠️ **로컬 pk=6, 서버 pk=3**으로 다릅니다. 이미지 경로는 로컬 기준 `c6/`으로 생성돼 서버에도 `c6/`로 배포됐습니다(정상 동작). 서버에서 신규 문항을 추가하면 `c3/`로 생성되지만 파일명이 `eco*`로 고유해 충돌 위험은 없습니다.

### 데이터 원본 및 파싱

comcbt.com PDF (`data/comcbt/자연생태복원기사YYYY-R.pdf`, 32개). **텍스트 레이어가 있어 자동 파싱 가능** (조경기사의 스캔 PDF와 다름).

```bash
python parse_eco.py                 # 전체 32회차 파싱
python parse_eco.py 2012-1          # 특정 회차만
python manage.py import_eco_questions          # 파싱 결과 → DB
python manage.py import_eco_questions --dry-run
```

**`parse_eco.py` 핵심 로직** (다른 comcbt PDF에도 재사용 가능):

| 처리 | 방법 |
|------|------|
| 과목 판정 | 문항번호 범위(1~20, 21~40…)로 결정. `N과목 : 과목명` 표시는 해당 과목 **마지막 페이지 하단**에 나와서 신뢰 불가 |
| 정답표 | 마지막 페이지에 번호 10개 → 정답(①~④) 10개 블록 반복 |
| 광고 제거 | `종이 문제집`/`실제 시험에서 사용하는`/`PC 버전` 중 하나를 만나면 **그 줄부터 이후 전부 폐기** (개별 줄 필터링은 정상 문항을 오탐) |
| 이미지 추출 | PDF 내 이미지 객체를 좌표로 문항에 매칭 후 3배 확대 렌더링 |

**이미지 매칭에서 반드시 지켜야 할 3가지** (실제로 버그가 났던 지점):

1. **2×2 격자 배치** — 보기가 좌우 2열로 놓이는 문항이 있어, y좌표만으로 정렬하면 ①②가 뒤바뀐다. **y로 행 클러스터링(tolerance 15pt) 후 행 안에서 x 오름차순** 정렬해야 한다.
2. **컬럼/페이지 넘김** — 좌측 단 마지막 문항의 보기가 우측 단 상단에, 또는 다음 페이지 상단에 이어지는 경우. 해당 컬럼 위에 문항번호가 없으면 직전 컬럼/페이지의 마지막 문항으로 귀속시킨다.
3. **이미지 개수별 매핑** — 5개 이상이면 **뒤 4개를 보기 ①~④**로, 앞의 여분은 지문 그림(`text_image`). 보기 텍스트가 있는데 그림이 4개면 각 보기의 부속 그림이므로 보기에 배정.

### AI 해설 생성

```bash
python generate_eco_explanations.py            # 회차×과목 단위 40개 병렬
python generate_eco_explanations.py --force    # 덮어쓰기
python generate_eco_explanations.py --year 2012
```

- 회차·과목 목록을 **DB에서 자동 조회**하므로 2022년 4과목 개편이 자동 반영됨
- `WORKERS=40`, `DELAY=0.5`, `MODEL=gemini-3-flash-preview`
- 이미지 문항은 `get_image_parts()`가 멀티모달로 이미지를 함께 전송 (실측: 텍스트 문항 입력 ~250토큰 vs 이미지 문항 ~4,550토큰)

### 배포

```bash
# 로컬: 문항+해설+이미지 추출
python deploy_eco.py export     # → _deploy_eco.json(5.7MB) + _deploy_eco_images.zip(4.3MB)

# git push 후 서버에서
python deploy_eco.py load       # 이미지 압축해제 + DB 적재
```

### 쪽집게 노트

| 과목 | 상태 | 분량 | 커버리지 |
|------|------|------|----------|
| 환경생태학개론 | ✅ 완성 | 144,468자 / 2,380줄 (12장+부록) | **600/600 (100%)** |
| 환경계획학 | 미작성 | | |
| 생태복원공학 | 미작성 | | |
| 경관생태학 | 미작성 | | |
| 자연환경관계법규 | 미작성 | | |
| 생태환경조사분석 (신) | 미작성 | | 2022~ 신 체계, 각 40문항 |
| 생태복원계획 (신) | 미작성 | | |
| 생태복원설계·시공 (신) | 미작성 | | |
| 생태복원 사후관리·평가 (신) | 미작성 | | |

> 신 체계 4과목은 각 40문항뿐이라 단독 노트보다는, 구 체계 노트를 학습한 뒤 2022년 기출로 보완하는 편이 효율적이다. 실제로 2012~2021 기출을 학습하면 2022-1의 **77.5%(62/80문항)** 가 동일·유사 문항으로 커버된다(유사도 분석 결과).

```bash
python load_eco_textbook.py 환경생태학개론 env --dry   # 병합+검증만
python load_eco_textbook.py 환경생태학개론 env         # DB 저장 + 배포용 md 생성
python load_eco_textbook_deploy.py                     # 서버에서 적재
```

`load_eco_textbook.py`가 **구조 점검(장/절/항/키워드표 개수)과 커버리지 검증(노트 ref vs DB 실제 문항)** 을 함께 수행한다. 존재하지 않는 ref도 검출한다.

**노트 생성 작업 패턴** (조경기사와 동일):
1. DB에서 과목 문항을 `[YYYY-R-N] 문제 / *정답보기` 형식 텍스트로 추출
2. 12장을 3장씩 4묶음으로 나눠 **병렬 에이전트 4개**에 배정. 각 에이전트가 **640문항 전문을 정독**한 뒤 담당 장 작성
3. 병합 → 커버리지 검증 → 미연결 문항은 **부록**으로 흡수해 100% 달성

> 절 바로 아래에 도입 문단 없이 `####` 항으로 들어가면 절의 `content_html`이 비지만 정상이다. 기존 노트도 동일(조경관리론 55%, 식물병리학 54%가 그런 절). 하위 항까지 없는 진짜 빈 절이 0개인지만 확인하면 된다.

## 산업기사 쪽집게 노트 현황

식물보호산업기사(pk=2)의 쪽집게 노트 4과목 완성:
- 식물병리학 (pk=6)
- 해충학 (pk=7)
- 농약학 (pk=8)
- 잡초방제학 (pk=9)

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

조경기사 강의 영상의 srt 자막을 자연스러운 워드 문서(.docx)로 변환하는 작업 패턴.

### ★ 절대 원칙: "워드 생성 전에 모든 처리를 텍스트 단계에서 완료한다"

**워드 파일에 들어간 뒤 수정하지 말 것.** 워드(.docx) 파일은 한 번 만들면 수정이 매우 비효율적이다:
- run 경계 문제로 단어 치환이 자주 누락됨
- 사용자가 워드를 열어두면 PermissionError로 저장 실패
- 한자 병기 시 볼드/스타일이 깨짐
- 그림이 들어간 워드는 더 위험 (재생성하면 그림 손실)
- 한 건씩 발견하면 한 건씩 수정하는 패턴이 반복되며 시간 낭비

**올바른 흐름:**

1. **참고서 정독** — 해당 단원(예: 한국 조경사 p.164~171)을 직접 처음부터 끝까지 정독해 한자·표기·용어를 파악. fuzzy matching이나 자동 검출만 의존하지 말고, 사람이 읽듯 직접 이해
2. **자막 정독** — srt 자막 전체를 처음부터 끝까지 직접 읽어 STT 오타 후보·일본어 음독·강의 흐름 파악
3. **교정·한자·볼드 사전을 한 번에 작성** — 두 텍스트 비교로 모든 항목을 한 사전에 모음
4. **텍스트 단계에서 모두 적용** — srt → 구두점 부여 → STT 오타 교정 → 한자 병기 → 볼드 적용 → 단락 분할
5. **마지막에 한 번만 워드 생성** — 모든 처리가 끝난 텍스트로 docx를 한 번만 작성

### 입력 파일 위치

- 자막: `C:\Users\gocom\Downloads\WORK\output\<강의명>\<강의명>.srt`
- 강의 스틸컷(영상 캡처): `<강의명>.pptx` — 자막당 1슬라이드 1:1 대응 (텍스트 강의록에선 사용하지 않음)
- 참고서 OCR 텍스트: `N:\개인\조경기사\pdf\조경사_텍스트.txt` — **단원별 정독 필수**
- 조경기사 용어사전: `C:\Users\gocom\Downloads\WORK\조경기사_용어사전.txt` (보조 자료)
- 출력 파일: `<강의명> 강의록.docx` (같은 폴더에 저장)

### 처리 단계 (순서 엄수)

**Step 1. 참고서 정독 (Read 도구로 직접 읽기)**
- 해당 단원의 시작·끝 줄 번호를 grep으로 찾고 Read 도구로 통째로 읽음
- 한자 표기, 인물·정원·책·식물 등 핵심 용어를 메모
- fuzzy matching이나 어휘 빈도 분석에 의존하지 말 것 — 사람이 읽듯 이해해야 정확

**Step 2. 자막 정독 (Read 도구로 직접 읽기)**
- srt 전체를 800줄씩 나눠 끝까지 읽음
- 일본어 음독, STT 오타, 강사가 풀어 설명한 부분 식별

**Step 3. 텍스트 단계 일괄 처리 스크립트 작성**

한 파이썬 스크립트에서 모든 처리를 순서대로 수행:

```python
# 1) srt 파싱: 시간 제거, 텍스트만 결합
# 2) STT 오타 교정: 직접 정독해서 발견한 사례를 사전에 등록
# 3) 종결 어미 기준 마침표/물음표 부여
# 4) 접속 부사·연결 어미 뒤 쉼표 부여
# 5) 한자 병기 사전을 길이순 정렬, "처음 등장 시 1회만" 한자 추가
# 6) 문장 분할 → 5문장씩 단락 묶음
# 7) 볼드 토큰화: 한자 병기 형태("term(漢字)") 포함
# 8) python-docx로 워드 생성 (그림 없음, 텍스트만)
```

**Step 4. 한 번만 실행 → 검증 → 끝**
- 실행 후 사용자에게 "여기 이상하다"는 지적이 들어오면, 그 항목을 명시적 교정 사전에 추가하고 처음부터 다시 한 번만 재생성
- 워드를 열어 직접 수정하지 말 것

### 한자 병기 원칙

- **참고서에 한자가 명시된 용어만** 병기. 임의로 한자를 추측해 붙이지 말 것
- 자막에 처음 등장하는 곳에 단 한 번만 한자 추가: `term` → `term(漢字)`
- 길이순 정렬로 긴 용어 먼저 매칭 (예: "방지원도" 먼저, "방지" 나중)
- 한 번 한자가 붙은 용어는 다시 처리하지 않도록 처리 완료 set 관리

### STT 오타 자동 교정 원칙

자막 STT가 잘못 받아쓴 표기를 참고 텍스트와 대조해 자동 검출/교정한다.

- **검증 절차**: 교정 후보(`wrong → right`) 적용 전 참고 텍스트에 `right` 표기가 정확히 존재하는지 확인
- **safe-list 기반**: 명백한 인명·정원명·책 이름의 오타만 치환. 강사가 자연스럽게 쓰는 일반 어휘(예: "디딤돌", "호남지방")는 정상 한국어이므로 보존
- **fuzzy matching**: `difflib.SequenceMatcher`로 stem 유사도 0.6~1.0 사이 + 1~2글자 차이만 의심 후보로 등록
- **run 경계 처리**: docx의 run이 단어 중간에서 분리될 수 있으므로, 단일 run 안 검색 → 인접 run 합쳐 검색 순서로 치환

### 일본어 표기 → 한자 한국어 음독 통일

조경 시험은 한자 한국어 음독 표기를 사용하므로 일본 정원·인물명을 시험 표기로 통일한다.

| 자막(일본어 음독) | 시험 표기(한자) |
|---|---|
| 후시미성 | 복견성 |
| 쥬라쿠다이 | 취락제 |
| 니조성 | 이조성 |
| 가쓰라리큐(가쓰라 이궁) | 계리궁 |
| 신주쿠교엔 | 신주쿠어원 |
| 아카사카이궁 | 적판이궁 |
| 히비야공원 | 일비곡공원 |
| 도다이지 | 동대사 |
| 와카쿠사산 | 약초산 |
| 센노리큐 | 천리휴 |
| 고보리엔슈 | 소굴원주 |
| 이스이엔 | 의수원 |
| 신쥬안 | 진주암 |
| 료안지 | 용안사 |
| 다이안 | 대암 |
| 후신안 | 불심암 |
| 코호안 | 고봉암 |
| 후루타 오리베 | 고전직부 |
| 기타무라 엔킨사이 | 북촌원금재 |
| 다이쇼시대 | 대정시대 |

### 자막 STT 오타 사례 (모모야마~메이지 강의 기준)

참고 텍스트와 대조해 검출된 실제 STT 오타:

| 자막 STT | 참고 텍스트(정답) |
|---|---|
| 풍해 씻긴 | 풍우에 씻긴 |
| 디딤돌이나 포석 | 뜀돌이나 포석 |
| 북촌원금제 | 북촌원금재 |
| 제국다정명석도회 | 제국다정명적도회 |
| 삼도일련 | 삼도일연 |
| 동해일련 | 동해일연 |
| 삼신산도 | 삼신선도 |
| 문진사자림 | 문원사자림 |
| 마른 소나무는 뒤를 따라 지표를 표현했고 | 마른 소나무잎을 깔아 지피를 표현했고 |
| 신쥬안 | 진주암 |
| 료안지 | 용안사 |
| 절석 직선 | 절석직선 |
| 축산정조전 후편 | 축산정조전후편 |

### STT 오타 자동 검출의 3단계 전략

자막 STT 오타는 형태에 따라 검출 난이도가 다르므로 다음 3단계로 접근한다.

**1단계: 단어 단위 fuzzy match (가장 쉬움)**
- 1~2글자만 다른 케이스 (예: 북촌원금제↔북촌원금재, 삼도일련↔삼도일연)
- `difflib.SequenceMatcher` ratio 0.6~0.92 + 1~2글자 차이로 검출
- 강사의 일반 어휘는 노이즈가 많으므로 `safe-list` 적용 필수

**2단계: 문장 단위 fuzzy match (중간)**
- 어절 일부가 바뀐 케이스 (예: "지천회유식 정원이다" ↔ "지천회유식 정원")
- 참고서에서 5~25자 구절을 추출해 docx의 비슷한 길이 구절과 비교
- 대부분은 강사가 자연스럽게 풀어 설명한 정상 문장이므로, 자동 치환 위험. 후보만 보고하고 사용자 확인 필요

**3단계: 단어가 거의 다 바뀐 케이스 (가장 어려움)**
- 예: "마른 소나무잎을 깔아 지피 표현" → "마른 소나무는 뒤를 따라 지표를 표현"
- 단어 fuzzy로도 0.6 미만, 문장 fuzzy도 길이 차이로 놓침
- **앵커 기반 검출**: 같은 문장에 등장하는 고정 키워드(예: "석탑이나 석등으로 고찰의 분위기")를 앵커로 잡고, 앵커 주변의 다른 표현이 참고서와 다르면 의심
- 결국 사용자의 명시적 지적이 가장 정확. 사용자가 알려준 케이스는 즉시 반영하고 CLAUDE.md에 사례로 누적

### 새 강의록 작업 시 권장 흐름

**[추천] 텍스트 단계 일괄 처리 흐름** (사전 작업 완료 후 워드는 한 번만 생성):

1. 참고서 해당 단원을 Read 도구로 직접 정독
2. srt 자막을 Read 도구로 끝까지 정독
3. 두 텍스트를 비교해 STT 오타·일본어 음독·한자 병기 대상을 한 사전에 모음
4. 한 파이썬 스크립트에서 순차 처리: srt 파싱 → 구두점 → STT 교정 → 한자 병기 → 볼드 → docx 생성
5. **사용자 검토 후 추가 교정 필요하면 사전에 항목 추가하고 스크립트 재실행** (워드 직접 편집 금지)
6. 누적된 사례를 CLAUDE.md `STT 오타 사례` 및 `일본어 → 한자 음독 매핑` 표에 추가

### 한국 조경사 핵심 한자 병기 표 (16번 강의에서 누적)

다음 강의(한국 조경사 시대별)에서도 그대로 활용 가능:

| 분류 | 한글 | 한자 |
|---|---|---|
| 사상 | 신선사상 | 神仙思想 |
| 사상 | 음양오행사상 | 陰陽五行思想 |
| 사상 | 풍수지리사상 | 風水地理思想 |
| 사상 | 유교사상 | 儒敎思想 |
| 사상 | 은일사상 | 隱逸思想 |
| 사상 | 노장사상 | 老莊思想 |
| 사상 | 도참사상 | 圖讖思想 |
| 핵심 | 천원지방 | 天圓地方 |
| 핵심 | 비보 | 裨補 |
| 핵심 | 배산임수 | 背山臨水 |
| 양식 | 방지원도 | 方池圓島 |
| 양식 | 방지방도 | 方池方島 |
| 양식 | 자연풍경식 | 自然風景式 |
| 양식 | 축경식 | 縮景式 |
| 요소 | 석가산 | 石假山 |
| 요소 | 축산 | 築山 |
| 요소 | 가산 | 假山 |
| 요소 | 조산 | 造山 |
| 요소 | 괴석 | 怪石 |
| 요소 | 경석 | 景石 |
| 식물 | 사절우 | 四節友(梅松菊竹) |
| 식물 | 사군자 | 四君子(梅蘭菊竹) |
| 식물 | 세한삼우 | 歲寒三友(松竹梅) |
| 인물 | 주돈이 | 周敦頤 |
| 인물 | 도연명 | 陶淵明 |
| 인물 | 강희맹 | 姜希孟 |
| 인물 | 정약용 | 丁若鏞 |
| 책 | 산림경제 | 山林經濟 |
| 책 | 경국대전 | 經國大典 |
| 책 | 지봉유설 | 芝峯類說 |
| 책 | 애련설 | 愛蓮說 |
| 정원 | 안압지 | 雁鴨池 |
| 정원 | 포석정 | 鮑石亭 |
| 정원 | 소쇄원 | 瀟灑園 |
| 정원 | 다산초당 | 茶山草堂 |

(전체 매핑은 16번 강의록 생성 스크립트의 `HANJA` 사전 참조)

### docx 생성 시 주의사항

- **외부 API 사용 금지**: 자막 텍스트 분석·구두점 부여·오타 교정은 모두 규칙 기반(정규식 + 사전 매칭)으로 직접 처리. Gemini 등 외부 API 호출 금지
- **스타일 손실 방지**: 단락 전체 텍스트 치환보다 run 단위 치환 선호. run 경계에 걸친 표현은 인접 run을 합쳐 첫 run에 새 텍스트 + 나머지는 빈 문자열로 처리
- **워드 파일 잠금**: 사용자가 워드를 열어둔 상태에서 저장하면 `PermissionError` 발생. 처리 전 닫혀있는지 확인하고 안 되면 사용자에게 안내
- **인코딩**: 한글 출력 시 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")`로 강제. Windows 콘솔에서 한글 깨짐 방지

### 워드 문서 스타일 규칙

- 폰트: 맑은 고딕 11pt
- 줄간격: 1.6
- 단락 첫 줄 들여쓰기: 0.7cm
- 단락 후 간격: 6pt
- 페이지 여백: 좌우 2.5cm, 상하 2.0cm
- 제목: Heading 0 (가운데 정렬)
- 부제: 일반 단락 13pt 회색(#555)
- 볼드 색상: 다크그린(#1B4332)

## 과목/자격증 페이지 조회 추적

`subject_detail`(방송대) / `certification_detail`(기사) 페이지 진입을 추적해서 "어느 사용자가 어느 과목·탭을 몇 번 봤는지" 통계 산출.

### 모델

| 앱 | 모델 | 추적 대상 |
|---|---|---|
| main | `SubjectViewLog` | `/subjects/<pk>/?tab=<tab>` 진입 |
| gisa | `CertificationViewLog` | `/gisa/<cert_id>/?tab=<tab>` 진입 |

공통 필드: `subject/certification(FK) · user(FK) · tab(20자) · viewed_at · ip · user_agent(300자)`. 인덱스: `(viewed_at)`, `(user, viewed_at)`, `(대상, tab, viewed_at)`.

### 진입 기록 시점

- 두 뷰 모두 `active_tab = request.GET.get('tab', ...)` 직후 `try/except`로 `objects.create(...)` 호출. 로그 저장 실패해도 페이지 렌더링은 계속됨.
- 탭 값 예: 방송대 `notes/exam/wrong/history/latest`, 기사 `textbook/study/solve/mock/wrong/history/latest/glossary`
- `tab` 미지정 시 기본값: 방송대 `notes`, 기사 `textbook`

### "조회 vs 풀이"의 차이

- **조회(view log)**: 페이지 진입만 — 사용자가 문항을 펼쳐보지 않아도 카운트
- **풀이(Attempt)**: 답안 제출 시점에만 — 조회보다 훨씬 적음
- 자원식물학 사례(2026-06-07): 06-06 하루 `?tab=latest` 진입 44회·9 IP, 최신기출 풀이 0건 → "조회만 하고 풀이 안 함" 패턴이 일반적

### 통계 조회 패턴

```python
from django.db.models import Count
from main.models import SubjectViewLog

# 어제 과목·탭별 조회 TOP
SubjectViewLog.objects.filter(viewed_at__gte=yesterday, viewed_at__lt=today)\
    .values('subject__name', 'tab').annotate(c=Count('id')).order_by('-c')

# 특정 사용자가 본 최신기출 과목
SubjectViewLog.objects.filter(user=u, tab='latest')\
    .values('subject__name').annotate(c=Count('id')).order_by('-c')
```

### nginx access.log 기반 IP 통계는 불완전

- IP↔사용자 매핑 불가 + 모바일 IP 변경 + 14일 보존 한계
- `SubjectViewLog` 도입 이후로는 사용자별 정확 추적 가능

### 마이그레이션

- `main/0009_subjectviewlog.py`
- `gisa/0012_certificationviewlog.py`

## PDF 자료실 (main 앱)

방송대 과목별 PDF 학습 자료를 회원에게 제공. 다운로드는 차단하고 열람·인쇄만 허용하며, 모든 사용 이력을 워터마크와 함께 추적한다.

### 모델 구조

| 모델 | 설명 | 주요 필드 |
|------|------|-----------|
| `SubjectMaterial` | 과목별 PDF 자료 | subject(FK), title, file(FileField), uploaded_by, created_at |
| `MaterialOpenLog` | 열람·인쇄 기록 | material(FK), user(FK), action(view/print), opened_at, ip, user_agent |

- 업로드 경로: `materials/subject_<id>/<filename>`
- `MaterialOpenLog.action`: `'view'` (열람) / `'print'` (인쇄)
- 인덱스: `opened_at`, `(user, opened_at)`

### 다운로드 차단 4중 방어 (main/views.py)

| 계층 | 방어 수단 | 위치 |
|---|---|---|
| URL | 별도 다운로드 엔드포인트 없음. `material_stream`만 존재하며 inline 렌더링 전용 | `main/urls.py` |
| 응답 헤더 | `Content-Disposition: inline` (브라우저 다운로드 다이얼로그 차단) | `material_stream` |
| 응답 헤더 | `Accept-Ranges: none` + `Cache-Control: private, no-store` (Range 요청·캐시 차단) | `material_stream` |
| 렌더링 | PDF.js로 canvas에 그려서 원본 파일이 DOM에 노출 안 됨 + 우클릭/단축키 차단 + 워터마크 | `material_view.html` |

- `@xframe_options_sameorigin` 적용 (iframe 임베드는 동일 출처만 허용)
- 다운로드 시도 자체는 별도 로그 없음 (`material_stream` 호출은 PDF.js 정상 렌더링과 구분 불가)

### 워터마크

- **메인 워터마크**: "한울회 A+ 학습 시스템" + 사용자명·시각 (각 페이지 정중앙, -30도 회전)
- **위치**: 각 PDF 페이지(canvas) 위에 개별 배치, 용지 가운데 정렬 (`pdf-page-frame > pdf-watermark`)
- **투명도**: 메인 `rgba(0,0,0,0.08)`, 부제 `rgba(0,0,0,0.10)` (본문 가독성 우선, 2026-05-15 완화 적용)
- **인쇄 시**: canvas에 `ctx.fillText()`로 직접 합성하여 인쇄물에도 워터마크 영구 각인

### 열람·인쇄 추적

- **열람 로그**: `material_view` 뷰 진입 시 `MaterialOpenLog(action='view')` 저장
- **인쇄 로그**: 인쇄 버튼 클릭 → `material_print_log` API → `MaterialOpenLog(action='print')` 저장
- IP는 `HTTP_X_FORWARDED_FOR` 우선, User-Agent는 300자 truncate

### 사용자 입장에서의 "PDF 다운로드 이력" 해석

시스템에는 직접 다운로드 엔드포인트가 없으므로, **사용자가 PDF를 받아 본 행위 = `action='view'` 로그**가 곧 다운로드 이력으로 간주된다. 사용 현황 조회 시 열람·인쇄를 함께 보여줄 것.

### 통계 조회 패턴

```python
from main.models import MaterialOpenLog
from django.db.models import Count

# 사용자별 7일 사용량
rows = MaterialOpenLog.objects.filter(opened_at__gte=week_ago).values(
    'user__first_name','user__username','action'
).annotate(c=Count('id'))

# 자료별 7일 사용량
rows = MaterialOpenLog.objects.filter(opened_at__gte=week_ago).values(
    'material__title','material__subject__name','action'
).annotate(c=Count('id'))
```

## 회원 가입·승인 흐름 (accounts 앱)

가입 신청 → **관리자 승인** → 이메일 인증 → 활성화의 3단계 절차로 운영. 봇/스팸/원치 않는 가입을 사전 차단.

### 흐름

1. **사용자 가입 폼 제출** (`/accounts/signup/`)
2. **계정 생성**: `is_active=False, profile.is_approved=False`
3. **관리자 알림 메일** 발송 (gocompu21@gmail.com) + 사용자에게 "관리자 검토 후 인증 메일 발송" 안내 페이지 표시
4. 관리자가 `/manage/members/?tab=pending`에서 [승인] 또는 [거부]
   - **승인**: `profile.is_approved=True, approved_at, approved_by` 설정 + `EmailVerificationToken` 생성 + 인증 메일 발송
   - **거부**: `user.delete()` (즉시 삭제)
5. 사용자가 인증 메일 링크 클릭 → `verify_email` → `is_active=True` + 자동 로그인

→ **인증 메일은 관리자 승인 후에만** 사용자에게 발송된다. 봇이 가입 폼을 제출해도 관리자가 안 누르면 메일 전송 0.

### 모델 (`accounts/models.py`)

`UserProfile`에 승인 필드 3개:
- `is_approved` BooleanField (default=False)
- `approved_at` DateTimeField (null=True)
- `approved_by` ForeignKey → User (null=True, related_name='approved_signups')

### 관리자 알림 배지

- `accounts/context_processors.py`의 `pending_signup_count`가 글로벌 컨텍스트에 주입
- staff에게만 노출: `User.objects.filter(is_active=False, profile__is_approved=False).count()`
- `base.html` "관리" 메뉴 옆에 빨간 배지 `(N)` 표시 (count > 0일 때만)
- `config/settings.py`의 `TEMPLATES.OPTIONS.context_processors`에 등록

### 관리자 페이지 (`/manage/members/`)

상단 탭:
- [회원 목록 (N)] — 기본
- [승인 대기 (M)] — `?tab=pending` (M > 0이면 빨간 배경)

승인 대기 탭: 이름·아이디·이메일·가입일시·[승인][거부] 버튼

### URL/뷰

| URL | 뷰 | 메서드 | 동작 |
|---|---|---|---|
| `/manage/members/<pk>/approve/` | `member_approve` | POST | 승인 + 인증 메일 발송 |
| `/manage/members/<pk>/reject/` | `member_reject` | POST | 즉시 삭제 |

JSON 응답: `{ok: true, username, [warning]}` 또는 `{error}`

### 기존 비활성 회원 마이그레이션

`accounts/0006_approve_existing_active_users.py` — 이미 `is_active=True`인 사용자 전원을 자동으로 `is_approved=True`로 처리하는 RunPython 마이그레이션. 도입 전 회원 100명 보호.

### 자동 삭제 (`cleanup_unverified`)

- 기존: 24시간 미인증 → 삭제
- **변경**: **7일** 미승인·미인증 → 삭제 (`--days 7`)
- 관리자가 휴가 등으로 며칠 못 봐도 신청이 사라지지 않게 여유 시간 확보
- cron 일정도 동시에 조정 필요

### 가입 안내 페이지 (`signup_pending.html`)

"관리자 검토 후 승인되면 인증 메일이 발송됩니다" + 승인 절차 안내 박스 (보통 하루 이내, 7일 자동 취소 등)

## 사용자 활동 분석 쿼리 패턴

운영자가 "사용자 현황"·"비활성 회원"·"이중 가입 의심" 등을 조회할 때 사용하는 표준 쿼리 패턴. 명단 자체는 휘발성·개인정보라 CLAUDE.md에 저장하지 않고, **추출 방법만** 기록한다.

### 활성 사용자 판정 기준

사용자가 "활성"인지는 다음 세 모델 중 **어느 하나라도** 기록이 있으면 참:

```python
active_g = set(GisaAttempt.objects.values_list('user__username', flat=True).distinct())
active_e = set(ExamAttempt.objects.values_list('user__username', flat=True).distinct())
active_p = set(MaterialOpenLog.objects.values_list('user__username', flat=True).distinct())
active = active_g | active_e | active_p
```

- 풀이가 0건이어도 **PDF만 열람한 회원도 활성**으로 간주한다 (자료실만 활용하는 회원이 실제로 존재).
- `User.is_active=True`만 대상으로 한다 (24h 미인증 자동삭제 대상은 제외됨).

### 비활성 회원 카테고리 4분류

활용 안내 우선순위를 정할 때 다음 4분류로 본다:

| 카테고리 | 판정 | 의미 / 안내 우선순위 |
|---|---|---|
| 미로그인 | `last_login IS NULL` | 가입만 하고 한 번도 안 들어옴. **이메일 안내 1순위** |
| 가입일 당일 이탈 | `last_login == date_joined` 일자 | 첫 진입 후 길을 잃은 것 — 사용법 안내 필요 |
| 최근 로그인 + 활동 0건 | `last_login >= now-7d` AND 활동 없음 | 시스템 사용법이 막막한 케이스 — **개별 메시지 1순위** |
| 오래된 비활성 | 위 모두 아님 | 학습 흥미 잃음 — 안내 효과 낮음 |

### 이중 가입 의심 탐지

같은 사람이 다른 이메일로 두 번 가입한 케이스가 실제로 발견됨 (예: 김태헌 totalrank / xogjs987).

```python
from collections import Counter
names = User.objects.filter(is_active=True).values_list('first_name', flat=True)
dups = [n for n, c in Counter(names).items() if c > 1 and n]
# dups에 든 이름은 동명이인일 수도 있으므로 자동 병합·삭제 금지 — 운영자 수동 확인
```

- 동명이인이 실제로 존재할 수 있으므로 (예: 김상현 = 운영자 본인 + 학생) **이메일·가입일·활동량으로 교차 확인**한 뒤에만 처리.
- 운영자 본인 계정은 `root` (관리용) + `gocompu21` (학습용) 분리. 통계에서 `root`는 풀이 0건으로 빠지고 실제 학습은 `gocompu21`에서 잡힘.

### 사용자별 누적 활동 머지 패턴

기사·방송대·PDF를 한 dict로 머지하는 표준 코드:

```python
from django.db.models import Count, Q, Max
gisa_qs = GisaAttempt.objects.values('user__username','user__first_name').annotate(
    c=Count('id'), correct=Count('id', filter=Q(is_correct=True)), last=Max('created_at'))
exam_qs = ExamAttempt.objects.values('user__username','user__first_name').annotate(
    c=Count('id'), correct=Count('id', filter=Q(is_correct=True)), last=Max('created_at'))
pdf_qs = MaterialOpenLog.objects.values('user__username','user__first_name','action').annotate(
    c=Count('id'), last=Max('opened_at'))

merged = {}  # username → {name, gisa, gisa_correct, exam, exam_correct, pdf_v, pdf_p, last}
# 세 쿼리를 username 키로 머지하면서 last(=가장 최근 활동 시각)는 max로 갱신
```

### 박만우 케이스 — 학습모드(study) 정답률 0%

`GisaAttempt.mode='study'`(학습모드)는 채점이 없어 `is_correct=False`로 저장된다. 따라서 누적 정답률 0%로 보여도 **실력 부족이 아니라 모드 차이**다. 사용자 통계 해석 시 mode별로 나눠 봐야 한다:

```python
# 학습모드 제외한 실전 정답률
GisaAttempt.objects.filter(user=u).exclude(mode='study').aggregate(
    total=Count('id'), correct=Count('id', filter=Q(is_correct=True)))
```

- `mode` 값: `exam` (기출고사) / `mock` (모의고사) / `wrong_retry` (오답 재풀이) / `study` (학습모드)
- 학습모드만 사용하는 회원에게는 "이제 기출고사·모의고사로 실력 점검 단계 추천" 안내가 적절.

### 저장 금지 사항

다음은 CLAUDE.md에 절대 저장하지 않는다:
- 사용자 명단 (이름·이메일·username) — 개인정보 + 매일 변동
- 사용자별 풀이 건수·정답률 스냅샷 — DB가 항상 정답이므로 코드 저장소에 두면 즉시 stale
- 활동 로그 / 누가 무엇을 했나 — `git log`나 DB 쿼리로 항상 재생성 가능

저장 가치가 있는 건 **분석 방법론과 판정 기준**뿐.

## 모의고사 세대(Round) 시스템 (gisa)

같은 라운드 내에서 모의고사 출제 시 중복 문제를 피하고, 풀이 풀이 사이클을 라운드(R) 단위로 추적한다.

### MockGeneration 모델 (gisa/models.py)

| 필드 | 설명 |
|------|------|
| `user` | FK → User |
| `subject` | FK → GisaSubject (과목 단위 추적) |
| `generation` | IntegerField, 현재 라운드 (기본 1) |
| `seen_question_ids` | JSONField (List[int]), 이번 라운드에 출제·응답된 문제 ID |
| `updated_at` | DateTimeField (auto_now) |

- `unique_together = [('user', 'subject')]` — **자격증이 아닌 과목 단위**로 라운드 관리
- 한 과목만 집중 응시해도 다른 과목 신선도(R 진행도)에 영향 없음
- 마이그레이션: `0010_mockgeneration` (자격증 단위 생성) → `0011_reset_mock_generation_to_subject` (과목 단위로 변환, RunPython으로 기존 데이터 삭제 후 필드 변경)

### 누적 시점: 답안 선택 즉시 (AJAX)

문제 출제 시점도 제출 시점도 아니라, **사용자가 답안을 선택하는 즉시** 해당 문제 ID를 누적한다.

- API: `POST /gisa/<cert_id>/mock/mark-answered/` → `mock_mark_answered` 뷰
- 트리거: `selectAnswer()`, `selectBubble()` 함수 내에서 `markAnsweredOnce(qid)` 호출
- 중복 방지: 프론트엔드의 `_markedQids` Set으로 한 문제당 1회만 fetch POST
- 응답: `{ok: true, seen: N, generation: G}`

### 풀 소진 시 자동 라운드 +1

- 출제 시점(`mock_exam_take`)에 unseen 문제 수가 `min(20, total_pool)`보다 적으면 generation 즉시 +1 + seen 리셋
- 헤더에 `🎉 새 라운드!` 배지 1회 표시 (`gen_reset_just_now` 컨텍스트)
- 제출 시점(`mock_exam_submit`)에도 보강 누적 (미응답 `selected='0'` 제외, 중복 저장 방지)

### 라운드 표시 UI

| 위치 | 형식 | 비고 |
|------|------|------|
| `mock_exam_take.html` exam-top-header | `· R{N}` 또는 `· R{N}+` | 다중 과목 응시 시 `+` 접미사 |
| `mock_exam_take.html` mobile-header | `모의고사 · R{N}` | 단일/다중 동일 표기 규칙 |
| `certification_detail.html` 모의고사 탭 카드 | `R{N} (완주 K회)` | K = generation - 1 |
| `certification_detail.html` 과목별 모의고사 버튼 | `R{N} · {%}` 미니 배지 | 진행률 표시 |

- 헤더 텍스트에서 과목명 제거 (`R1` 형식, "조경관리론 세대 1" 같은 장황한 표현 금지)
- 색상: 노란색(`#ffc107`) 강조

### 자격증 상세 모의고사 탭 진행도 통계 (?tab=mock)

`certification_detail` 뷰에 `mock_stats` 컨텍스트 추가. 로그인 사용자에게만 표시.

```python
mock_stats = []
if request.user.is_authenticated:
    gen_map = {g.subject_id: g for g in MockGeneration.objects.filter(
        user=request.user, subject__certification=cert)}
    for subj in subjects:
        total_pool = GisaQuestion.objects.filter(
            exam__certification=cert, subject=subj
        ).exclude(exam__exam_type="최신").count()
        g = gen_map.get(subj.pk)
        seen = len(g.seen_question_ids or []) if g else 0
        gen = g.generation if g else 1
        pct = round(seen / total_pool * 100, 1) if total_pool else 0
        mock_stats.append({
            "subject_id": subj.pk, "order": subj.order, "name": subj.name,
            "round": gen, "seen": seen, "total": total_pool, "pct": pct,
            "rounds_completed": gen - 1,
        })
```

UI 구성:
- 모의고사 탭 상단: 카드 그리드 (`grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))`)
- 카드 내용: 과목명, `R{N} (완주 K회)`, 진행률 바, `{seen} / {total}문제 · {pct}%`
- 과목별 모의고사 버튼: `R{N} · {pct}%` 미니 배지 추가

### 채점 후 "새 모의고사" 버튼: 같은 과목 유지

`mock_exam_result` 뷰에 `next_mock_url` 컨텍스트 추가:
- 단일 과목 응시 시 `?subject=<id>` 쿼리 파라미터 유지
- 다중 과목/전체 응시 시 `/gisa/<cert>/mock/`로 이동
- `exam_result.html` 모바일 헤더 + PC 액션 영역 2곳에 적용

### 미응답 제외 규칙

`mock_exam_submit`에서 `selected != '0'`인 문제만 누적:
- 사용자가 페이지를 열기만 하고 안 풀었을 때 풀 소진 가속화 방지
- 답안 선택 즉시 누적(`mock_mark_answered`)되므로 제출 단계 보강은 누락 케이스 대응용

### 관련 URL

```python
path("<int:cert_id>/mock/mark-answered/", views.mock_mark_answered, name="mock_mark_answered"),
```

### 운영 주의사항

- MockGeneration 데이터는 사용자 학습 이력의 일부이므로 함부로 삭제하지 말 것
- 누적이 부정확해 보일 때(예: "2회 응시인데 120개 누적") 출제 시점 누적 → 답안 선택 시점 누적으로 이미 수정 완료
- 풀 소진 판정은 `len(unseen) < min(20, total_pool)` 기준 (정확히 20문제 남았을 때는 마지막 라운드 완주 가능)
