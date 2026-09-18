'성운' 탭의 **답안지 II · 시설물배치도**와 문제지 조건을 AI 이미지 모델에 주고 만든 **입체 조감도**입니다(2026년 9월 18일).
위 첫 장이 **GPT**(gpt-image-2.5-sunburst), 둘째 장이 **제미나이**(gemini-3-pro-image-preview) — GPT 는 4회차(남동 휴게공간을 두 번 더 부분 수정), 제미나이는 2회차입니다.

## 만든 방법

1. 시설물배치도에서 표제란을 잘라낸 그림을 **참고 그림**으로 주고, 아래 **1회차 프롬프트**로 그렸습니다
2. 나온 그림을 도면과 대조했더니 두 모델 모두 **남동 모서리를 둥글게** 그리고 **지하철 출입구를 부지 안 광장에** 넣었습니다(도면은 45° 모따기 · 출입구는 모서리 바깥 보도). 제미나이는 서측 상업지를 아파트로 그렸습니다
3. 1회차 그림을 참고 그림으로 다시 주고 **2회차(수정) 프롬프트**로 그 부분만 고치게 했습니다 — 나머지는 그대로 두라고 못박았습니다
4. GPT 2회차의 **남동 휴게공간**이 도면과 달랐습니다(사용자 지적) — 장애인 주차 북쪽에 화단, 벤치가 흩어져 있고, 광장 동쪽에 없는 화단, 서측 가장자리에 볼라드 대신 나무. 그 자리만 **마스크**로 지정해 다시 그리게 하고(3회차), 나온 그림에서 마스크 안쪽만 잘라 원본에 얹었습니다 — 마스크 밖도 조금씩 흔들리기 때문입니다
5. 3회차는 장애인 주차가 10칸(한 칸은 기호가 겹쳐 깨짐)·윗줄 벤치 5개였습니다. 그 줄만 더 좁은 마스크로 **개수만** 고치게 했습니다(4회차)
6. 4회차의 장애인 주차칸 줄이 오른쪽으로 0.76° 기울어 아래 녹지대와 어긋났습니다(사용자 지적). 파란 칸의 윗변·아랫변을 재서 기울기를 구하고 그 덩어리만 반대로 돌려 바로 세웠습니다(0.05°) — 모델을 다시 부르지 않았습니다
7. 장애인 주차칸이 옆 주차열과 **일렬이 아니었습니다**(사용자 지적 — 도면은 3번째 주차열 위쪽 칸과 같은 줄). 칸 덩어리를 옆 칸과 같은 앞선(y 510)·같은 깊이로 옮기고, 녹지대와 서쪽 끝 화단도 함께 올렸습니다. 그렇게 해서 광장 쪽에 생긴 틈만 마스크로 관목·잔디를 채우게 했습니다(아래 5회차 프롬프트)

## 도면과 대조

| 도면(성운 답안) | GPT | 제미나이 |
| --- | --- | --- |
| 주차열 4줄(위 2줄 길고 아래 2줄 짧음), 열 가운데 녹음수 | ✓ | ✓ |
| 북서 휴게광장 — 퍼걸러 · 격자 수목보호대 | ✓ | ✓ |
| 북측 화장실 · 주차관리소(북동 · 남서) | ✓ | ✓ |
| 남동 휴게광장 — 장애인 주차 8칸(북쪽으로 열림) · 그 남쪽 녹지대 · 벤치 한 줄 6개와 휴지통 · 음수대 | ✓ (4회차에 고침) | 화단 · 벤치 배치가 다름 |
| 남동 휴게광장 — 직각삼각형 화단 · 위 3 · 왼쪽 3 벤치 · 서측 볼라드 · 모서리 체크무늬 포장 | ✓ (3회차에 고침) | 화단이 네모로 바뀜 |
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

