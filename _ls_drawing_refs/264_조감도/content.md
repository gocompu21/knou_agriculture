'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물설계도(스케치 포함) · 식재설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 적벽돌 연구소 5동(4층 1 · 3층 4)이 가운데를 비우고 둘러섬, FL+600 계단 · 화강석 바닥 | ✓ |
| 모임광장 30×30 — 원형 연못 + 중앙 조형물, 대형조명등 4, 쉘터 4, 평의자 16, 정원등 16 | ✓ |
| 남쪽 주진입(볼라드 5) · 동쪽 차량진입(주차장 옆) · 북동 부진입 | ✓ |
| 휴게공간(서, 기존녹지 옆) — 파고라 3×6 2, 3인용 평의자, 수목보호대 4 | ✓ |
| 서쪽 기존녹지 · 목재펜스, 동쪽 주차장, 남동 운동장 | ✓ |
| 광장 둘레 구상 · 향나무 정형 식재, 건물 접한 녹지 자연형(느티 · 층층 · 이팝 · 목련 · 복자기), 사철 · 수수꽃다리 · 진달래 · 매자 · 모란 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of the CENTRAL PLAZA OF A RESEARCH-INSTITUTE CAMPUS (연구소 건물군 중앙광장) in central Korea. The FIRST attached image is the facilities plan with a sketch (hand-drawn Korean exam answer sheet, north is up); the SECOND is the planting plan. Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), high enough that the whole campus (about 110 x 90 m) is visible. Late-spring daylight, soft shadows.

    BUILDINGS: FIVE research buildings with RED BRICK facades and flat roofs stand around a central open space: a long 4-storey building along the NORTH, a 3-storey building to its WEST (north-west), a 3-storey building along the EAST (with the campus PARKING LOT — asphalt, cars — beyond it to the east), and TWO 3-storey buildings side by side along the SOUTH with the MAIN ENTRANCE walk passing between them from the south. Every building floor is 60 cm above the plaza, with granite entrance landings and short steps. Existing dense WOODLAND lies along the WEST edge behind a timber fence; a sports FIELD lies to the south-east.

    LAYOUT (from the plan):
    1. CENTRAL GATHERING PLAZA (모임광장), 30 x 30 m, in the middle of the courtyard: a square of granite-slab paving with a CIRCULAR centre — a round shallow POND (about 8 m across, stone-edged) with a tall abstract SCULPTURE rising from its middle, ringed by a circular walk; 4 tall LAMP POSTS (4.5 m) at the pond's four sides; 4 fan-shaped SHELTERS (부채꼴 쉘터) on the diagonals; 16 flat benches around; the plaza's four corners are planted squares with clipped shrubs, and 16 small garden lamps.
    2. Paved walks (interlocking blocks) run from the plaza to each building entrance (north, west, east, south) with steps up to the building landings.
    3. MAIN ENTRANCE from the SOUTH: a wide walk between the two south buildings, with 5 stone BOLLARDS across it (no vehicles); a VEHICLE entrance from the east near the parking lot; a pedestrian entrance from the north-east.
    4. REST AREA (휴게공간) on the WEST side beside the woodland: a small granite-paved area with TWO long timber PERGOLAS (3 x 6 m), a few 3-seat benches, 4 square tree grates with shade trees, and a drinking fountain, reached by short steps.
    5. PLANTING: formal rows of Korean firs and junipers around the gathering plaza; zelkovas, planes and ginkgos as shade trees at the rest area and entrances; naturalistic groups of dogwoods, fringe trees, magnolias, maples and paperbark maples in the lawns along the buildings; euonymus hedges, lilac, azalea, barberry and tree-peony masses; lawn everywhere else.

    STYLE: clean, realistic landscape-architecture visualization; red-brick buildings, granite plaza, pond and lawns clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
