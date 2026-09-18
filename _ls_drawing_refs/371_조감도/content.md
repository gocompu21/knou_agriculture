'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 설계기본계획도와 A−A′ 단면도를 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다. 시점은 남서쪽 상공에서 북동쪽을 본 것입니다(도면의 북쪽이 위)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 서쪽 도로 — 북서 차량진입 · 남서 보도진입 | ✓ |
| 북서 주차장 — 관광버스 13대(서쪽 한 줄) · 승용차 20대(가운데 2열 + 자귀나무 화단), 아스팔트, 둘레 인도 2~3m + 경계식재 | ✓ |
| 진입광장(소형고압블럭) — 3인용 의자 · 음수대 · 휴지통, 소나무 요점식재 | ✓ |
| 휴게공간(사괴석포장) 가운데 상징조형물 1, 벤치 10 · 음수대 2 · 휴지통 10 | ✓ |
| 경외(+0.15) → 계단 → 경내(+1.80) → 계단 → 전통한옥(+2.35) 축선 | ✓ |
| 경내 전통담장, 한옥 앞 마사토 다짐, 둘레 잔디, 경관녹지(회화나무 · 리기다소나무) | ✓ |
| 북측 채석장 시선차단 — 잣나무 · 리기다소나무 차폐, 부지 외곽 은행 · 자귀나무 완충 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of the landscaped grounds around a Korean HISTORIC SITE (사적지). The FIRST attached image is the master plan (facilities + planting, hand-drawn Korean exam answer sheet, north is up); the SECOND is the A-A' section through it (west to east). Reproduce the plan's layout, shapes and positions faithfully; do not invent elements that are not in the plan.

    CAMERA: oblique aerial view from the SOUTH-WEST looking north-east, tilted about 45 degrees (true 3D perspective), high enough that the whole site (about 75 m east-west x 65 m north-south) plus the road on the west is visible. Late-spring daylight, soft shadows.

    The site rises from WEST to EAST in three levels: the outer grounds (경외) at street level on the west, then a grassy slope, then the walled inner precinct (경내) 1.8 m higher on the east, with a traditional building 2.35 m up.

    WEST: a public ROAD runs north-south along the west edge, with a vehicle entrance in the north-west and a pedestrian entrance in the south-west.

    OUTER GROUNDS (west two-thirds), from north to south / west to east:
    1. NORTH-WEST: a large asphalt PARKING LOT — along its west side a row of 13 long 90-degree stalls for TOUR BUSES (12 x 3.5 m each), and in its middle two double rows of car stalls (20 cars, 5.5 x 2.5 m) separated by a long narrow planted median with 7 silk trees; the lot is edged by a 2–3 m sidewalk and a 2–3 m hedge/tree border (Korean pines along the north and west, forsythia and azalea hedges). Buses and cars parked.
    2. SOUTH-WEST: the pedestrian entrance leads into a small ENTRANCE PLAZA paved with small grey interlocking blocks; along its edges backed benches, a drinking fountain and trash bins.
    3. From the entrance plaza a wide pedestrian axis runs east into a square REST PLAZA (about 18 x 18 m) paved with dark granite setts (사괴석), with ONE tall abstract SYMBOLIC SCULPTURE on a hexagonal plinth at its exact centre; around the plaza 3-person benches (10 in total across the grounds), a second drinking fountain and trash bins; zelkovas and ginkgos for shade.
    4. EAST of the rest plaza the axis continues as a granite-block walk and climbs the grassy slope by a wide flight of STONE STEPS (15 cm risers) to the inner precinct gate; the slope is planted with lawn, azalea masses and a few maples. A screen of Korean pines and pitch pines along the NORTH edge blocks the view of a quarry to the north.

    INNER PRECINCT (east, 1.8 m above): enclosed by a low TRADITIONAL KOREAN WALL (grey stone base, plastered face, grey tiled coping). Inside, on the north half, a traditional single-storey wooden HANOK with a grey tiled hip-and-gable roof standing on a stone platform (2.35 m), with a forecourt of compacted sandy earth (마사토) in front of it and lawn around; a second flight of steps leads up from the walk to this platform. The southern part of the precinct is a scenic lawn/garden with pines, pagoda trees, jujubes and quinces; along the north edge inside the wall, a group of pagoda trees and pitch pines.

    PLANTING accents: 3 red pines flanking the entrance plaza as focal trees; rows of ginkgo and silk trees along the south and east boundaries; lilac, spiraea and flowering shrubs at plaza corners; a boxwood hedge around the parking lot.

    STYLE: clean, realistic landscape-architecture visualization; asphalt, granite setts, interlocking blocks, sandy earth, lawn and tiled roofs clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
