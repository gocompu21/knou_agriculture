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

### 잡초 동정 퀴즈 (방송대 subject_detail ?tab=weeds)

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
  `api_note_questions?ref=YYYY-N` 재사용). '피'·'띠' 같은 **한 글자 이름은 앞뒤가 한글
  음절이 아닐 때만** 인정한다 — 그냥 `contains` 로 하면 '피해'·'피복' 에 다 걸린다.
  두 글자 이상은 그대로 찾는다('여뀌' 가 '여뀌바늘' 문항에 걸리는 것은 두고 본다).
  로컬 기준 123종 중 13종에 배지가 붙는다(올방개 4건이 최다)
- **출제 횟수 별**(`_wqStars`, `.wq-stars` 노란색): 5회↑ ★★★ / 3~4 ★★ / 2 ★ / 1 ☆,
  0회는 없음 — 실기 쪽집게 노트와 같은 기준이다. 답 화면 이름 옆과 목록 표 종명 옆에
  붙는다. 122종 중 30종만 출제 이력이 있다(★★★ 5 · ★★ 15 · ★ 3 · ☆ 7)
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
    - 썸네일이 84px 이라 무슨 사진인지 안 보인다. 돋보기(⊕)로 **크게 볼 수 있다**
      (`weedZoom`). 드래그와 겹치지 않게 버튼을 따로 두고 클릭을 멈춘다
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
  바꾼다(폭 520px 상한)
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

## 다른 자격증 (별도 문서)

각 자격증의 데이터 현황·구축 절차·주의사항은 별도 문서에 있다. 해당
자격증 작업을 할 때 열어 볼 것.

- **[docs/조경기사.md](docs/조경기사.md)** — pk=5, 3,360문항 6과목
  (2013~2022). 쪽집게 노트 6과목(합계 190만자), comcbt PDF 답안표로
  정답 검증해 146건 수정한 경위, Gemini Gems 파일 9개 목록, 교재 배포
  스크립트.
- **[docs/식물보호기사.md](docs/식물보호기사.md)** — 기사 pk=1(3,631문항
  5과목), 산업기사 pk=2(3,207문항 4과목). 텍스트 파일 import 형식,
  회차×과목 100개 병렬 해설 생성, 쪽집게 노트 마크다운 구조(식물병리학·
  농림해충학), 용어집 5,870개 생성 방법.


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
- AI 해설: 전체 Gemini 해설 생성 완료 (gemini-3-flash-preview)

> ⚠️ **로컬 pk=6, 서버 pk=3**으로 다릅니다. 이미지 경로는 로컬 기준 `c6/`으로 생성돼 서버에도 `c6/`로 배포됐습니다(정상 동작). 서버에서 신규 문항을 추가하면 `c3/`로 생성되지만 파일명이 `eco*`로 고유해 충돌 위험은 없습니다.

### 필기 데이터 구축 이력

2012~2025 필기 3,880문항을 만든 절차는 모두 끝났다. 상세는
**[docs/자연생태복원_필기구축.md](docs/자연생태복원_필기구축.md)** 참조 —
comcbt PDF 자동 파싱(`parse_eco.py`)과 이미지 매칭에서 지켜야 할 3가지,
2023~2025 스캔본 LLM 판독과 회차별 페이지 매핑, 정답표 오류 4건 정정 근거,
선지별 해설 보강이 필수인 이유(UI가 `explanation`을 안 쓴다), 배포 명령,
쪽집게 노트 9과목(176만자) 작성 패턴과 법 개정 병기 14항목.


## 실기 필답형 (자연생태복원기사)

주관식 실기 필답형을 **출제 → 답안 작성 → AI 채점 → 점수 조정**으로 학습하는 기능.
필기(객관식)와 완전히 분리된 모델·뷰·템플릿을 쓴다.

### 시험 정보 (Q-net 출제기준 2025.01.01~2027.12.31)

| 항목 | 내용 |
|------|------|
| 과목명 | 생태복원 전문실무 |
| 검정방법 | 복합형 = **필답형(1시간 30분, 45점) + 작업형(3시간, 55점)** |
| 합격기준 | 합계 **60점 이상** (개별 과락 없음) |
| 출제기준 | 주요항목 8 / 세부항목 36 / 세세항목 142 |

