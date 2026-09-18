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
