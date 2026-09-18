'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도(단면 포함) · 식재설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 팔각정 · 침상공간(벽천 · 연못 · 라운드 계단 · 직선 계단 + RAMP · 계단식 녹지대 · 원형플랜터 · 적/회색 타일) · 화장실 · 파고라 3 · 주차 10 · 마운딩이 도면대로 나왔으나 시점이 평면이었습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로 다시 그리게 했습니다(2회차) — 3m 깊이의 침상공간이 벽과 벽천이 보이는 진짜 구덩이로 읽힙니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 서 50m 광로 · 남 24m 도로, 남서 모따기, 북서 도시림 · 북 고물수집장 · 동 초등학교 운동장 | ✓ |
| '가'(+6.0) 경관식재공간 잔디 · 관목, 팔각정(한 변 3m) 1, 계단으로 연결 | ✓ |
| '나' 보행자 휴식공간 화강석 포장 — 화장실 1 · 파고라 3 · 음수대 1 · 벤치 6 · 조명등 4 | ✓ |
| '라' 침상공간 −3m — 서쪽 연못 2m + 벽천 3m, 녹지대 1.5m, S1 라운드 계단, S2 직선 계단 + RAMP 8%, 북 · 동 계단식 녹지대 2, 원형플랜터 Ø5, 적/회색 타일 | ✓ |
| '다' 주차 10대 아스콘, 진입로 5m(남측 도로), 운동장 쪽 마운딩 2m 이하 | ✓ |
| 도로변 완충식재(50m 쪽 H3m ↑ · 24m 쪽 H2m ↑), 고물수집장 경계 식재, 도시림 경계 식재 생략 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a street-corner pocket park (north is up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the octagonal pavilion in the raised south-west zone, the sunken square garden with its waterfall wall and pond on the west side, the fan-shaped steps at its north-west corner, the straight steps and zig-zag ramp at its south-east corner, the stepped planter terraces on the north and east walls, the round central planter, the red/grey checker floor, the toilet and three pergolas along the north plaza, the 10-stall parking lot on the east with its drive from the south road, the mound toward the school playground, the boulevard on the west, the road on the south, the woodland and scrap yard to the north.

    Change ONLY the camera: image 2 is a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the south-west looking north-east, tilted about 45 degrees, at roughly 50 m height, so the 3 m deep sunken garden reads as a real pit with visible walls and the waterfall, and the pavilion, pergolas, toilet and trees show their height and sides; the far (north-east) side appears smaller than the near side. Long soft late-afternoon shadows.

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
