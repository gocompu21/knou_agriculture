'성운' 탭의 **답안지 II · 시설물배치도**와 문제지 조건을 AI 이미지 모델에 주고 만든 **입체 조감도**입니다(2026년 9월 18일).
위 첫 장이 **GPT**(gpt-image-2.5-sunburst), 둘째 장이 **제미나이**(gemini-3-pro-image-preview) — 둘 다 2회차(재작업)입니다.

## 만든 방법

1. 시설물배치도에서 표제란을 잘라낸 그림을 **참고 그림**으로 주고, 아래 **1회차 프롬프트**로 그렸습니다
2. 나온 그림을 도면과 대조했더니 두 모델 모두 **남동 모서리를 둥글게** 그리고 **지하철 출입구를 부지 안 광장에** 넣었습니다(도면은 45° 모따기 · 출입구는 모서리 바깥 보도). 제미나이는 서측 상업지를 아파트로 그렸습니다
3. 1회차 그림을 참고 그림으로 다시 주고 **2회차(수정) 프롬프트**로 그 부분만 고치게 했습니다 — 나머지는 그대로 두라고 못박았습니다

## 도면과 대조

| 도면(성운 답안) | GPT | 제미나이 |
| --- | --- | --- |
| 주차열 4줄(위 2줄 길고 아래 2줄 짧음), 열 가운데 녹음수 | ✓ | ✓ |
| 북서 휴게광장 — 퍼걸러 · 격자 수목보호대 | ✓ | ✓ |
| 북측 화장실 · 주차관리소(북동 · 남서) | ✓ | ✓ |
| 남동 휴게광장 — 삼각 화단 · 장애인 주차 | ✓ | 화단이 네모로 바뀜 |
| 서측 보행로 + 주차 1줄 | ✓ | ✓ |
| 북 · 서측 12m 상록 차폐 띠, 남 · 동측 가로수 | ✓ | ✓ |
| 북측 주거지 · 서측 상업지 · 남 · 동측 35m 광로 | ✓ | ✓ (2회차에 고침) |
| 남동 모서리 45° 모따기 | ✓ (2회차에 고침) | 녹지 경계만 대각선, 도로 모서리는 둥긂 |
| 지하철 출입구 — 모서리 바깥 보도 | ✓ (2회차에 고침) | ✓ (2회차에 고침) |

GPT 쪽이 도면에 더 가깝습니다. 비용은 GPT 약 $0.08(2장), 제미나이 약 $0.26(2장)이었습니다.

