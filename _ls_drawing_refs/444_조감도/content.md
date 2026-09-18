'성운' 탭의 **답안지 II · 시설물배치도**와 **답안지 III · 배식평면도**, 문제지 조건을 AI 이미지 모델에 주고 만든 **입체 조감도**입니다(2026년 9월 18일).
위 사진의 첫 장이 **GPT**(gpt-image-2.5-sunburst, 3회차), 둘째 장이 **제미나이**(gemini-3-pro-image-preview, 2회차)입니다.

## 만든 방법 (GPT)

1. 도면 2장(시설물배치도 · 배식평면도, 표제란은 잘라냄)을 **참고 그림**으로 주고 **1회차 프롬프트**로 그렸습니다. 배치는 도면대로 나왔으나 거의 평면이었고, 남동 광장의 벤치 줄이 2개뿐이었습니다
2. **도면 + 1회차 그림**을 함께 주고 "배치는 그대로, 45° 입체 시점으로 다시 그리되 벤치 줄·녹지대 교목을 고치라"고 했습니다(2회차). 입체감이 생기고 배치도 유지됐습니다. 남은 것은 벤치 줄 3개(도면 6개), 삼각 화단 벤치 자리, 정원등, 볼라드 수
3. **도면 + 2회차 그림**을 주고 광장 가구의 **개수만** 고치게 했습니다(3회차) — 벤치 줄 3+3 과 휴지통·음수대, 삼각 화단 위 3 · 왼쪽 3, 정원등 3. 볼라드는 5개를 요구했는데 7개로 남았습니다

> **회차마다 도면을 첫 참고 그림으로 다시 준다.** 앞 회차 그림만 주면 기준이 흐려져 조금씩 어긋납니다.
> **마스크로 일부만 고치거나 그림을 손으로 자르고 돌리지 않는다.** 그 방법으로 한 앞선 시도는 장애인 주차칸을 옆 주차열에 맞춘다고 옮기다 순환 차로를 막고, 비스듬한 조감도에서 칸만 수평으로 세워 오히려 주변과 어긋나게 만들었습니다. 틀리면 도면과 함께 **통째로 다시 그리게** 하는 편이 확실합니다

## 도면과 대조 (GPT 3회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 107m × 150m 부지, 남동 모서리 45° 모따기, 모서리 밖 보도에 지하철 출입구 | ✓ |
| 주차열 4줄(북쪽 2줄 길고 남쪽 2줄 짧음), 열마다 가운데 녹지 · 녹음수 · 양 끝 둥근 화단 | ✓ |
| 주차장을 도는 순환 차로 — 장애인 주차칸 서쪽 남북 차로가 남쪽 가장자리까지 열림 | ✓ |
| 장애인 주차 8칸 — 3번째 열 동쪽, 그 열 위쪽 칸과 같은 줄, 북쪽 차로로 열림 | ✓ |
| 서측 보행로 + 주차 1줄, 북 · 서측 12m 상록 차폐 띠, 남 · 동측 6m 가로수 | ✓ |
| 북서 휴게광장(퍼걸러 2 · 격자 수목보호대), 북측 화장실, 주차관리소 북동 · 남서 | ✓ |
| 남동 광장 — 장애인 주차 아래 녹지대(교목 6 · 정원등 3), 벤치 3 + 휴지통 · 음수대 + 벤치 3 | ✓ |
| 남동 광장 — 직각삼각형 화단(위 벤치 3 · 왼쪽 벤치 3), 북동 · 남서 모서리 체크무늬 포장 | ✓ |
| 남동 광장 서측 볼라드 5 | **7개** — 두 번 요구했으나 안 줄었습니다 |
| 북측 주거지 · 서측 상업지 · 남 · 동측 광로, 글자 없음 | ✓ |

비용은 GPT 3장 약 $0.12, 제미나이 2장 약 $0.26 입니다.

