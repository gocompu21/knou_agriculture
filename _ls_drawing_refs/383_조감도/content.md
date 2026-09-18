'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 식재설계평면도(횡단면 포함) 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다. 12층 업무용 빌딩의 5층 저층부 옥상이라, 북쪽 휴게실과 서쪽 식당 벽면이 서고 남동쪽 아래로 도로가 보입니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 30×22.5 슬래브, 동쪽 · 남서 모서리 모따기, 콘크리트 옹벽 H1.5, 북쪽 휴게실 · 서쪽 식당 출입문 | ✓ |
| 집합 및 휴게공간(북서) — 목재데크 30~60cm 높임, 가운데 환경조각물 1, 긴 벤치 | ✓ |
| 간이휴게공간(북 · 잔디, 긴 벤치) | ✓ |
| 수경공간 2 — 북동 모따기 안 분수, 남쪽 큰 연못 분수(분수 5) | ✓ |
| 휴식공간(동) — 파고라 4×4 1, 긴 벤치(합계 5) | ✓ |
| 조명등 15 · 휴지통 3, 급수관 · 전기배선 | ✓ |
| 둘레 식재대 마운딩 — 향나무 · 주목 · 단풍 · 목련, 회양목 · 눈향 · 무궁화 · 철쭉, 비비추 · 원추리, 꽃창포 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of a ROOF GARDEN (옥상정원) on the 5th-floor podium roof of a 12-storey office building in central Korea. The FIRST attached image is the facilities plan, the SECOND the planting plan with a cross-section (hand-drawn Korean exam answer sheets, north is up). Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), from about 40 m above the roof so the whole garden (30 x 22.5 m) fills the frame, with the tall office tower rising behind it on the north/west and the city street far below on the south-east. Late-spring daylight, soft shadows.

    THE ROOF: an octagon-like slab — a 30 m (east-west) x 22.5 m (north-south) rectangle whose EAST (north-east and south-east) and SOUTH-WEST corners are cut diagonally. It is enclosed by a 1.5 m concrete parapet wall. The tower's glass-and-stone walls rise along the NORTH side (a staff lounge with a door, "ENT") and the WEST side (a cafeteria with a door, "ENT"); the garden floor is 60 cm below those doorsills.

    LAYOUT (from the plan):
    1. NORTH-WEST: the GATHERING & REST AREA (집합 및 휴게공간), a rectangular TIMBER DECK raised 30–60 cm above the garden floor (up a few steps), with an abstract ENVIRONMENTAL SCULPTURE at its centre and long timber benches along its north edge; it is reached from the lounge door.
    2. NORTH-CENTRE: a small INFORMAL REST AREA (간이휴게공간) of lawn with two long benches and stepping stones, just east of the deck.
    3. NORTH-EAST (inside the north-east chamfer): a triangular WATER FEATURE (수경공간) with fountain jets and water plants, 20 cm below the floor.
    4. EAST-CENTRE: the RELAXATION AREA (휴식공간): a timber PERGOLA (4 x 4 m) with long benches, on a timber-deck floor.
    5. SOUTH-CENTRE: a large timber-deck terrace stepping down toward the south; below it (south) a second, larger WATER FEATURE — a curved pond with rocks, fountain jets, irises and water plants, hugging the south parapet.
    6. SOUTH-WEST: the cafeteria door opens onto a timber walkway that runs east along the south side of the deck; a planted mound with trees along the south-west chamfer.
    7. WEST and NORTH edges and all corners: raised PLANTING BEDS (mounded soil for trees) with juniper, yews, Japanese maples, magnolias, boxwood and creeping juniper, rose-of-sharon and azalea masses, hostas and daylilies; the whole perimeter inside the parapet is planted.
    8. 15 small garden lamp posts along the decks and paths; 3 trash bins; a supply pipe feeds the fountains. Timber deck, lawn, water and gravel/stone paving should be clearly distinguishable.

    STYLE: clean, realistic landscape-architecture visualization of a rooftop; show the parapet, the tower walls with windows, and the city below. Do NOT write any text, letters, numbers, labels or signs.
