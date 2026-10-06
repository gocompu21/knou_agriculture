# CAD 확인 도구 (tools/cad_test)

CAD 탭(`templates/gisa/_cad.html`)을 고친 뒤 **대표님 화면 그대로 재현해 확인**하는 도구.
예전에는 세션마다 임시 폴더에 시험 코드를 새로 짰고, 세션이 끝나면 사라졌다(2026-10 여기로 모음).

| 파일 | 하는 일 |
|------|---------|
| `cadkit.py` | 공통 도구 — `Cad(doc)` 로 도면을 초안으로 넣고 CAD 탭을 연다. 도면 좌표(m)로 누르기·끌기·확대, 초안 읽기, 찍기, 페이지 오류 모으기. `server_drawing(pk)` 는 운영 도면을 **읽기만** 해 온다. 직접 돌리면 JS 문법 검사 |
| `smoke.py` | 운영 도면 하나를 그대로 열어 페이지 오류·화면을 본다 |
| `lead_test.py` | 식재지시선 긋기 → 수정 → 형 바꾸기. 새 시험을 짤 때 본보기 |

```bash
../../../venv/Scripts/python.exe tools/cad_test/cadkit.py          # JS 문법 검사(node --check)
../../../venv/Scripts/python.exe tools/cad_test/smoke.py 10       # 서버 도면 pk 10 열어 보기
../../../venv/Scripts/python.exe tools/cad_test/lead_test.py      # 지시선 시험
```

- 개발 서버가 떠 있어야 한다(기본 8099, `--port`). `--noreload` 로 띄웠으면 **템플릿을 고친 뒤 다시 띄운다**
- 로그인은 로컬 DB 의 스태프 계정으로 세션을 만들어 쓴다(쿠키 값을 박아 두지 않는다)
- 결과 그림·운영 도면 캐시는 `out/` (git 밖)
- 시험은 **실제 배율로** — 확대해서만 시험하면 놓친다(맞춤 배율에서 템플릿 귀가 3px 이었던 일)