> 일부 자료의 "필답 2시간"은 과거 기준이다. 출제기준 원문이 1시간 30분으로 명시.
> 합계 합격이라 **필답 30점을 확보하면 작업형은 30/55만 받아도 합격**한다.
> 결과 화면이 이 환산값(`session.practical_estimate`)을 보여준다.

- 조사 정리: `_eco_practical_exam_research.md` (시험 구조·합격률·수험생 후기)
- 출제기준 구조화: `_eco_exam_standard_2025.json` / `.md` (생성: `parse_eco_standard.py`)
- 원본 PDF: `data/comcbt/자연생태복원기사_출제기준_2025-2027.pdf`

### 데이터 — 기출 726문항 (51회차)

2005~2026년 기출만 싣는다. 원본은 예문사 교재 PART 05 필답형 문제풀이편
스캔본(204쪽, **텍스트 레이어 없음**)과 블로그 복원본. LLM이 페이지 이미지를
직접 판독했다. 분석 결과는 `_eco_essay_pdf_analysis.md` 참조.

- **2023-2회, 2024-3회는 교재에 미수록**
- 이미지 72장 크롭 (`_eco_essay_parsed/images/`)
- 원문 오식은 `[box]` 지문 안의 것만 보존하고 `notes`에 기록. 발문의 명백한
  오식은 재서술 때 정정했다(아래 저작권 절 참조)

#### 예상문제 395건은 걷어냈다 (2026-09)

교재 저자가 출제기준을 보고 만든 문항이라 **저작권 부담이 가장 큰 부분**인데,
학습 값어치를 재 보니 낮아서 제거했다. 최근 7회차 96문항을 두 재료로 각각 맞혀 보면:

| 재료 | 적중 |
|------|------|
| 과거 기출 | 11% |
| 예상문제 395건 | **4%** |

2024년 두 회차는 적중 0건이었다. **예상문제에만 있는 고유 주제도 0개**라
(기출 주제 563개 중 89개와 겹칠 뿐), 기출과 겹치는 110건을 빼면 나머지는
언젠가 나올 수도 있는 영역일 뿐이다. 문항 수가 기출의 절반이 넘어 여기 시간을
쓰면 기출 회독이 밀린다.

```bash
python deploy_essay_drop_pred.py   # 서버에서 실행 (응시 기록 있으면 중단)
```

- 백업: `_essay_predicted_removed.json` (395건 전문)
- **코드는 그대로 두었다** — `source='예상'` 경로가 살아 있어 자체 제작 문항을
  넣으면 바로 동작한다. 목록의 영역 카드는 데이터가 없으면 통째로 감춰진다
- 지울 때 응시 기록이 0건임을 확인했다. 기록이 있으면 사용자 이력이 사라지므로
  배포 스크립트가 스스로 중단한다

```bash
python merge_eco_essay.py --crop          # 판독 배치 병합 + 검증 + 이미지 크롭
python manage.py import_essay_questions   # JSON → DB
python manage.py normalize_essay_points   # 기출 회차 배점을 45점으로 정규화
python manage.py classify_essay_std       # 출제기준 주요항목 자동 분류
```

**배점**: 교재에 배점 표기가 없어 유형별로 부여한다(계산·서술·표그림 4 / 열거 3 / 빈칸·단답 2).
기출은 `normalize_essay_points`가 회차 합계를 45점에 맞춘다(0.5점 단위 가감).

### 모델 (gisa/models.py)

| 모델 | 설명 | 핵심 필드 |
|------|------|-----------|
| `GisaEssayQuestion` | 필답 문항 | source(예상/기출), section, year, round, number, qtype, text, **answer_items(JSON)**, answer_text, reference, points, rubric, std_major |
| `GisaEssaySession` | 응시 세션 | mode(online/paper), status, paper_code, total_points, score |
| `GisaEssayAttempt` | 문항별 답안 | answer_text, transcribed_text, ai_score, **final_score**, feedback(JSON) |
| `GisaEssayUpload` | 시험지 사진 | page_no, image, transcribed |

- **답을 `answer_items`(리스트)로 저장하는 것이 핵심.** 교재 풀이가 이미 `①②③` 포인트
  단위라, 그대로 채점 기준표가 된다. 배점을 항목 수로 나눠 부분점수를 준다.
