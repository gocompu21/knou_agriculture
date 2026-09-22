'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 종합계획도 · 호안 상세도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 하천 — 사주부 호안(호안블럭 · 나무말뚝 · 야자섬유두루말이 · 갈대 · 갯버들) — 제방(초화 · 교목 열) — 자전거도로 · 보행로 — 휴식/조각/잔디공간 — 완충 보행로 — 주차 10대 — 도로 · 주거지 차례가 도면대로 나왔으나 시점이 평면에 가깝고 조각이 4개였습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로, 조각을 3개로 고치게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 서쪽부터 하천 8m · 호안 · 제방 · 공원 · 주차장 · 도로 | ✓ |
| 사주부 호안 — 호안블럭 · 나무말뚝 1열 · 야자섬유두루말이 2열 · 갈대 1m · 갯버들 1m | ✓ |
| 제방 +1.0 성토, 상층부에만 교목(낙우송 · 왕버들 · 물푸레) 한 줄, 초화(유채 · 민들레 · 쑥부쟁이) | ✓ |
| 자전거도로 2m(투수콘) + 보행로 2.5m, 경계식재(무궁화 · 개나리) | ✓ |
| 휴식공간 — 이동식 쉘터 4×4 2 · 벤치 6 · 휴지통 2 | ✓ |
| 조각공원 — 원형연못 Ø4 + 2m 원형동선, 잔디에 조각 3 | ✓ (2회차에 3으로) |
| 잔디공간 — 원형쉘터 Ø3 4, 둘레 화관목 | ✓ |
| 보행자 완충공간 3m, 주차 10대 직각 일방통행(북 입구 → 남 출구), 도로변 완충녹지 · 배수 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the master plan of a riverside park (north is up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — river and bio-engineered bank on the left (revetment blocks, stakes, coir rolls, reeds, willow cuttings), the grass levee with its wildflowers and line of trees, the bicycle path and pedestrian path, the hedged park with the rest area (two square shelters, benches, bins), the sculpture garden with the round pond and circular path, the lawn with four round umbrella shelters, the buffer walkway with trees, the single row of parking stalls with north entrance / south exit, the road and houses on the right.

    Change these two things only:
    1. CAMERA — image 2 is almost a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the south-east looking north-west, tilted about 45 degrees, at roughly 60 m height, so the shelters, sculptures, trees, levee slope and riverbank show their height and sides and the far (north) end appears smaller than the near (south) end. Long soft late-afternoon shadows.
    2. The sculpture garden has EXACTLY 3 sculptures on plinths (currently 4).

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.

---

# 입체 평면도 · 축측도 — 블렌더로 세운 모형 (2~4번 그림)

위 조감도는 **분위기**를 보여 주지만 **치수는 맞지 않습니다**. 이미지 모델은 화면에서
길이를 재지 못하기 때문에, "주차 구획 10대"·"연못 ⌀4m"를 몇 번을 말해도 회차마다
달라집니다. 그래서 **치수가 필요한 그림은 3차원 모형으로 따로 세웠습니다**.

- **2번 — 입체 평면도**: 도면의 치수를 그대로 세운 모형을 바로 위에서 내려다본 것.
  도면과 겹쳐 보면 띠 경계·주차 구획·연못 지름이 1m 단위로 맞습니다
- **3번 — 입체 축측도**: 같은 모형을 45° **평행투영**으로 본 것. 조감도(원근)와 달리
  먼 변과 가까운 변의 길이가 같아, **그림에서 잰 길이가 곧 실제 길이**입니다
- **4번 — 실사 입체도**: 3번을 그대로 두고 **재질만** 실사로 바꾼 것. 배치·시점·크기를
  건드리지 못하게 못박았습니다

## 모형에 들어간 치수 (성운 답안 도면 기준)

서 → 동, 단위 m.

| 띠 | 범위 | 내용 |
| --- | --- | --- |
| 하천 | 0 ~ 8 | 수면 −1.0 |
| 사주부 호안 | 8 ~ 12.72 | 호안블럭 2m · 나무말뚝 1열 · 야자섬유두루마리 2열 · 갈대 1m · 갯버들 1m |
| 제방 | 12.72 ~ 18 | 마루 +1.0, 교목 15주 한 줄(낙우송 5 · 왕버들 5 · 물푸레나무 5) |
| 자전거도로 | 18 ~ 20 | 적색 투수콘, 보행로와 사이에 연석선 |
| 보행로 | 20 ~ 22.5 | 회색 투수콘 |
| 공원 | 22.5 ~ 35.8 | 북에서 남으로 휴식(0~13) · 조각(13~27) · 잔디(27~40) |
| 완충 보행공간 | 35.8 ~ 38.5 | 소형고압블럭 |
| 주차장 | 38.5 ~ 53.3 | 아스팔트, 2.5×5 구획 북 5 + 남 5 |
| 동측 완충녹지 | 53.3 ~ 55 | 회양목 |

시설은 휴식공간에 쉘터 4×4 2동 · 평의자 6(좌 2 · 우 2 · 가운데 가로 2) · 휴지통 2,
조각공원에 원형연못 ⌀4 + 원형동선 폭 2 + 십자동선 1.8, 잔디밭 네 구획에 조각 8,
잔디공간에 원형퍼걸러 ⌀3 4동입니다.

## 왜 이렇게 만들었나

이미지 모델에게 축측도를 22회차까지 시켜 봤지만, 고치면 다른 데가 틀어지는 일이
되풀이됐습니다 — 자리를 백분율로 말해도, 개수를 "정확히 3개"라고 말해도 듣지
않습니다. 반면 3차원 모형은 **숫자를 고치면 그 자리만 정확히 바뀌고** 나머지는
한 화소도 변하지 않습니다.

> 검증은 눈대중이 아니라 **겹쳐 보기**로 했습니다. 도면의 검은 선만 뽑아
> 1m = 같은 화소로 맞춘 뒤 평면 렌더 위에 빨갛게 얹어, 어긋난 곳을 찾아 숫자를
> 고치고 다시 렌더하기를 되풀이했습니다.

실사(4번)는 그 모형 그림을 GPT 에 주고 **"배치·시점·크기는 한 개도 건드리지 말고
재질만 바꿔라"**고 한 것입니다. 사진처럼 보이면서도 치수는 모형 그대로입니다.
