'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 배식평면도 2장을 참고 그림으로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 기념관 · 정형연못 2 · 중앙광장 문주 4 · 파고라/잔디 휴식공간 · 사괴석담장과 중문 · 주차 5+5 · 계단과 경사로로 오르는 마름모꼴 기념탑 공간(기념탑 · 군상조형물 2 · 명각표석)이 모두 도면대로 나왔으나 시점이 평면에 가까웠습니다
2. 도면 + 1회차 그림을 주고 배치는 그대로 45° 입체 시점으로 다시 그리게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 기록·기념관(단층 팔작지붕) + 사괴석포장 전면 + 정형연못 2 | ✓ |
| 중앙광장 22×22, 문주 4 | ✓ |
| 시설물 휴식공간(파고라 5×10 · 등벤치) · 잔디 휴식공간 | ✓ |
| 사괴석담장 H2.2 + 기와지붕 중문 | ✓ |
| 진입공간 — 가운데 보행 진입, 양쪽 주차 5+5(장애인 2), 목련 화단, 차량 진입 2곳 | ✓ |
| '다' 지역 — 계단 + 굽은 경사로, 마름모꼴 기념탑 공간, 원형좌대 + 기념탑 H18, 군상조형물 2, 명각표석 | ✓ |
| 둘레 잣나무 차폐, 광장 둘레 녹음수, 광장 동쪽 소나무 요점식재, 기존수림 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a memorial park (drawing's top = up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the tiled-roof memorial hall at the top with its stone-sett forecourt and two rectangular ponds, the central plaza with its four gate pillars, the pergola rest area (left) and lawn rest area (right), the stone wall with the small tiled gate, the central pedestrian approach with a 5-stall parking lot on each side, the steps and winding ramp up to the diamond-shaped memorial terrace on the right with its tall steel tower, two bronze figure groups and inscribed stone, the pine screen along the left edge and the surrounding forest.

    Change ONLY the camera: image 2 is almost a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the drawing's lower-right, looking toward the upper-left, tilted about 45 degrees, at roughly 80 m height, so the memorial hall's roof and walls, the 18 m tower, the gate pillars, the stone wall, the pergola and every tree show their height and sides, and the far (top) side of the site appears smaller than the near (bottom) side. Long soft late-afternoon shadows. The whole site plus a margin of forest and the access road at the bottom stays in frame.

    Also make sure: EXACTLY 4 gate pillars at the four corners of the central plaza; EXACTLY 2 bronze figure groups; the parking lots have 5 stalls each. Everything else exactly as in image 2. Photorealistic. Do NOT write any text, letters, numbers, labels or signs.
