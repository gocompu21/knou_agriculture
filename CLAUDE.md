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
  CAD(`docs/CAD.md`) · 실기 필답(`docs/실기필답.md`) · 영상(`docs/도면영상.md`) · 이미지 모델(`docs/GPT이미지.md`) ·
  쪽집게 노트(`docs/쪽집게노트.md`) · 잡초 퀴즈(`docs/잡초퀴즈.md`) · 동영상 탭(`docs/동영상탭.md`) · 실기 작업형(`docs/실기작업형.md`)이
  그렇게 나갔다. 그 기능을 고칠 때는 그 문서를 먼저 읽고, 경험도 그 문서에 적는다

- 기능을 고칠 때마다 **무엇을 왜 그렇게 했는지**와 **겪은 함정**을 해당 절에 적는다.
  결과만 적지 말고 "처음엔 이렇게 했다가 이래서 바꿨다"를 남긴다 — 그래야 같은 길을 다시 안 간다
- 이 CAD 는 일반 CAD 가 아니라 **실제 제도판을 화면으로 옮긴 것**이라 교과서에 없는 기준이 대부분이다.
  그 기준은 대표님의 실물 사진과 지적에서 나온다 — 사진은 눈대중 말고 화소를 세어 옮긴다
- **대표님 화면 그대로 재현해 확인한다.** 확대한 상태에서만 시험하면 놓친다 — 템플릿 귀 긋기는
  확대해서는 됐는데, 맞춤 배율(귀가 화면 3px)에서 곧은 변부터 대고 돌면 안 그어졌다. 아래쪽 가장자리
  띠는 svg 사각형 그대로 두었더니 상태줄에 가려 커서가 닿지 않았다
- 고치면 묻지 않고 커밋 → main → 서버 배포까지 한다 — **`bash tools/ship.sh "커밋 제목"`** 한 줄로
  (바뀐 템플릿 JS 검사 → 커밋(Co-Authored-By) → rebase·push → 서버 pull·gunicorn 재시작. 문서만이면 `--no-restart`,
  서버만 맞추려면 `--deploy`). 서버 마이그레이션은 하지 않으니 필요하면 따로
- **템플릿(.html)을 Edit/Write 하면 훅이 그 안의 JS 를 저절로 `node --check` 한다**(사용자 설정 `~/.claude/settings.json`
  의 PostToolUse → `~/.claude/hooks/jscheck_template.py`). 오류면 바로 알려 오니 그 자리에서 고친다.
  워크트리의 `.claude/` 는 git 밖이라 프로젝트 설정이 아니라 사용자 설정에 두었다

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

## 쪽집게 노트 · 잡초 퀴즈 (별도 문서)

- **[docs/쪽집게노트.md](docs/쪽집게노트.md)** — 방송대 StudyNote(30과목 341장)·노트 생성 방식·PREFIX_MAP, 관리자 편집(Toast UI·밑줄·이미지), 아코디언, 관련 문제 펼침, 질의응답 ↔ 절 연결, 답 렌더러 조각
- **[docs/잡초퀴즈.md](docs/잡초퀴즈.md)** — 잡초방제학 A+ 문제집 재구축, 잡초 동정 퀴즈(카드·사진 자르기·손그림·교수 메모·기출 배지·별칭표·새 카드 등록·위키미디어 사진)
- 꼭 지킬 것: 세 페이지가 같은 잡초 조각을 쓴다(`main/_weed_*.html`, 이름은 `wd-`·`wdn-`). `display:flex` 는 `[hidden]` 을 이긴다 — `.클래스[hidden] { display:none }` 을 함께 둔다. Django `{# #}` 는 한 줄 주석뿐

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


## 동영상 탭 · 실기 작업형 화면 (별도 문서)

- **[docs/동영상탭.md](docs/동영상탭.md)** — 목차꼴 분류 관리(그 자리에서 갈아 끼우기·판 확인·반전), 등록 실패 표시, AI 요약(유튜브 주소 그대로 Gemini 에)
- **[docs/실기작업형.md](docs/실기작업형.md)** — 자연생태복원 작업형, 조경 작업형(기출분석 탭·도면 자료 탭·조감도 만드는 법·모눈 도면 → SVG → 단계 재생)
- 꼭 지킬 것: 템플릿 JS 는 `python _jscheck.py '<주소>'`(또는 `node --check`)로 문법 검사 — 서버 렌더 검사로는 안 잡힌다

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
- 화면은 `templates/gisa/_cad.html` 한 파일. 고친 뒤 `python tools/cad_test/cadkit.py` 로 JS 문법 검사 —
  서버는 200 을 주는데 브라우저에서만 블록이 통째로 죽는다
- **대표님 화면 그대로 재현해 확인**한다(맞춤 배율, 실제 도면). 시험 도구는 **`tools/cad_test/`** 에 있다 —
  `cadkit.py`(도면을 초안으로 넣고 CAD 탭을 여는 `Cad`, 운영 도면 읽어 오기, JS 문법 검사) · `smoke.py <pk>` · `lead_test.py`(본보기).
  임시 폴더에 새로 짜지 말고 여기에 더한다. 개발 서버(`--noreload` 면 템플릿 고친 뒤 다시 띄울 것)
- **서버 도면을 직접 고칠 때는 `python tools/server_cad.py` 로만** 한다(2026-10, 하네스 5번) — `list` · `pull <번호>` ·
  `edit <번호> 고침.py [--dry]`(고침.py 의 `apply(doc)` 가 doc 을 고친다 → 바뀐 것 요약 → 올림) · `backups` · `restore`.
  올리기 직전 서버 `~/cad_backups/` 에 지금 판을 백업하고, **판(stamp)이 받아 올 때와 다르면 올리지 않는다**
  (그사이 대표님이 화면에서 저장했으면 덮지 않는다). 먼저 `--dry` 로 바뀌는 것을 보고, 올린 뒤에는
  대표님께 "그 도면을 열어 두셨다면 저장하지 말고 새로 고침"을 꼭 말씀드린다
- 기준은 대표님 실물 사진·지적에서 나온다 — 사진은 화소를 세어 옮긴다

## 블렌더 모형 · 도면 소개 영상 · 이미지 모델 (별도 문서)

- **[docs/도면영상.md](docs/도면영상.md)** — 블렌더로 도면 세우기(make428·401·444, anim444), 444 소개 영상에서 대표님이 정한 규칙(흐름·차 장면·힉스필드 CLI)
- **[docs/GPT이미지.md](docs/GPT이미지.md)** — GPT·Gemini 이미지 모델 화법·덧그리기·화소 검증, 인포그래픽 글자 검증
