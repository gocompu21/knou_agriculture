'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 배식설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 사다리꼴 부지(북쪽 변이 비스듬), 남쪽 도로에서 북쪽으로 오르는 경사지 | ✓ |
| 남측 중앙 주동선 9m → 중앙광장(10.3, 수목보호대 4) | ✓ |
| 서쪽 운동공간 28×40 마사토, 코트 2면, 벤치 | ✓ |
| 동쪽 놀이공간 — 미끄럼틀 · 시소 · 정글짐 · 회전무대 · 철봉 · 그네 6종, 마사토 · 동측 부동선 4m | ✓ |
| 광장 → 계단(15×30) + RAMP → 전망 및 휴게공간(14.5, 주동선 축), 파고라 2 · 벤치 · 음수대 | ✓ |
| 북동 경사지를 도는 산책로 2m 콘크리트, 동쪽으로 나감 | ✓ |
| 남측 도로변 3m 상록 완충녹지(소나무 · 잣나무 · 독일가문비), 경사면 관목 군식, 벤치 20 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of a hillside NEIGHBOURHOOD PARK (근린공원) in central Korea. The FIRST attached image is the facilities plan, the SECOND the planting plan (hand-drawn Korean exam answer sheets, north is up). Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees (true 3D perspective), high enough that the whole site plus the road on the south is visible. Late-spring daylight, soft shadows.

    SITE: a trapezoid 80 m wide, 60 m tall on the west side and 105 m tall on the east side (the NORTH edge slopes up diagonally from the north-west corner to the higher north-east corner). The ground is flat along the SOUTH road (level 10) and rises steadily northward as a grassy wooded HILLSIDE (to level 18 at the north-east). A road with houses runs along the south edge.

    LAYOUT (from the plan):
    1. MAIN ENTRANCE: from the south road, a 9 m wide MAIN WALK (block paving) enters at the centre of the south edge and runs straight north to the CENTRAL PLAZA (level 10.3), a square granite-paved plaza about 15 m wide with 4 square tree grates and shade trees.
    2. WEST of the main walk: the SPORTS AREA (28 x 40 m, sandy decomposed-granite surface, level 10.2) containing TWO TENNIS / BADMINTON COURTS side by side with low fences, benches around.
    3. EAST of the main walk (south-east part): the CHILDREN'S PLAYGROUND (sandy surface) with six play items — a slide, a 3-seat seesaw, a jungle gym, a merry-go-round, a 4-bar horizontal bar and a 2-seat swing — plus benches; a 4 m SECONDARY WALK enters from the EAST road edge at the south-east and joins the plaza.
    4. NORTH of the plaza: the ground rises; a wide flight of STONE STEPS (15 cm risers) with a switch-back RAMP (10%) beside it climbs to the VIEWPOINT REST AREA (전망 및 휴게공간, level 14.5) — a small granite-paved terrace directly on the main axis, with TWO timber pergolas (3 x 5 m), several benches and a drinking fountain, looking south over the park; the cut slopes around it are 1:1 grassy banks with shrubs.
    5. NORTH-EAST: from the terrace a 2 m free-curving WALKING TRAIL (concrete) loops through the wooded hillside and comes out at the east edge (upper right), following the contours.
    6. Along the SOUTH road edge: a 3 m+ buffer belt of evergreen trees (red pines, Korean pines, Norway spruces) screening the park from the road, with hedges. Ginkgos, zelkovas and planes as shade trees around the plaza and courts; dogwood, fringe trees, red maples and mountain ash on the slopes; azalea and rhododendron masses on all cut slopes; boxwood hedges along walks. The hillside beyond is natural woodland.
    7. 20 benches in total spread over the plaza, courts, playground and terrace. Drainage gratings at the courts and playground.

    STYLE: clean, realistic landscape-architecture visualization; block paving, granite, sandy courts, lawn slopes and steps clearly distinguishable. Do NOT write any text, letters, numbers, labels or signs.