- **① 항목 수는 문제가 묻는 것의 수와 같아야 한다.** "정의와 특징을 서술하시오"면
  ① 정의 ② 특징. 특징을 ②③④로 쪼개면 답의 뼈대가 문제와 어긋난다. 한 항목 안의
  세부 열거는 ㉠㉡㉢ 으로 적는다. "N가지"를 묻는 열거형은 N개 항목이 맞다.
  (2026-09 정비: 무선추적법·비오톱 기능·극상 특징·파편화 저감방안 등 9문항)
- **한 가지만 묻는 서술형("X란 무엇인지 설명하시오")은 ①② 없이 문장으로 쓴다.**
  `answer_items` 는 문장 하나(줄바꿈으로 문장 구분), 채점 포인트는 `rubric` 에
  따로 둔다 — 화면은 문장, 채점은 포인트별 부분점수. (2026-09 정비 29문항, 백업
  `_essay_prose_backup.json`). 단순 라벨→"은/는" 기계 변환은 "결과는 …" 같은
  어색한 문장을 만들므로 직접 다시 써야 한다
- `answer_text`는 표·계산식처럼 항목으로 쪼갤 수 없는 답.
- `reference`(법조문·지침·배경 설명)는 **채점에 쓰지 않고** 학습 자료로만 노출.
  화면 라벨은 **「해설」** (2026-09 변경, 이전 "참고자료 (법조문·지침)").
- `final_score`가 있으면 그것이, 없으면 `ai_score`가 점수다(`attempt.score` 프로퍼티).

### 저작권 — 답·그림·문제문을 모두 다시 씀

원본이 예문사 교재라 **세 갈래를 전부** 손봤다. 하나라도 남기면 의미가 없다.

| 대상 | 처리 |
|------|------|
| 답 (`answer_items`·`answer_text`) | 전량 재서술 (Claude 직접, 외부 API 미사용) |
| 그림 65장 | 자작 SVG로 교체. **구도까지 바꿔야 한다** — 좌표만 옮기면 "거의 같다"는 지적을 받는다 |
| 문제문 (`text`) | 987건 재서술 (2026-09). 당시 1,121건 대상이었고 이후 예상문제 395건은 삭제 |
| 예상문제 395건 | 통째로 삭제 — 저작권 부담 대비 적중률 4% (위 참조) |

> 기출 문항 **번호는 바꾸지 않는다.** 회차별 번호는 교재의 편집이 아니라 국가시험
> 사실이고, 과거 응시 기록(`GisaEssayAttempt`가 `question__number`로 정렬)과
> 다른 수험 자료 대조가 걸려 있다.

**사실은 저작물이 아니다** — 법조문, 수치 기준, 분류 체계, 계산식은 그대로 둔다.
보호되는 것은 **표현과 도해의 구성**이다.

#### 문제문 재서술 강도 — "조사 정도만"

사용자 지시가 명확했다: *"너무 용어나 많이 고치지 말고, 조사 정도를 바꿔서 문장만"*.
수험자가 느끼는 문제는 완전히 같아야 한다.

| 바꾸는 것 | 그대로 두는 것 |
|-----------|----------------|
| 어미 `~하고자 한다`→`~하려고 한다`, `~일 경우`→`~라면` | 전문 용어 전부 (매토종자·비오톱·SLOSS…) |
| 조사 `중`→`가운데`, `~에 따른`→`~에 따라` | 수치·법령명(낫표 포함)·답 개수 지시 |
| 문장 끊기/잇기, 조건절 위치 | `[box]` 지문 내용, 마크다운 표 |
| 괄호 단서를 `(단, …)`로 분리 | 묻는 내용과 요구 사항 |

> 용어를 풀어 쓰면 안 된다. "매토종자"→"묻혀 있던 씨앗"은 **문제를 새로 쓴 것**이다.
> `SLOSS 논쟁에 대하여 설명하시오` 정도로 이미 최소인 문장은 `~이란 무엇인지`까지만.
> 억지로 못 바꾸겠으면 원문 유지가 정답이다 (실제 134건이 그랬다).

```bash
python dump_essay_text_rewrite.py            # 40건씩 29배치
# → 병렬 에이전트 6개가 batch_NN_done.json 저장 (배치마다 즉시 저장 필수)
python load_essay_textrw.py                  # 검증만
python load_essay_textrw.py --apply          # DB 반영 (_essay_text_backup.json 자동 백업)
python deploy_essay_text.py export / load    # 서버 배포
```