## 3회차(남동 휴게공간 부분 수정) 프롬프트 — GPT · 마스크 사용

    Edit ONLY the transparent (masked) area of this aerial rendering: the south-east rest plaza of the parking park, including the row of accessible parking stalls at its top. Everything outside the mask (asphalt aisle, other parking rows, the diagonal site edge, the sidewalk, the glass subway entrance, roads, crosswalks) must stay exactly as it is. North is up, east is right. Match the lighting, scale and rendering style of the rest of the image.

    Redraw the masked area to match the landscape design drawing exactly, from top (north) to bottom (south):

    1. ACCESSIBLE PARKING: one straight row of 8 blue accessible parking stalls with white wheelchair symbols, side by side, the stalls OPEN TO THE NORTH onto the asphalt driving aisle above them (cars would drive in from the top). No planting on the north side of the stalls. At the WEST (left) end of the row: a small rounded planting island with low shrubs and one lilac tree.
    2. Directly SOUTH of the 8 stalls (below them): one narrow continuous planting strip about 3 m wide running the full length of the stall row, with a single line of 6 medium deciduous trees evenly spaced and low clipped shrubs under them, and 3 small square garden lamps along it.
    3. REST PLAZA below that strip, paved with light-grey granite slabs in a square grid:
       - Along the TOP edge of the plaza, right under the planting strip: a straight line of 6 wooden benches (3 on the left, 3 on the right) with a round trash bin and a round drinking fountain side by side in the middle of the line.
       - In the middle-left of the plaza: ONE raised flower bed shaped as a RIGHT TRIANGLE — its left side is a straight vertical edge, its top side is a straight horizontal edge, and its long side runs diagonally from the top-right corner down to the bottom-left corner (parallel to the site's diagonal edge). Inside it: 3 round dark-green evergreen shrubs (junipers) and low flowering shrubs. A row of 3 wooden benches just ABOVE the triangle's top edge, and a column of 3 wooden benches along the triangle's LEFT edge.
       - Along the plaza's LEFT (west) edge, where it meets the asphalt aisle: a straight line of 5 short stone bollards. NO trees along this edge.
       - The plaza's top-right corner (next to the diagonal edge) and its bottom-left corner: a checkered pattern of grey and reddish concrete paving blocks. NO planting beds there; the only planting in the whole plaza is the triangle bed and the strip under the parking stalls.
       - A pedestrian opening in the diagonal site edge, leading out to the subway entrance on the sidewalk.

    No other flower beds, no other benches, no extra trees in the plaza. Do NOT add any text, letters, numbers or signs.

## 4회차(개수만 수정) 프롬프트 — GPT · 더 좁은 마스크

    Edit ONLY the transparent (masked) strip of this aerial rendering. Keep everything outside it exactly the same, and keep the same layout inside it — only fix the COUNTS. North is up.

    From top to bottom the strip contains:
    1. A row of EXACTLY 8 (eight) blue accessible parking stalls, all the same width, filling the same length as now, divided by 7 white lines. Each stall has exactly ONE clean white wheelchair symbol, centred. No merged, doubled or broken symbols. Count them: 1, 2, 3, 4, 5, 6, 7, 8.
    2. Below the stalls, the same narrow planting strip with the same 6 round deciduous trees, low shrubs, and EXACTLY 3 small square garden lamps (one at the left third, one in the middle, one at the right third).
    3. Below the strip, on the granite paving, one straight line of: 3 wooden benches on the left, then a round trash bin and a round drinking fountain side by side in the middle, then 3 wooden benches on the right. EXACTLY 6 benches in total, evenly spaced.

    Same lighting and style as the rest of the image. No text, letters or numbers.

## 5회차(틈 메우기) 프롬프트 — GPT · 마스크

    Edit ONLY the transparent (masked) horizontal band of this aerial rendering. Everything outside it must stay exactly the same — the blue accessible parking stalls and the planting strip with round trees ABOVE the band, and the granite plaza with the line of benches BELOW it.

    Fill the band as the lower half of that planting strip: grass and dense low clipped evergreen shrubs, continuing seamlessly from the shrubs and tree canopies above. There must be ONE single light-grey concrete curb, only along the very BOTTOM edge of the band, where the planting meets the plaza paving. NO curb, path, paving or line anywhere else inside the band — it is one continuous planted bed.

    Do NOT add trees, lamps, benches, bollards, cars, parking stalls or wheelchair symbols. Top-down aerial view, same lighting and style. No text, letters or numbers.
