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
python manage.py generate_explanations --model gemini-2.5-flash
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
- 8,940문제 전체 해설 생성 완료 (gemini-2.5-flash 사용)

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

- `templates/main/index.html`: 한울회 A+ 학습시스템 홈페이지
- `templates/base.html`: 공통 레이아웃
- `templates/exam/study_mode.html`: 학습모드 (기출 풀이 + 채점)
- `main/views.py`, `main/urls.py`: 홈 라우팅
- `exam/views.py`, `exam/urls.py`: 시험/문제 관련 뷰

## 주요 파일 구조

```
knou_agriculture/
├── config/             # Django 설정
├── main/               # 메인 앱 (Subject 모델, 홈)
├── exam/               # 시험 앱
│   ├── models.py       # Exam, Question, Attempt 모델
│   ├── views.py        # 학습모드, 관리 뷰
│   └── management/commands/
│       ├── import_questions.py       # 엑셀 → DB import
│       └── generate_explanations.py  # Gemini 해설 생성
├── accounts/           # 회원 관리 앱
├── templates/          # HTML 템플릿
├── scrape_exam.py      # 개별 과목 스크래핑
├── scrape_all.py       # 전체 과목 일괄 스크래핑
├── generate_all.py     # 전체 과목 병렬 해설 생성
└── data/               # 엑셀 파일 (gitignore)
```

## 알려진 주의사항

- 올에이클래스 HTML에는 "중복답안 가이드" 범례 테이블이 답안표 앞에 존재함. 정답 파싱 시 반드시 `allaAnswerTableDiv` 영역 내에서만 추출해야 함 (범례의 A~K 코드가 정답으로 오인될 수 있음)
- 동명 과목(글쓰기 등)이 여러 학년에 존재하므로 `--grade` 옵션으로 구분 필요
- `Question.answer`는 CharField이며 `'1,2'` 형태의 문자열로 복수 정답을 표현함 (IntegerField 아님)
- 학습모드 JS에서 정답 비교 시 `split(',')` + `indexOf`로 처리 (parseInt 사용 금지)