## 1회차 프롬프트 — GPT (참고: 시설물배치도 · 배식평면도)

    Create a photorealistic 3D bird's-eye perspective rendering of a landscaped "parking park" (주차공원). The FIRST attached image is the facilities plan (north is up), the SECOND is the planting plan of the same site. These plans are the ground truth: reproduce their layout, proportions and positions faithfully, and only turn them into a realistic 3D view. Do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST, looking north-west, tilted about 45 degrees (a true 3D perspective, not a flat top-down map), high enough that the entire site and a little of the surrounding streets are visible. Late-spring daylight, soft shadows.

    SITE: a flat rectangle about 150 m (east-west) x 107 m (north-south). Only the SOUTH-EAST corner is cut by a straight 45-degree chamfer about 25 m long. Wide boulevards run along the SOUTH and EAST sides and meet at the south-east corner; a glass-roofed subway station entrance stands on the public sidewalk just outside the chamfered corner. Mid-rise apartments lie beyond the NORTH edge, 4-6 storey commercial buildings beyond the WEST edge.

    PERIMETER (from the plan):
    - North and west edges: a 12 m wide green buffer belt of dense evergreen conifers with deciduous trees and azalea masses in front. Along the inside of the north belt runs a pedestrian path; a small hip-roofed toilet building (6 x 10 m) stands on this north strip a little west of the centre.
    - South and east edges: a 6 m green strip with a row of street trees and low clipped hedges.
    - NORTH-WEST corner: rest plaza paved with granite slabs — two long wooden pergolas, benches, a drinking fountain, and a grid of trees in square tree grates.
    - WEST side, inside the buffer: a north-south pedestrian walkway paved in grey-and-red concrete blocks, with ONE single row of parking stalls just east of it.
    - Vehicle entrances: one on the EAST edge near the north-east corner, one on the SOUTH edge near the south-west corner. A 4 x 4 m parking attendant booth stands beside each vehicle entrance (north-east and south-west).

    PARKING (centre, black asphalt, white stall lines, about 300 cars, all 90-degree stalls, cars parked in most stalls):
    - A continuous one-way RING driving aisle (6 m wide) runs around the whole parking area, connecting both vehicle entrances. Every parking row is reachable from this ring; NO row or plaza may block the ring.
    - Four east-west DOUBLE rows of stalls (stalls back-to-back) with driving aisles between them. Rows 1 and 2 (the two northern rows) run almost the full width of the site. Rows 3 and 4 (the two southern rows) are SHORTER and occupy only the western two-thirds; their east ends stop well before the east ring aisle.
    - Down the middle of every double row runs a narrow planted median with a line of deciduous shade trees; each row ends in a rounded planting island with low shrubs.
    - ACCESSIBLE PARKING: one straight row of 8 blue stalls with white wheelchair symbols, located EAST of row 3 (the third row from the north), in line with row 3's northern stalls, opening north onto the same aisle as row 3. A north-south segment of the ring aisle passes just WEST of these stalls and continues south to the south edge — this aisle must stay open.

    SOUTH-EAST REST PLAZA (directly south of the 8 accessible stalls, in the south-east part, bounded on the west by that north-south ring aisle and on the south-east by the chamfered site edge):
    - Light-grey granite slab paving in a square grid; a checkered band of grey and reddish concrete blocks at its north-east corner and its south-west corner.
    - Between the accessible stalls and the plaza: a narrow 3 m planting strip with a line of about 6 deciduous trees, low shrubs and 3 small garden lamps.
    - Along the top edge of the plaza, right under that strip: a straight line of 6 wooden benches (3 + 3) with a round trash bin and a round drinking fountain in the middle.
    - In the plaza's west half: ONE raised flower bed shaped as a right triangle (vertical left side, horizontal top side, long diagonal side from top-right to bottom-left, parallel to the chamfer), planted with 3 round junipers and low flowering shrubs; 3 benches along its top edge, 3 benches along its left edge.
    - Along the plaza's WEST edge, where it meets the north-south ring aisle: a line of 5 short stone bollards (no trees, no wall) — the aisle beside it stays a normal open asphalt roadway.
    - A pedestrian opening in the chamfered edge leads out to the subway entrance on the sidewalk.

    STYLE: clean professional landscape-architecture visualization. Show asphalt for the car areas and granite / concrete-block paving for pedestrian areas clearly. Do NOT write any text, letters, labels, numbers or signs anywhere in the image.

