'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도(단면 포함) · 배식평면도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 못과 흙무덤, 다각형 목재데크 관찰로와 육각전망대, 횃대, 통나무 펜스, 경사로 2, 방지원도 연못과 파고라 4, 주차 18대가 도면대로 나왔으나 시점이 평면에 가까웠습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로 다시 그리게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| A 지역 — 못(+8.0)과 흙무덤(+9.0), 서쪽 물길, 기존수림 | ✓ |
| 흙무덤 경유 폭 2m 목재데크 관찰로(다각형), 완충공간 2, 육각전망대 Ø5 | ✓ |
| 학습안내판 4 · 횃대 10 · 통나무 펜스 1(H0.8, 못 둘레 2m 여유) · 펜스 2(H1.2, A · B 경계) | ✓ |
| A–B 경사로 2(8%, L 6.2m) | ✓ |
| B 지역 — 보행동선 3m 콘크리트블록, 주차 18대 · 출입구 2 · 차로 6m, 아스팔트 | ✓ |
| 수경휴식공간 — 방지원도 연못 12×12 장대석, 목재파고라 4×4 2 · 평상형 파고라 3.5×3.5 2, 마사토 | ✓ |
| 수생식물(갈대 · 부들 · 수련), 8.5 이하 초화(금계국 · 벌개미취 · 부처꽃), 8.5 이상 관목 · 남부수종 교목(녹나무 · 굴거리 · 팽나무) | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a waterside park (north is up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the natural pond with the grassy mound island in the north, the angular timber boardwalk loop with corner decks, the hexagonal gazebo on its west, the bird perches, the log fence around the pond and the taller log fence across the middle, the two ramps, the wildflower meadow, the square granite-edged pond with a round island and the four pergolas in the south-west, the 18-stall parking lot in two facing rows in the south-east, the concrete-block walks, the woodland on the west, the parking and road outside the east and south-east.

    Change ONLY the camera: image 2 is a near top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the south-east looking north-west, tilted about 45 degrees, at roughly 70 m height, so the gazebo, pergolas, boardwalk rails, perches, mound and trees show their height and sides and the far (north-west) side appears smaller than the near side. Long soft late-afternoon shadows.

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
