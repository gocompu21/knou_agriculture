'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 배식설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 45° 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 북(33.0)에서 남(30.0)으로 내려가는 경사, 가운데 주택(남향 현관 · 남쪽 베란다), 북동 참나무 보호수목 | ✓ |
| 남서 대문(차량 · 보행) 안쪽 소형주차장(투수콘) + 차폐식재 | ✓ |
| 전정 — 대문 → 현관 점토벽돌 주진입로, 잔디, 정원등 | ✓ |
| 주정(남동) — 야외조각 1, 경관석 3석조 1, 남측 마운딩 1m에 소나무 6 · 산철쭉 | ✓ |
| 측정(동) — 자연석판석 산책로, 맥문동 · 비비추, 느티 · 감나무 · 청단풍 | ✓ |
| 북동 침목계단 5m + 좌우 자연석 쌓기 | ✓ |
| 후정(북) — 자연형 연못 20m² 이상(꽃창포 · 옥잠화 · 붓꽃), 육각 파고라 + 등의자, 왕벚 · 수수꽃다리 | ✓ |
| 작업정(북서) 투수콘, 서측 서양측백 14주 차폐 | ✓ |
| 둘레 순환 산책로, 정원등 5 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of a Korean detached-house GARDEN (주택정원). The FIRST attached image is the facilities plan, the SECOND the planting plan of the same garden (hand-drawn Korean exam answer sheets, north is up). Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), from about 35 m height so the whole lot (about 24 x 24 m) fills the frame with a small margin. Late-spring daylight, soft shadows.

    THE LOT slopes gently DOWN from north (33.0 m) to south (30.0 m). A single-storey modern Korean HOUSE (light-grey walls, dark hip roof) stands in the middle, slightly west of centre; its front entrance faces SOUTH (a few steps up to the door) and a veranda projects on the south side. A large protected OAK tree (6 m tall, wide crown) stands at the NORTH-EAST corner of the lot. The lot is enclosed by a low wall; the GATE is at the SOUTH-WEST corner (a vehicle gate and a pedestrian gate side by side on the south wall).

    SPACES (from the plan):
    1. SOUTH-WEST corner, inside the gate: a small single-car PARKING SPACE paved with permeable concrete, screened by dense evergreen shrubs (spindle tree hedge).
    2. FRONT GARDEN (전정) south of the house: the MAIN PATH from the pedestrian gate to the front door is paved with red-brown CLAY BRICKS; the rest is lawn with low azalea beds along the path and 2 garden lamps.
    3. MAIN GARDEN (주정) SOUTH-EAST of the house: an open lawn with ONE modern outdoor SCULPTURE on a low plinth as the focal point, ONE group of three natural landscape stones, and along the south edge a gently MOUNDED bank (1 m high) planted with 6 red pines (소나무) and masses of azalea — the mound curves along the whole south side.
    4. SIDE GARDEN (측정) EAST of the house: a winding stepping-stone/flagstone path of natural stone slabs runs from the front garden north along the east side of the house, with lily-turf and hosta ground cover and a few deciduous trees (zelkova, persimmon, maple).
    5. At the NORTH-EAST, beside the big oak: a curving flight of RAILWAY-SLEEPER STEPS (about 5 m long, 15 cm risers) climbing the slope, flanked on both sides by dry-stacked natural stone walls.
    6. BACK GARDEN (후정) NORTH of the house: a natural-shaped POND (about 20 m², irregular outline edged with rocks, irises, hostas and marsh plants) in the low, poorly drained corner, and next to it a HEXAGONAL timber PERGOLA (3.3 m across) with a backed bench, under the oak's shade — a quiet rest area. Cherry trees and lilacs around.
    7. WORK YARD (작업정) NORTH-WEST corner, behind the kitchen: a small utility area paved with permeable concrete, visually screened from the gardens by shrubs.
    8. Along the whole WEST boundary (the side with a poor view): a dense screen of 14 columnar arborvitae (서양측백) in a row.
    9. A continuous flagstone walking path loops around the house connecting all spaces; 5 small garden lamps in total.

    STYLE: clean, realistic landscape-architecture visualization; clay-brick path, flagstones, permeable concrete, lawn, pond water clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