`load_essay_textrw.py`가 원문과 자동 대조해 **수치 누락·답 개수 지시 변경·법령명 소실·
`[box]`/표 구조 파손**을 잡아낸다. 하나라도 걸리면 그 건만 보류한다. 실제 987건 중 위반 0건.

> **자격증 pk가 로컬 6 / 서버 3으로 다르므로** 배포 스크립트는 pk가 아니라
> `(source, section, year, round, number)`로 문항을 찾는다.

#### 원문 오식은 이때 함께 잡는다

재서술하며 답과 대조하면 오식이 드러난다. 실제로 정정한 것:

| 오식 | 정정 | 근거 |
|------|------|------|
| `CFC` | `CEC` | 답이 Cation Exchange Capacity |
| `NH⁺` | `NH₄⁺` | 답 표기 |
| `옆면적 지수` | `엽면적 지수` | 답이 LAI 정의 |
| `IUCN LED LIST` | `IUCN 적색목록(Red List)` | — |
| `2,000본/m³` | `2,000본/m²` | 파종량이 g/m²라 면적 단위 |
| `100,0000m²` (2023-1 #6) | `100,000m²` | 모범답안이 100,000 기준으로 계산 |
| `등고선 10m와 110m` (2024-1 경사도) | `등고선 100m와 110m` | 모범답안이 표고차 10m(20%)로 계산. 사용자 확인 후 정정 |

**단, `[box]` 지문 안의 오식은 손대지 않는다** — 복원문제집이라 원문 보존이 우선이다.
확신이 없으면 그대로 두고 `notes`에 기록한다.

### 채점 엔진 (gisa/essay_grading.py)

유형에 따라 규칙과 LLM을 나눈다. **반환 형식은 동일**하다.

| 유형 | 엔진 | 방식 |
|------|------|------|
| 단답·빈칸 | `rule` | 정규화(공백·번호기호 제거) 후 부분 문자열 포함 여부. 애매하면 LLM으로 위임 |
| 계산 | `rule` → `llm-calc` | 최종 답 수치가 전부 맞으면 규칙으로 만점. 하나라도 어긋나면 계산 전용 LLM |
| 열거·서술·표그림 | `llm` | 채점 기준표의 포인트마다 "답안이 이 내용을 담았는가" 판정 |

**계산형이 까다롭다** — 교재 풀이가 계산 과정을 통째로 적어 두어 중간값(10,000 × 60% × 1.3
= 7,800 …)까지 정답 수치로 잡히면, 최종 답만 쓴 답안이 오답 처리된다.
`final_answer_numbers()`가 "② 답"·`∴` 표지 뒤를 우선해 최종 답만 뽑지만 완벽하지 않으므로,
**확실히 맞은 경우에만 규칙으로 끝내고 나머지는 LLM에 넘긴다**. 계산 전용 프롬프트는
배점의 70%를 답 정확성, 30%를 과정에 배분한다(답이 맞으면 과정을 생략해도 70%는 준다).

만점 보정: 균등 배분(4점 ÷ 3항목 = 1.33)에서 생기는 반올림 오차 때문에 전부 맞아도
3.99점이 나온다. 모든 포인트가 matched면 만점으로 올린다.

### 손글씨 사진 판독 (gisa/essay_ocr.py)

**판독과 채점을 반드시 분리한다.** 한 번에 시키면 오독인지 오답인지 구분할 수 없다.
판독 → 사용자 확인·수정 → 채점 순서다.

정확도를 올리는 두 장치:
1. **그 시험지의 문항 번호·문제문**을 함께 보낸다 → 문항 경계 판정에 결정적
2. **모범답안에서 뽑은 용어 목록**(회차당 ~130개)을 힌트로 준다 → 한글 받침 오독 감소
   `_collect_terms()`가 조사(`을/를/이/가/에서…`)를 떼고 명사만 남긴다.
   "매트이식", "톨훼스큐", "대체서식지" 같은 고유 용어가 잡히는 게 핵심.

프롬프트에 한글 자모 혼동쌍(ㄴ/ㄹ, ㅁ/ㅇ, ㅂ/ㅍ, ㅐ/ㅔ …)을 명시하고,
"목록에 없는 낱말을 목록의 낱말로 억지로 바꾸지 말 것"이라는 안전장치를 둔다.

> 답안은 한글이 주 언어이고 영문 약어(LID, HGM, GPP, IUCN)와 화학식이 섞인다.

### 사용 모델 (config/settings.py)

```python
GEMINI_ESSAY_GRADE_MODEL = 'gemini-3.7-flash'        # 채점 (최신 stable)
GEMINI_ESSAY_OCR_MODEL   = 'gemini-3.1-pro-preview'  # 손글씨 판독 (정확도 우선)
ESSAY_DAILY_GRADE_LIMIT  = 20   # 사용자당 하루 채점 횟수
ESSAY_DAILY_OCR_LIMIT    = 40   # 사용자당 하루 판독 장수
```

> 프로젝트의 기존 해설 생성은 `gemini-3-flash-preview`(preview)를 쓰지만, **신규 코드는
> stable을 쓴다** — preview 모델은 예고 없이 종료된다. 환경변수로 교체 가능.

### 화면 (templates/gisa/)

| URL | 뷰 | 템플릿 | 설명 |
|-----|-----|--------|------|
| `/gisa/<id>/essay/` | `essay_list` | `essay_list.html` | 회차 카드 + 영역 카드 + 응시 이력 |
| `/gisa/<id>/essay/take/` | `essay_take` | `essay_take.html` | 풀이 (온라인 입력 / 사진 업로드) |
| `/gisa/<id>/essay/<sid>/submit/` | `essay_submit` | — | 제출 → 채점 |
| `/gisa/<id>/essay/<sid>/result/` | `essay_result` | `essay_result.html` | 결과 + 포인트 대조 + 점수 조정 |
| `/gisa/<id>/essay/<sid>/sheet/` | `essay_sheet` | `essay_sheet.html` | **인쇄용 시험지** |
| `/gisa/<id>/essay/<sid>/upload/` | `essay_upload` | — (JSON) | 사진 업로드 → 판독 |
| `/gisa/<id>/essay/adjust/<aid>/` | `essay_adjust` | — (JSON) | 사용자 점수 조정 |
| `/gisa/<id>/essay/grade-one/<qid>/` | `essay_grade_one` | — (JSON) | 학습 모드 단건 즉시 채점 |

**필기와 실기는 목록에서부터 완전히 분리한다.** 자격증 목록(`/gisa/`)이 한 자격증을
`[필기]`·`[실기]` 두 카드로 나눠 보여주고, 실기 카드는 `essay_list`로 직행한다.
필기 상세(`certification_detail`)에는 실기 탭을 두지 않는다 — 시험 성격·채점 방식·
학습 흐름이 모두 달라 한 페이지에 섞으면 탭만 늘어나고 오히려 찾기 어렵다.

**실기 페이지(`essay_list`)는 필기 상세와 같은 7개 탭**이다 (`?tab=`, 기본 `textbook`).
탭 전환은 클라이언트에서 보이기만 바꾸고 주소를 갱신한다(내용은 전부 서버 렌더).

| 탭 | 내용 |
|----|------|
| `textbook` 쪽집게 노트 | **주제별 교재** (`gisa/essay_textbook.py` → `build_textbook`, 10분 캐시). 8개 분류(topic_group) pill → 주제(topic_key) 아코디언. 대상: 2회 이상 출제 + 계산 + 재출제 유력(약 193주제). 별 = 출제 회차 수(5회↑ ★★★ / 3~4 ★★ / 2 ★ / 1 ☆), 회차 배지(`note_badges`), 정리 자료(`freq58` 정의·이유·사례, `calc` 공식·대입·함정)를 대표 문항 → topic_key 로 이어 붙이고, 정리가 없으면 최근 문항+모범답안. 걸러 보기(★★★/계산/재출제/⚠️), 기출 문항 펼침(`siblings?all=1`) |
| `study` 기출학습 | 빈출(4·3·2회)·재출제 유력·계산 학습 + 회차별 학습(정답 보며) |
| `solve` 기출고사 | 회차별 풀기(90분)·시험지(인쇄→사진) |
| `mock` 모의고사 | `source='모의'` — 기출에서 topic_key 가 겹치지 않게 무작위(`_pick_mock`, 최근 연도 가중). **범위 지정**: `?yfrom=&yto=&g=1&g=8&n=15`(연도·분류·문항 수 5~30, `_mock_scope`). 범위는 세션 `section` 에 "모의 2020~2026 2분류 10문항"으로 남아 시험이력 라벨이 된다. 순번으로 표시 |
| `wrong` 오답노트 | `_wrong_attempts()` — 문항마다 **가장 최근 응시**로 판정, 만점 미달만. **답을 안 쓴 문항은 넣지 않는다**(안 푼 것과 틀린 것은 다르다). 다시 풀어 만점이면 빠진다. "오답 재풀이"는 `source='오답'`(최대 20문항, 타이머 없음) |
| `history` 시험이력 | 세션 표 (모의/오답 배지) |
| `qna` 질의응답 | 실기 질문 (`cert_subject='실기'`) |

- 쪽집게 노트 주제 제목은 **`gisa/essay_topic_titles.json` 이 최우선**이다(대표 문항의
  "연도-회차-번호" → 제목, 정리 자료 없는 135주제를 직접 지었다). 발문을 규칙으로
  잘라 만든 제목은 "토양은 입경에 따라 사토, 미사토…"처럼 문제의 부분집합이 되기
  쉬우니, 새 주제가 생기면 규칙에 맡기지 말고 이 파일에 **문제의 뜻**을 적어 넣는다
- 정리 자료의 **도해는 자작 SVG** 로 넣는다 — `add_essay_figures.py` (노트 항목의 절 끝에
  `<div class="q-svg" data-fig="키">`, 문항 해설에는 `[svg]…[/svg]`; 같은 키가 있으면 걷어내고
  다시 넣으므로 그림을 고쳐 다시 돌려도 된다). 폭 360px 안팎으로 작게 — 크면 부담스럽다.
  2026-09 현재 16개: 중규모 교란설 곡선, Bradshaw 도식, 생물권보전지역 동심원, 미티게이션
  3패널, 생태네트워크 모식도, 하천차수도, 클레멘츠 천이계열, 로지스틱 곡선(K), 단편화 5단계,
  SLOSS, 다차원 부피모형, 조류-인간 거리, 종-면적 곡선, 경성·연성 경계, 깔때기 효과, 생태통로 단면
- 58주제 정리의 「⚠️ 요구가 커진 지점」 절은 **발문이 실제로 달라진 주제에만** 둔다.
  배점·모범답안 구조만 근거로 "요구가 커졌다"고 쓴 8개 절(파편화 정의·리비히·
  개체군 생존율·r/K 분류·분포유형·환경수용력·거리효과·극상 특성)은 2026-09 에 뺐다
  (백업 `_essay_warn_removed.json`). 남은 30개는 호흡량 추가, 판정 기준, 빈칸형
  전환, 조건 추가처럼 문제가 바뀐 경우다
- 그 다음 순서(`_title_from`): 정리 자료 제목 > 발문(지시어 제거) 순.
  발문이 "다음에서 설명하는 것은"처럼 일반형이면 답의 첫 항목을, **빈칸 문항은
  문항 전체 맥락**(상자 문장, 없으면 발문 본문)의 괄호에 답을 채운 첫 문장을 쓴다
  (`_fill_blanks`). 답만 떼면 'ㄱ'·'경성' 같은 조각이 남는다
- 모의·오답 세션은 **만들 때 문항을 빈 답안 attempts 로 붙여 둔다**. 세션에 문항
  목록 필드가 없어, 이어 올 때(`?resume=`) 같은 세트를 되살릴 유일한 저장소다.
  하루 지나도 답이 하나도 없으면 목록 진입 시 지운다
- `essay_save` 는 임시저장이 아니라 **진행률 채점 1단계**라 status 를 `grading` 으로
  바꾼다. 임시저장은 `essay_draft`(`/essay/<sid>/draft/`) — 입력 2초 뒤 서버에
  attempts 로 묶어 저장하고, 화면을 떠날 때도 한 번 보낸다. 이어하기(`?resume=`)가
  이 초안을 textarea 에 채운다. localStorage 초안은 새로 고침 대비용으로 병행

- 실기 카드: 왼쪽 다크그린 띠 + `실기` 배지, "기출 N회차 · 문항 N개" 표기
- 실기 페이지 hero 우측에 `필기로 ›` 전환 링크
- 회차 수는 `(year, round)` 조합을 세야 한다. `Count('round', distinct=True)`는
  회차 번호(1·2·3)만 세어 10회차가 3으로 나온다. `values_list().distinct()`를 쓸 때는
  **`order_by()`로 `Meta.ordering`을 지워야** 한다(정렬 필드가 SELECT에 끼어들어
  중복 제거가 무력화된다)
- 기출은 90분 타이머 (예상문제 경로는 무제한 10문항씩이나 현재 데이터 없음)
- 답안은 `localStorage`에 자동 임시저장 (15문항 쓰다 날아가면 치명적)
- 결과 화면에서 **사용자가 점수를 직접 조정**할 수 있다(`final_score`). AI 오채점 보정용이며,
  `ai_score`와 따로 저장하므로 나중에 채점 품질을 점검할 수 있다.

### 시험지 인쇄 → 사진 제출 흐름

실기는 실제로 손글씨라 이 경로가 실전에 더 가깝다.

```
① 시험지 인쇄 (문항 + 답안 박스 + 시험지 코드)
② 볼펜으로 풀기
③ 페이지별 촬영 → 업로드
④ 판독 결과를 화면 textarea에 자동 채움
⑤ 사용자가 확인·수정
⑥ 제출 → 온라인 모드와 같은 채점 파이프라인
```

- **시험지 코드는 "연도-회차"(예: `2026-2`)로 고정**이다. 세션마다 다른 코드를
  주던 때는 먼저 인쇄한 시험지가 다음 세션에서 "다른 시험지"로 거부됐다. 시험지
  보안이 필요한 서비스가 아니므로 회차만 가린다. 판독기는 사진의 코드가
  연도-회차 꼴인데 다를 때만 거부하고, 안 읽히거나 다른 꼴이면 인쇄된 발문
  대조로 넘긴다(`_code_mismatch`)
- 코드는 모든 쪽 **바닥 가운데**에 찍힌다. `position:fixed` 글자 + `<tfoot>` 빈 칸
  조합이다 — fixed 만 쓰면 본문과 겹치고, `<tfoot>` 에 글자를 넣으면 마지막
  쪽에서 바닥까지 내려가지 않는다
- 답안 박스에 **굵은 테두리**를 두는 이유: 모델이 문항 경계를 찾는 데 결정적
- 박스 높이는 유형별로 다르다 (단답·빈칸 3줄 / 열거·표그림 6줄 / 서술·계산 8줄,
  줄 간격 32px). 화면의 시험지 모드·온라인 풀기도 같은 괘선 칸을 쓴다
- `@media print`로 A4 최적화(위 여백 18mm), `page-break-inside: avoid`로 문항 잘림 방지

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




## 노트 인포그래픽 생성 (OpenAI / Gemini)

쪽집게 노트 절에 넣는 인포그래픽을 만든다. 두 갈래가 있고 **OpenAI 쪽이 기본**이다.

| 스크립트 | 모델 | 장당 | 한글 | 쓰임 |
|----------|------|------|------|------|
| `gen_note_image_gpt.py` | `gpt-image-2.5-sunburst` | 약 $0.04 | 4장에 오타 1건 | **최종 생성** |
| `gen_note_image.py` | `gemini-3-pro-image-preview` | 약 $0.13 | 한 장에 오타 5건 | 구성 잡기 |

```bash
python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png
python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png --ref 고칠그림.png
python gen_note_image_gpt.py --prompt-file _p.txt --out _out.png --round 2   # _out_r2.png
```

- 인자는 Gemini 판과 같다. 다른 점은 `--aspect` 대신 **`--size`**(픽셀 크기).
  기본 `1536x1024`, 세로 `1024x1536`, 정사각 `1024x1024`. 커스텀은 16의 배수·비율 1:3~3:1
- `--quality` 는 `low`~`max` 6단계, 기본 `high`
- `--ref` 를 주면 그 그림을 고쳐 그린다(`images.edits`)
- 키는 `.env` 의 `OPENAI_API_KEY`. `settings.OPENAI_IMAGE_MODEL` 로 모델 교체 가능

### 만든 뒤 Claude 가 눈으로 검증한다

**생성으로 끝내지 말 것.** 만든 그림을 Read 로 열어 아래를 보고, 하나라도 걸리면
프롬프트를 고쳐 다시 만든다. 사람에게 "확인해 보세요"라고 넘기지 않는다.

| 보는 것 | 불합격 예 |
|---------|-----------|
| 한글 글자 | 없는 글자, 자모가 깨진 글자, 프롬프트와 다른 낱말 |
| 내용 중복 | 같은 항목이 두 칸에 나옴 |
| 사실 오류 | 배에 유근이 둘, 잎차례가 설명과 다름 — 학술 그림은 특히 |
| 빠진 항목 | 프롬프트에 적은 항목이 그림에 없음 |
| 판독성 | 글자가 너무 작거나 배경에 묻힘 |

다시 만들 때는 `--round 2` 로 앞 회차를 남긴다 — 무엇이 나아졌는지 견줘야 한다.
잘 안 고쳐지는 항목은 프롬프트에 **정확한 문자열을 따옴표로 박아** 준다
("제목(정확히 이 글자): …", "글자가 깨지거나 없는 글자를 만들지 마세요").

### 겪어 보고 알게 된 것 (2026-09)

**두 번 실패한 글자는 낱말을 바꿔 우회한다.** `특징` 이 `톡징` 으로 두 번 연속 나왔고,
프롬프트에 "'특징'을 '톡징'으로 쓰지 마세요"를 박아도 안 고쳐졌다. `특징` → `성질` 로
바꾸니 한 번에 해결됐다. 같은 글자를 고집하는 것보다 뜻이 같은 다른 말이 확실하다.

**`--quality max` 는 쓸 일이 드물다.** 토큰이 4배로 뛰어 장당 $0.165 가 되는데
`high`($0.041)와 눈에 띄는 차이가 없었다.

**사실 오류가 가장 놓치기 쉽다.** 한글만 보고 합격시키면 안 된다. 실제로 걸러낸 것:
휴면 유형 그림에서 "타발적 휴면"(발아하지 *못하는* 상태) 칸에 싹이 튼 새싹이 그려져
뜻이 정반대가 됐다. "싹·떡잎·뿌리를 그리지 마라"를 넣어 잡았다.

**구성은 Gemini, 최종 생성은 GPT** — 둘을 경쟁시키지 말고 역할을 나눈다.
Gemini 는 시키지 않은 좋은 구성(계층도·생활사 도해 등)을 제안하는 대신 한글 오타가
잦다(한 장에 5건: 겡게·꽃꽂·직용·꼭인발·비과). 그 구성을 받아 GPT 로 다시 그리면
정보량과 정확도를 모두 얻는다. 실제로 "잡초의 분류" 인포그래픽을 그렇게 만들었다.

**학술 그림은 도해가 사진보다 낫다.** 생장점 위치처럼 눈에 안 보이는 것을 보여야 할
때는 실사 대신 흙 단면 도해에 빨간 표시를 넣게 한다(화본과=밑동, 사초과=밑동+땅속
덩이줄기, 광엽=줄기 끝). 사진으로는 표현할 수 없는 내용이다.

**오타만 고칠 때는 `--mask` 로 자리를 찍어 준다.** `--ref` 만 주면 사진까지 전부 다시
그려진다(사용자가 "실사를 주는데 왜 바꾸느냐"고 지적한 원인). 고칠 글줄 자리만 투명한
PNG 를 `--mask` 로 함께 주면 그 자리를 맞춰 그리지만, **마스크 밖도 미세하게 흔들린다**
(평균 7/255). 그래서 결과에서 **마스크 영역만 잘라 원본에 얹는다** — 사진은 원본 픽셀
그대로 남는다. 자리는 눈대중이 아니라 글줄의 어두운 화소 띠를 재서 잡는다(눈대중으로는
윗줄을 물었다). "잡초의 발생실태"에서 8곳(밭뚝외풀·좀개구리밥·올챙이고랭이·여뀌바늘×3·
군락·괴경)을 이렇게 고쳤고, `밭`(받침 ㅌ)은 한 번 `발`로 나와 "ㅂ+ㅏ+받침 ㅌ, ㄹ이 아니다"를
박아 2회차에 잡았다. 크기는 16의 배수여야 하므로 1356 폭은 1360 으로 채운 뒤 되잘라 낸다.

넣기는 `insert_note_image.py` — Windows 에서 `/media/...` 경로가 변환되지 않도록
`MSYS_NO_PATHCONV=1` 을 붙인다.
