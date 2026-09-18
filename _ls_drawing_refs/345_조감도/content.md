'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 도시 미관광장의 시설물배치도 · 수목배치도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다. 문제 1의 공원묘지 토지이용계획(개념도)은 조감도로 만들지 않았습니다 — 1/12,000 지형도 위의 구역 구분이라 그림으로 옮길 시설이 없습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안, 도시 미관광장) | 결과 |
| --- | --- |
| 상 · 하 4차선 도로, 좌 · 우 업무용 빌딩 | ✓ |
| 부지 중앙 동서 4m 동선 녹색 투수콘, 중앙 Ø4 원형 지반(마름돌 벽 40cm) + 시계탑 | ✓ |
| 출입구 제외 둘레 식재함 폭 4m · 높이 80cm 소성벽돌 | ✓ |
| 수경공간 −60cm, 계단 · 램프 — 반경 10m 원호 + 직선 연못, 벽천 3m, 분수, 펌프실 2 | ✓ |
| 파고라 3.6×3.6 4 · 장의자 6m 2 · 집수구 | ✓ |
| 조각전시공간 +40cm — 원호 잔디, 조각 받침, ㄱ형 파고라 2 · 장의자 4m 2, 수목보호대 | ✓ |
| 화장실 6×4 · 관리소 겸 매점 5×4, 소형고압블록(ILP) | ✓ |
| 상록수 위주(소나무 · 잣나무 · 후박 · 태산목 · 감탕 · 해송), 능수버들 · 단풍, 피라칸사 · 영산홍 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of an URBAN ORNAMENTAL PLAZA (도시 미관광장) in a southern Korean city. The FIRST attached image is the facilities plan, the SECOND the planting plan (hand-drawn Korean exam answer sheets). Treat the drawing's TOP as "up" and describe positions as in the drawing (in reality the drawing's right side is north). Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the drawing's LOWER-RIGHT corner looking toward the upper-left, tilted about 45 degrees (true 3D perspective), high enough that the whole rectangular site (about 55 x 32 m) and the roads at its top and bottom edges are visible. Late-spring daylight, soft shadows.

    SURROUNDINGS: four-lane ROADS run along the TOP and BOTTOM edges of the site; tall OFFICE BUILDINGS stand beyond the LEFT and RIGHT edges. The site is flat.

    LAYOUT (from the plan):
    1. A 4 m wide CENTRAL WALK of green permeable concrete runs top-to-bottom through the exact middle, from the main entrance on the top road to the main entrance on the bottom road. At its centre a round raised planting bed 4 m across with a 40 cm dressed-stone wall, and in the middle of that a stone dais carrying a slender modern CLOCK TOWER / symbol tower about 6 m tall.
    2. Around the whole perimeter (except the two entrances) a continuous RAISED PLANTER BOX 4 m wide and 80 cm high, faced in red clinker brick, filled with evergreen trees and shrubs.
    3. RIGHT half (the drawing's right = the water garden, 수경공간), SUNKEN 60 cm below the walk, reached from the central walk by a curved flight of STEPS and a RAMP: a geometric POND along the far right end — its inner edge is a semicircular arc (radius 10 m centred on the middle of the right edge) joined to straight sections at least 3 m wide, with a raised 40 cm stone coping; at the pond's right end a 3 m high vertical WATERFALL WALL built against the planter, with a FOUNTAIN jet in the pond; two small pump rooms hidden in the planter. The sunken floor is paved with small grey interlocking blocks; TWO square timber pergolas (3.6 x 3.6 m) at the right half's top-left and bottom-left corners, plus two long 6 m benches, 2 square tree grates and drain grates.
    4. LEFT half (the sculpture garden, 조각전시공간), RAISED 40 cm above the walk: paved with interlocking blocks; a matching semicircular arc of lawn at the far left end; 6 hexagonal stone SCULPTURE PLINTHS with abstract sculptures arranged along the arc; two L-shaped timber pergolas (9 x 3 m) at the left half's top-right and bottom-right corners, two 4 m benches, 8 square tree grates with shade trees.
    5. Beside the central walk near the top entrance a small TOILET building (6 x 4 m) on the left and a small MANAGEMENT / KIOSK building (5 x 4 m) on the right; near the bottom entrance a second pair of small buildings.
    6. PLANTING: evergreens dominate — red pines, Korean pines, machilus, southern magnolia, holly and black pines in the perimeter planters; weeping willows and maples near the pond; pyracantha and azalea hedges; ajuga and lily-turf ground cover.

    STYLE: clean, realistic landscape-architecture visualization; green concrete walk, interlocking blocks, brick planters, water and lawn clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
