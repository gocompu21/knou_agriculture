'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 기본설계도와 A−A′ 단면도 · 벽천 스케치를 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 서 · 남 도로와 3m 보도, 남서 45° 모따기, 북 · 동 APT단지 | ✓ |
| 팔각 중심광장(석재타일 · 자연석판석), 가운데 원형 간이무대(+1.2) | ✓ |
| 북동 놀이공간 100m² 이상 — 시소 · 그네 · 미끄럼대 · 래더 · 정글짐 5종, 고무매트 | ✓ |
| 남서 침상광장 100m² 이상(−2.0), 계단 + RAMP 8.3%, 벽천 · 연못 | ✓ |
| 파고라 4 | ✓ |
| 지하주차장 차량입구 서북측 RAMP 17% · 출구 남동쪽 RAMP 17% | ✓ |
| 환기구 4m² 이상 4개, 녹지 내 균등 배치 | ✓ |
| 화장실 20m² 이상, 서쪽 도로변, 차폐 | ✓ |
| 서 · 남 주출입구, 북 · 동 부출입구(APT 연결), 포장 3종 | ✓ |
| 잣나무 · 독일가문비 차폐(북 · 동), 소나무 요점, 은행 가로변, 낙엽교목 7종 · 상록교목 4종 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of a CHILDREN'S PARK built on top of an UNDERGROUND PUBLIC PARKING GARAGE (어린이공원·주차공원) at a street corner in a Korean city. The FIRST attached image is the master plan (facilities + planting, hand-drawn Korean exam answer sheet, north is up); the SECOND is the section and a sketch. Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-WEST looking north-east, tilted about 45 degrees (true 3D perspective), from about 60 m height so the whole site (about 45 x 45 m) plus the two streets is visible. Late-spring daylight, soft shadows.

    SURROUNDINGS: arterial ROADS along the WEST and SOUTH edges with a 3 m sidewalk and pedestrian crossings; the SOUTH-WEST corner is chamfered at 45°. APARTMENT blocks beyond the NORTH and EAST edges. The site is flat (the roof slab of the garage).

    LAYOUT (from the plan):
    1. CENTRE: an OCTAGONAL CENTRAL PLAZA paved with natural flagstone and stone tiles, and at its exact centre a round raised OPEN-AIR STAGE (간이무대, about 8 m across, 1.2 m high, stone-faced, with steps up) ringed by a band of paving; the plaza itself is raised 60 cm above the paths with low steps.
    2. NORTH-EAST corner: the CHILDREN'S PLAYGROUND (about 12 x 10 m, rubber-mat surface) with five play items — a 3-seat seesaw, a 2-seat swing, a slide, a ladder/climbing frame and a jungle gym — enclosed by a low hedge.
    3. NORTH: a REST AREA with a large timber PERGOLA (3 x 3 m) and benches, between the playground and the plaza; a small pedestrian entrance from the apartments on the north edge.
    4. NORTH-WEST: the vehicle ENTRANCE to the underground garage — a straight RAMP (17%) descending from the west road, with a Korean-pine screen; south of the ramp a small TOILET building (pitched roof) beside the west main entrance, screened by shrubs.
    5. WEST: the MAIN ENTRANCE from the west road, a wide block-paved walk leading east to the plaza; a second timber pergola near it.
    6. SOUTH-WEST corner: a SUNKEN PLAZA (침상광장, about 12 x 10 m, 2 m below grade, stone-tile floor) reached by a flight of steps and a long RAMP (8.3%); against its inner (north-east) wall a WATERFALL WALL with a small POND in front, and benches; planted terrace around the top edge.
    7. SOUTH: a second pedestrian entrance from the south sidewalk; a third pergola on the plaza's south side; SOUTH-EAST corner: the vehicle EXIT of the garage — a second RAMP (17%) rising to the south road; a fourth pergola near the east side.
    8. Four small square VENTILATION SHAFTS for the garage placed in the green areas, evenly spread.
    9. PLANTING: a 1.5 m green strip with ginkgo street trees along the west and south roads; dense screen of Korean pines and Norway spruces along the north and east edges toward the apartments; red pines as accents at the entrances; zelkovas and planes around the plaza; cherries, maples, magnolias and dogwoods in the greens; forsythia, spiraea, azalea masses and spindle-tree hedges around the playground and toilet. Paving: stone tile, natural flagstone and clay brick in different areas.

    STYLE: clean, realistic landscape-architecture visualization; the ramps, sunken plaza with waterfall and the raised stage clearly readable. Do NOT write any text, letters, numbers, labels or signs.
