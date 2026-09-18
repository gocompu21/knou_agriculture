'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물 배치평면도 · 식재기본설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 남쪽 보도(+10.00) · 차도, 부지 +10.90, 보도 쪽 1:1.5 정지, 북 · 서 경관 불량 → 상록 차폐 | ✓ |
| 건물(f+11.35) 북측 ㄱ자, 드라이에어리어, 진입 계단(15×30) | ✓ |
| 건물 전면 광장(화강석) + 환경조각물 H3 · W2 1 | ✓ |
| '가' 지하층 진입 램프 5m · 10% (서쪽) | ✓ |
| '나' 건물 진입 보행로 3m · 계단(가운데), 콘크리트 보도블럭 | ✓ |
| '다' 주차진입로 6m · 램프 10%, 사선 주차 9대 아스팔트, 주변 대형 녹음수(느티 H4 · W3) | ✓ |
| 동쪽 정구장 1면 남북(우레탄), 그 남쪽 휴게공간 — 파고라 1 · 의자 6 · 음료수대 1 · 휴지통 2, 자연석 판석 | ✓ |
| 잣나무 차폐(북 · 서 H3 이상), 진입부 좌우 소나무 대형수, 은행 · 느티, 목련 · 벚 · 단풍, 회양목 · 조릿대 · 조팝 · 병꽃 · 철쭉 · 개나리 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of the LANDSCAPED GROUNDS OF AN OFFICE BUILDING (사무실 건축물 조경) in a small city in central Korea. The FIRST attached image is the facilities plan, the SECOND the planting plan (hand-drawn Korean exam answer sheets, north is up). Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), high enough that the whole lot (about 70 x 45 m) plus the street in front is visible. Late-spring daylight, soft shadows.

    SITE: a rectangular lot with a public SIDEWALK and ROAD along its SOUTH edge (street level 10.00); the lot is 90 cm higher (10.90) with a grassy 1:1.5 slope down to the sidewalk. A basement extends under the building and the forecourt. The NORTH and WEST neighbours have poor views, so those two edges get a dense evergreen screen.

    LAYOUT (from the plan):
    1. The BUILDING: a large modern 4-storey office block (light stone facade, flat roof) occupying the north-centre of the lot, L-shaped in plan (a long east-west wing along the north with a shorter wing coming south at its east end). Its ground floor is at 11.35, 45 cm above the forecourt, reached by short flights of steps at the entrances; narrow dry-area light wells (DA) run along its north side and west end.
    2. FORECOURT PLAZA (광장) in the SOUTH-WEST in front of the building: paved with granite in a formal pattern, with ONE tall modern ENVIRONMENTAL SCULPTURE (3 m high, 2 m wide) as the focal point; a strip of formal lawn and shrubs along its south edge above the slope. From the sidewalk at the centre-south ("나") a 3 m pedestrian walk of concrete pavers climbs by STEPS (15 cm risers) up to the plaza.
    3. WEST ("가"): a 5 m wide RAMP at 10% descending from the sidewalk to the basement along the west side of the plaza, with a stair beside it.
    4. SOUTH-EAST ("다"): a 6 m wide asphalt DRIVE ramping up at 10% from the road into a small asphalt PARKING LOT of about 9 angled (45°) stalls in one row along the south-east, shaded by large zelkovas (4 m tall, 3 m crowns); cars parked.
    5. EAST: a single TENNIS COURT (long axis north-south, green synthetic surface, low fence) in the north-east of the lot, and south of it a small REST AREA paved with natural flagstones with ONE timber pergola (4.5 x 4.5 m), 6 benches, a drinking fountain and 2 trash bins, bordered by shrubs.
    6. Concrete-paver walks connect the plaza, the building entrances, the rest area and the parking.
    7. PLANTING: a dense screen of Korean pines (3.5 m+) along the whole NORTH and WEST boundaries; two large red pines flanking the main entrance as symbol trees; ginkgos and zelkovas as shade trees around the parking and tennis court; magnolias, cherries and maples near the plaza and rest area; boxwood hedges, sasa bamboo, spiraea, weigela, azalea and forsythia masses in the beds; lawn on the south slope. Planting over the basement is in raised soil beds.

    STYLE: clean, realistic landscape-architecture visualization; granite plaza, concrete pavers, asphalt, flagstones, lawn and the tennis court clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