## 2회차 프롬프트 — GPT (참고: 시설물배치도 · 1회차 그림)

    The FIRST attached image is the facilities plan of a parking park (north is up). The SECOND attached image is a rendering of that plan whose LAYOUT is correct: keep every element of the second image in exactly the same place — the four double parking rows (two long northern rows, two shorter southern rows), the ring driving aisle around them, the single west row with its walkway, the north-west pergola plaza, the north toilet building, the two attendant booths, the 8 blue accessible stalls east of the third row, the south-east plaza with its triangular flower bed, bollards and checkered paving, the chamfered south-east corner and the subway entrance outside it on the sidewalk, the 12 m evergreen buffer on the north and west edges and the 6 m street-tree strip on the south and east edges.

    Make these changes:

    1. CAMERA — the second image is almost a flat top-down map. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE: camera in the south-east, looking north-west, tilted about 45 degrees, at roughly 80 m height. Buildings, pergolas, the toilet, the subway entrance and every tree must show their height and sides; the far (north-west) side of the site appears smaller than the near (south-east) side; cars show roofs and sides. Long soft shadows from afternoon sun. The whole site plus a margin of the surrounding streets stays in frame.

    2. In the south-east plaza, between the 8 accessible stalls and the plaza paving: a 3 m planting strip with a line of 6 medium deciduous trees, low shrubs and 3 small garden lamps. Directly below that strip, on the paving, one straight line of 6 wooden benches (3 on the left, 3 on the right) with a round trash bin and a round drinking fountain side by side in the middle.

    3. Around the triangular flower bed: 3 benches along its top edge and 3 benches along its left edge.

    Everything else exactly as in the second image. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.

## 3회차 프롬프트 — GPT (참고: 시설물배치도 · 2회차 그림)

    The FIRST attached image is the facilities plan of a parking park (north is up). The SECOND attached image is a 3D rendering of it that is already correct in layout and camera angle. Reproduce the second image EXACTLY — same camera, same perspective, same parking rows, trees, buildings, roads, subway entrance, lighting — and change ONLY the furniture details in the south-east rest plaza listed below:

    1. The straight line of benches on the paving directly below the planting strip (the strip under the 8 blue accessible stalls): make it EXACTLY 6 wooden benches in one straight row — 3 benches on the left, then the round trash bin and the round drinking fountain side by side in the middle, then 3 benches on the right. Currently there are only 3 benches.

    2. The triangular raised flower bed: place EXACTLY 3 wooden benches in a row along its TOP (horizontal) edge and EXACTLY 3 wooden benches in a column along its LEFT (vertical) edge. REMOVE the 2 benches that currently sit below / to the right of the triangle — there must be no benches along the diagonal side.

    3. In the planting strip under the accessible stalls, add 3 small square garden lamps evenly spaced between the trees.

    4. The stone bollards along the west edge of the plaza: EXACTLY 5, evenly spaced.

    Nothing else changes. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.

## 제미나이 프롬프트 (1회차는 GPT 1회차의 앞선 판과 같고, 2회차는 아래)

    Edit this aerial rendering of a parking park. Keep EVERYTHING else exactly as it is (parking rows, trees, plazas, toilet building, booths, roads, camera angle, lighting). Fix only the south-east corner (bottom-right of the site, where the south boulevard meets the east boulevard):

    1. The site corner must be cut off by a STRAIGHT DIAGONAL edge at 45 degrees (a chamfer, about 25 m long) — not rounded. The site boundary, the green planting strip and the plaza paving all follow this straight diagonal line, and the sidewalk outside runs parallel to it.
    2. The glass-roofed subway station entrance must stand OUTSIDE the site, on the public sidewalk between that diagonal edge and the road intersection, with its stair opening facing the rest plaza. Remove it from inside the plaza; fill that spot in the plaza with paving, benches and a small tree.

    Do NOT add any text, letters, numbers or signs.

    3. The buildings on the WEST side (left edge of the image) must be 4 to 6 storey COMMERCIAL buildings (shops on the ground floor, offices above), not apartment blocks. The apartments stay only on the NORTH side (top).