## 1회차 프롬프트 (두 모델 같음)

    Create a photorealistic 3D aerial bird's-eye perspective rendering (조감도) of a landscaped "parking park" (주차공원), based EXACTLY on the attached landscape site plan drawing (Korean landscape architect exam answer sheet, scale 1/400, north is UP in the drawing). Keep the layout, proportions and positions from the plan; only turn it into a realistic 3D view.

    Camera: high oblique aerial view from the SOUTH-EAST corner looking toward the north-west, about 60 m above ground, so the whole site is visible. Clear late-spring daylight, soft shadows.

    SITE (rectangle about 150 m east-west × 107 m north-south, flat):
    - The south-east corner is cut diagonally (chamfered). Just outside this corner, on the sidewalk, is a subway station entrance (Seoul-style glass-roofed stair entrance).
    - South side and east side: wide 35 m urban boulevards meeting at an intersection at the south-east corner, with cars and crosswalks.
    - North side: residential area (mid-rise apartments). West side: commercial buildings (4–6 storey shops/offices).

    PARKING (center of the site, black asphalt):
    - About 300 cars in 90-degree (perpendicular) parking stalls, white stall lines, 2.3 m × 5 m stalls, 6 m driving aisles, one-way circulating loop.
    - Four long east-west double rows of stalls. The upper two rows run almost the full width; the lower two rows are shorter (western part only).
    - Down the middle of each double row runs a narrow planted median with a line of deciduous shade trees (Chinese fringe tree / zelkova). Each row ends with a rounded planting island with shrubs.
    - One more single row of stalls along the west side, next to a north-south pedestrian walkway paved in grey-and-red concrete blocks.
    - A group of 8 accessible parking stalls (blue with wheelchair marks) in the south-east part.
    - Vehicle entrances: one on the east side (upper right) and one on the south side (lower left, south-west). Small 4 m × 4 m parking attendant booths next to both vehicle entrances.
    - Cars parked in most stalls (mixed colours, mostly white/grey/black sedans and SUVs).

    REST AREAS (two, as in the plan):
    - North-west corner: square plaza paved with granite slabs, with two long wooden pergolas (4 m × 8 m), benches, a drinking fountain, and a grid of trees planted in square tree grates.
    - South-east part (next to the chamfered corner, near the subway entrance): second rest plaza with benches, a triangular flower bed with flowering shrubs, and a pedestrian entrance facing the subway.
    - A small toilet building (6 m × 10 m, hip roof) on the north side, a little west of centre.
    - A pedestrian path runs along the whole north edge; part of it is paved with interlocking blocks.

    PLANTING (important — about one third of the site is green):
    - North and west edges: a 12 m wide buffer belt — a dense continuous row of evergreen conifers (eastern white pine, hinoki cypress, juniper) screening the residential and commercial areas, with deciduous trees and masses of azalea/rhododendron shrubs in front.
    - South and east edges along the boulevards: a 6 m wide green strip with a row of street trees (ginkgo, zelkova) and low clipped boxwood and azalea hedges.
    - Flowering accent trees (crabapple, dogwood, hawthorn) at the entrances and around the rest areas.

    STYLE: realistic landscape-architecture visualization, clean and accurate, like a professional competition rendering. Show the pavement materials clearly (asphalt for cars, granite slabs and concrete blocks for pedestrians).
    Do NOT write any text, letters, labels, numbers or signs in the image.

## 2회차(수정) 프롬프트 — GPT

    Edit this aerial rendering of a parking park. Keep EVERYTHING else exactly as it is (parking rows, trees, plazas, toilet building, booths, roads, buildings, camera angle, lighting). Fix only the south-east corner (bottom-right of the site, where the south boulevard meets the east boulevard):

    1. The site corner must be cut off by a STRAIGHT DIAGONAL edge at 45 degrees (a chamfer, about 25 m long) — not rounded. The site boundary, the green planting strip and the plaza paving all follow this straight diagonal line, and the sidewalk outside runs parallel to it.
    2. The glass-roofed subway station entrance must stand OUTSIDE the site, on the public sidewalk between that diagonal edge and the road intersection, with its stair opening facing the rest plaza. Remove it from inside the plaza; fill that spot in the plaza with paving, benches and a small tree.

    Do NOT add any text, letters, numbers or signs.

## 2회차(수정) 프롬프트 — 제미나이

    Edit this aerial rendering of a parking park. Keep EVERYTHING else exactly as it is (parking rows, trees, plazas, toilet building, booths, roads, camera angle, lighting). Fix only the south-east corner (bottom-right of the site, where the south boulevard meets the east boulevard):

    1. The site corner must be cut off by a STRAIGHT DIAGONAL edge at 45 degrees (a chamfer, about 25 m long) — not rounded. The site boundary, the green planting strip and the plaza paving all follow this straight diagonal line, and the sidewalk outside runs parallel to it.
    2. The glass-roofed subway station entrance must stand OUTSIDE the site, on the public sidewalk between that diagonal edge and the road intersection, with its stair opening facing the rest plaza. Remove it from inside the plaza; fill that spot in the plaza with paving, benches and a small tree.

    Do NOT add any text, letters, numbers or signs.

    3. The buildings on the WEST side (left edge of the image) must be 4 to 6 storey COMMERCIAL buildings (shops on the ground floor, offices above), not apartment blocks. The apartments stay only on the NORTH side (top).
