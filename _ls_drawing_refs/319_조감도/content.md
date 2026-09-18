'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 기본설계도와 단면도를 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 동 30m 도로 · 남 이면도로, 남동 모따기, 북 · 서 · 남 오피스빌딩 | ✓ |
| 북서 지하주차장 차량진출입구 RAMP 17% | ✓ |
| 팔각 중앙광장 석재타일, 중심 환경조형물 1, 이동식 화분 4, 식수대 + 폭 30cm 연식의자 | ✓ |
| 북동 휴게공간 파고라 4×4 2, 벤치 | ✓ |
| 동측 진입광장 볼라드 5, 남동 관리공간 화장실 · 목재데크 | ✓ |
| 소형고압블럭 동선, 조명등 8 · 음수대 2 · 휴지통 3 | ✓ |
| 잣나무 차폐(북 · 서), 은행나무 완충(남 · 동), 벚나무 유도, 일본목련 · 느티 · 중국단풍 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of a small URBAN PARKING-DECK PARK (주차공원 — a park built on the roof slab of an underground parking garage) in a Korean city centre. The FIRST attached image is the master plan (facilities + planting, hand-drawn Korean exam answer sheet, north is up); the SECOND is the section. Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), high enough that the whole site (about 60 x 50 m) plus the roads is visible. Late-spring daylight, soft shadows.

    SURROUNDINGS: a wide 30 m road along the EAST edge, a narrower back street along the SOUTH edge; the SOUTH-EAST corner of the site is chamfered. Mid-rise OFFICE BUILDINGS stand beyond the north, west and south edges. The whole site is a flat concrete deck at street level.

    LAYOUT (from the plan):
    1. NORTH-WEST corner: the vehicle ENTRANCE/EXIT of the underground garage — a straight RAMP (17%) descending into the ground from the back street on the west, with a row of Korean pines screening it.
    2. CENTRE: an OCTAGONAL CENTRAL PLAZA (about 22 m across) paved with stone tiles in a radial pattern; at its exact centre a modern abstract ENVIRONMENTAL SCULPTURE on a low round plinth; around the sculpture 4 movable planters; along four of the octagon's edges long raised PLANTER BOXES (식수대, 70 cm high, planted with shrubs and small trees) with a continuous 30 cm wide timber bench seat along their edges.
    3. NORTH-EAST: a REST AREA paved with small interlocking blocks with TWO timber pergolas (4 x 4 m) and benches, sheltered by pines and cherries.
    4. EAST edge (toward the 30 m road): a small entrance plaza with 5 stone bollards and a pedestrian entrance; a strip of shade trees (Japanese magnolia, zelkova) and a tree-grate row along the road.
    5. SOUTH-EAST: a MANAGEMENT AREA with a small TOILET building (pitched roof) and a small timber-deck terrace beside it, entered from the chamfered corner.
    6. SOUTH-WEST corner: a triangular ENTRANCE PLAZA at the pedestrian entrance from the back street with forsythia beds.
    7. WEST: between the ramp and the plaza a planted green with a winding path, lilacs and Chinese maples.
    8. Paths of small grey interlocking blocks link the entrances (north, east, south-west) to the central plaza; 8 lamp posts, 2 drinking fountains, 3 trash bins along them.
    9. PLANTING: a line of Korean pines (20) around the north and west edges as a screen; ginkgos (13) along the south and east edges; cherries (10) along the path to the east entrance; zelkovas, Japanese magnolias and Chinese maples as accents; forsythia, lilac, kerria and azalea masses in the beds; juniper ground cover.

    STYLE: clean, realistic landscape-architecture visualization; stone tiles, interlocking blocks, timber deck, planter boxes with bench edges clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
